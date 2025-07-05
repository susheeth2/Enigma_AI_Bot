"""
Enhanced API routes with MCP integration, document chat, RAG, and web search
"""
import uuid
from flask import Blueprint, request, jsonify, session, Response
from services.enhanced_chat_service import EnhancedChatService
from services.file_service import FileService
from services.mcp_service import MCPService
from utils.database import DatabaseManager
import json
import time

enhanced_api_bp = Blueprint('enhanced_api', __name__)
enhanced_chat_service = EnhancedChatService()
file_service = FileService()
mcp_service = MCPService()
db_manager = DatabaseManager()

@enhanced_api_bp.route('/enhanced/send_message', methods=['POST'])
def enhanced_send_message():
    """Enhanced message sending with mode-specific routing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        stream = data.get('stream', False)
        mode = data.get('mode', 'chat')
        max_tokens = data.get('max_tokens', 50000)

        if stream:
            return Response(
                enhanced_stream_chat_response(
                    user_message, 
                    session['user_id'], 
                    session['session_id'],
                    mode,
                    max_tokens
                ),
                mimetype='text/stream'
            )
        else:
            result = enhanced_chat_service.process_message_with_mode(
                user_message, 
                session['user_id'], 
                session['session_id'],
                mode,
                max_tokens
            )
            return jsonify(result)

    except Exception as e:
        print(f"[enhanced_send_message] Error: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

def enhanced_stream_chat_response(user_message, user_id, session_id, mode='chat', max_tokens=50000):
    """Enhanced generator function for streaming chat responses with mode support"""
    try:
        # Save user message with fallback
        try:
            save_result = mcp_service.save_message(user_id, session_id, 'user', user_message)
            if not save_result['success']:
                db_manager.save_message(user_id, session_id, 'user', user_message)
        except Exception as e:
            print(f"[Save Message Error] {e}")
            db_manager.save_message(user_id, session_id, 'user', user_message)

        # Get chat history for context
        history = db_manager.get_session_messages(user_id, session_id)
        memory_context = "\n".join([f"{m['role'].capitalize()}: {m['message']}" for m in history[-10:]])

        # Mode-specific context building
        vector_context = ""
        enhanced_context = memory_context

        if mode in ['document', 'rag']:
            # Get relevant documents from vector store with fallback
            try:
                doc_search_result = mcp_service.search_documents(session_id, user_message)
                if doc_search_result['success'] and doc_search_result['documents']:
                    vector_context = "\n".join([
                        doc.get('text', '') for doc in doc_search_result['documents']
                    ])
                    enhanced_context = f"Chat History:\n{memory_context}\n\nRelevant Documents:\n{vector_context}"
                elif mode == 'document':
                    enhanced_context = f"Chat History:\n{memory_context}\n\nNote: No documents found. Please upload a document first."
            except Exception as e:
                print(f"[Vector Search Error] {e}")
                # Fallback to direct vector store
                try:
                    from utils.vector_store import VectorStore
                    vector_store = VectorStore()
                    if vector_store.collection_exists(session_id):
                        relevant_docs = vector_store.search_documents(session_id, user_message)
                        vector_context = "\n".join([doc.get('text', '') for doc in relevant_docs])
                        enhanced_context = f"Chat History:\n{memory_context}\n\nRelevant Documents:\n{vector_context}"
                except Exception as fallback_error:
                    print(f"[Vector Store Fallback Error] {fallback_error}")
                    if mode == 'document':
                        enhanced_context = f"Chat History:\n{memory_context}\n\nNote: Document search unavailable."

        # Generate streaming response with enhanced LLM service
        full_response = ""
        
        # Check if tools are needed (web search, image generation, etc.)
        llm_service = enhanced_chat_service.llm_service
        tool_analysis = llm_service._analyze_tool_requirements(user_message)
        
        if tool_analysis['requires_tools']:
            # Execute tools first
            try:
                tool_results = llm_service._execute_tools(tool_analysis['tools'], user_message, user_id, session_id)
                enhanced_context = llm_service._build_enhanced_context(enhanced_context, tool_results)
                
                # Yield tool execution status
                yield f"data: {json.dumps({'tool_status': 'Tools executed', 'tools': [t['type'] for t in tool_analysis['tools']]})}\n\n"
            except Exception as tool_error:
                print(f"[Tool Execution Error] {tool_error}")
                yield f"data: {json.dumps({'tool_status': 'Tool execution failed', 'error': str(tool_error)})}\n\n"

        # Generate streaming response with enhanced context and higher token limit
        try:
            for chunk in llm_service.generate_streaming_response(user_message, enhanced_context, max_tokens=max_tokens):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                time.sleep(0.02)  # Slightly faster streaming
        except Exception as e:
            print(f"[Streaming Error] {e}")
            # Fallback to non-streaming response
            try:
                fallback_response = llm_service.generate_response(user_message, enhanced_context, max_tokens=max_tokens)
                full_response = fallback_response
                yield f"data: {json.dumps({'content': fallback_response})}\n\n"
            except Exception as fallback_error:
                print(f"[Fallback Response Error] {fallback_error}")
                full_response = "I apologize, but I'm experiencing technical difficulties. Please try again."
                yield f"data: {json.dumps({'content': full_response})}\n\n"

        # Save complete AI response with fallback
        try:
            save_result = mcp_service.save_message(user_id, session_id, 'assistant', full_response)
            if not save_result['success']:
                db_manager.save_message(user_id, session_id, 'assistant', full_response)
        except Exception as e:
            print(f"[Save Response Error] {e}")
            db_manager.save_message(user_id, session_id, 'assistant', full_response)
        
        yield f"data: [DONE]\n\n"

    except Exception as e:
        print(f"[enhanced_stream_chat_response] Error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@enhanced_api_bp.route('/enhanced/upload_file', methods=['POST'])
def enhanced_upload_file():
    """Enhanced file upload with mode-aware processing"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        file = request.files.get('file')
        
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400

        # Process with original file service
        result = file_service.process_uploaded_file(
            file, 
            session['session_id'], 
            session['user_id']
        )

        # Enhanced processing for documents
        if result['type'] == 'document':
            result['mcp_enhanced'] = True
            result['mcp_status'] = 'Document processed and ready for chat operations'

        # Save document info to database
        if result['type'] == 'document':
            db_manager.save_document(
                session['user_id'],
                session['session_id'],
                result['filename'],
                file.content_type,
                0  # Size already calculated in service
            )

        return jsonify(result)
    except Exception as e:
        print(f"[enhanced_upload_file] Error: {e}")
        return jsonify({'error': str(e)}), 400

@enhanced_api_bp.route('/enhanced/generate_image', methods=['POST'])
def enhanced_generate_image():
    """Enhanced image generation using MCP"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Use MCP service for image generation (with fallback)
        try:
            result = mcp_service.generate_image(prompt)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'image_url': result['result'].get('image_url'),
                    'prompt': prompt,
                    'mcp_enabled': True
                })
        except Exception as mcp_error:
            print(f"[MCP Image Generation Error] {mcp_error}")
        
        # Fallback to direct image service
        try:
            from services.image_service import ImageService
            image_service = ImageService()
            image_url = image_service.generate_image(prompt)
            
            if image_url:
                return jsonify({
                    'success': True,
                    'image_url': image_url,
                    'prompt': prompt,
                    'mcp_enabled': False
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Image generation failed',
                    'mcp_enabled': False
                }), 500
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'error': f'Image generation failed: {str(fallback_error)}',
                'mcp_enabled': False
            }), 500

    except Exception as e:
        print(f"[enhanced_generate_image] Error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_api_bp.route('/enhanced/web_search', methods=['POST'])
def enhanced_web_search():
    """Enhanced web search using MCP with Serper.dev"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        num_results = data.get('num_results', 5)
        search_type = data.get('search_type', 'web')

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Use MCP service for web search with Serper.dev
        try:
            result = mcp_service.web_search(query, num_results, search_type)
            
            return jsonify({
                'success': result['success'],
                'results': result.get('results', {}),
                'query': query,
                'search_type': search_type,
                'mcp_enabled': True,
                'provider': 'Serper.dev',
                'error': result.get('error')
            })
        except Exception as e:
            print(f"[MCP Web Search Error] {e}")
            return jsonify({
                'success': False,
                'error': f'Web search failed: {str(e)}',
                'query': query,
                'search_type': search_type,
                'mcp_enabled': False
            }), 500

    except Exception as e:
        print(f"[enhanced_web_search] Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'mcp_enabled': False
        }), 500

# Keep all other routes with better error handling
@enhanced_api_bp.route('/get_chat_sessions')
def get_chat_sessions():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        sessions = enhanced_chat_service.get_user_sessions(session['user_id'])
        return jsonify(sessions)
    except Exception as e:
        print(f"[get_chat_sessions] Error: {e}")
        return jsonify({'error': 'Failed to get chat sessions'}), 500

@enhanced_api_bp.route('/load_session/<session_id>')
def load_session(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        messages = enhanced_chat_service.get_session_messages(session['user_id'], session_id)
        return jsonify(messages)
    except Exception as e:
        print(f"[load_session] Error: {e}")
        return jsonify({'error': 'Failed to load session'}), 500

@enhanced_api_bp.route('/new_session')
def new_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    session['session_id'] = f"sess_{str(uuid.uuid4()).replace('-', '')}"
    return jsonify({'session_id': session['session_id']})

# Fallback routes for compatibility
@enhanced_api_bp.route('/send_message', methods=['POST'])
def fallback_send_message():
    """Fallback to enhanced send_message"""
    return enhanced_send_message()

@enhanced_api_bp.route('/upload_file', methods=['POST'])
def fallback_upload_file():
    """Fallback to enhanced upload_file"""
    return enhanced_upload_file()

@enhanced_api_bp.route('/web_search', methods=['POST'])
def fallback_web_search():
    """Fallback to enhanced web_search"""
    return enhanced_web_search()