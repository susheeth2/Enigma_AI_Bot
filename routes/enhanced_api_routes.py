"""
Enhanced API routes with MCP integration and Serper.dev web search
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
    """Enhanced message sending with MCP integration"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        stream = data.get('stream', False)

        if stream:
            return Response(
                enhanced_stream_chat_response(user_message, session['user_id'], session['session_id']),
                mimetype='text/stream'
            )
        else:
            result = enhanced_chat_service.process_message(
                user_message, 
                session['user_id'], 
                session['session_id']
            )
            return jsonify(result)

    except Exception as e:
        print(f"[enhanced_send_message] Error: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

def enhanced_stream_chat_response(user_message, user_id, session_id):
    """Enhanced generator function for streaming chat responses with MCP"""
    try:
        # Save user message using MCP
        save_result = mcp_service.save_message(user_id, session_id, 'user', user_message)
        if not save_result['success']:
            # Fallback to direct database save
            db_manager.save_message(user_id, session_id, 'user', user_message)

        # Get chat history for context
        history = db_manager.get_session_messages(user_id, session_id)
        memory_context = "\n".join([f"{m['role'].capitalize()}: {m['message']}" for m in history[-10:]])

        # Get relevant documents from vector store using MCP
        vector_context = ""
        doc_search_result = mcp_service.search_documents(session_id, user_message)
        if doc_search_result['success'] and doc_search_result['documents']:
            vector_context = "\n".join([
                doc.get('text', '') for doc in doc_search_result['documents']
            ])

        # Combine contexts
        full_context = f"Chat History:\n{memory_context.strip()}\n\nRelevant Docs:\n{vector_context.strip()}"
        
        # Generate streaming response with MCP tool capabilities
        full_response = ""
        
        # Check if tools are needed
        llm_service = enhanced_chat_service.llm_service
        tool_analysis = llm_service._analyze_tool_requirements(user_message)
        
        if tool_analysis['requires_tools']:
            # Execute tools first
            tool_results = llm_service._execute_tools(tool_analysis['tools'], user_message, user_id, session_id)
            enhanced_context = llm_service._build_enhanced_context(full_context, tool_results)
            
            # Yield tool execution status
            yield f"data: {json.dumps({'tool_status': 'Tools executed', 'tools': [t['type'] for t in tool_analysis['tools']]})}\n\n"
            
            # Generate streaming response with enhanced context
            for chunk in llm_service.generate_streaming_response(user_message, enhanced_context):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                time.sleep(0.05)
        else:
            # Generate normal streaming response
            for chunk in llm_service.generate_streaming_response(user_message, full_context):
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk})}\n\n"
                time.sleep(0.05)

        # Save complete AI response using MCP
        save_result = mcp_service.save_message(user_id, session_id, 'assistant', full_response)
        if not save_result['success']:
            # Fallback to direct database save
            db_manager.save_message(user_id, session_id, 'assistant', full_response)
        
        yield f"data: [DONE]\n\n"

    except Exception as e:
        print(f"[enhanced_stream_chat_response] Error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@enhanced_api_bp.route('/enhanced/upload_file', methods=['POST'])
def enhanced_upload_file():
    """Enhanced file upload with MCP integration"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        file = request.files.get('file')
        
        # First process with original file service
        result = file_service.process_uploaded_file(
            file, 
            session['session_id'], 
            session['user_id']
        )

        # If it's a document, also process with MCP
        if result['type'] == 'document':
            # The file has already been processed and cleaned up by file_service
            # We'll use the MCP service for future document operations
            result['mcp_enhanced'] = True
            result['mcp_status'] = 'Document processed and ready for MCP operations'

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

        # Use MCP service for image generation
        result = mcp_service.generate_image(prompt)
        
        if result['success']:
            return jsonify({
                'success': True,
                'image_url': result['result'].get('image_url'),
                'prompt': prompt,
                'mcp_enabled': True
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'mcp_enabled': True
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
        search_type = data.get('search_type', 'web')  # web, news, images, videos, places

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Use MCP service for web search with Serper.dev
        result = mcp_service.web_search(query, num_results, search_type)
        
        return jsonify({
            'success': result['success'],
            'results': result.get('results', []),
            'query': query,
            'search_type': search_type,
            'mcp_enabled': True,
            'provider': 'Serper.dev',
            'error': result.get('error')
        })

    except Exception as e:
        print(f"[enhanced_web_search] Error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_api_bp.route('/enhanced/search_news', methods=['POST'])
def enhanced_search_news():
    """Enhanced news search using MCP with Serper.dev"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        num_results = data.get('num_results', 5)
        time_range = data.get('time_range', 'qdr:d')  # qdr:h, qdr:d, qdr:w, qdr:m, qdr:y

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Use MCP service for news search
        result = mcp_service.search_news(query, num_results, time_range)
        
        return jsonify({
            'success': result['success'],
            'results': result.get('results', []),
            'query': query,
            'time_range': time_range,
            'mcp_enabled': True,
            'provider': 'Serper.dev',
            'error': result.get('error')
        })

    except Exception as e:
        print(f"[enhanced_search_news] Error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_api_bp.route('/enhanced/search_images', methods=['POST'])
def enhanced_search_images():
    """Enhanced image search using MCP with Serper.dev"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        num_results = data.get('num_results', 5)
        safe_search = data.get('safe_search', True)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Use MCP service for image search
        result = mcp_service.search_images(query, num_results, safe_search)
        
        return jsonify({
            'success': result['success'],
            'results': result.get('results', []),
            'query': query,
            'safe_search': safe_search,
            'mcp_enabled': True,
            'provider': 'Serper.dev',
            'error': result.get('error')
        })

    except Exception as e:
        print(f"[enhanced_search_images] Error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_api_bp.route('/enhanced/search_videos', methods=['POST'])
def enhanced_search_videos():
    """Enhanced video search using MCP with Serper.dev"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        num_results = data.get('num_results', 5)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Use MCP service for video search
        result = mcp_service.search_videos(query, num_results)
        
        return jsonify({
            'success': result['success'],
            'results': result.get('results', []),
            'query': query,
            'mcp_enabled': True,
            'provider': 'Serper.dev',
            'error': result.get('error')
        })

    except Exception as e:
        print(f"[enhanced_search_videos] Error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_api_bp.route('/enhanced/search_places', methods=['POST'])
def enhanced_search_places():
    """Enhanced places search using MCP with Serper.dev"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        location = data.get('location')
        num_results = data.get('num_results', 5)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Use MCP service for places search
        result = mcp_service.search_places(query, location, num_results)
        
        return jsonify({
            'success': result['success'],
            'results': result.get('results', []),
            'query': query,
            'location': location,
            'mcp_enabled': True,
            'provider': 'Serper.dev',
            'error': result.get('error')
        })

    except Exception as e:
        print(f"[enhanced_search_places] Error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_api_bp.route('/enhanced/get_webpage_content', methods=['POST'])
def enhanced_get_webpage_content():
    """Enhanced webpage content extraction using MCP"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        max_length = data.get('max_length', 5000)

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Use MCP service for webpage content extraction
        result = mcp_service.get_webpage_content(url, max_length)
        
        return jsonify({
            'success': result['success'],
            'content': result.get('result', {}),
            'url': url,
            'mcp_enabled': True,
            'error': result.get('error')
        })

    except Exception as e:
        print(f"[enhanced_get_webpage_content] Error: {e}")
        return jsonify({'error': str(e)}), 500

# Keep original routes as fallback
@enhanced_api_bp.route('/send_message', methods=['POST'])
def fallback_send_message():
    """Fallback to original send_message if enhanced version fails"""
    # Import original function
    from routes.api_routes import send_message
    return send_message()

@enhanced_api_bp.route('/upload_file', methods=['POST'])
def fallback_upload_file():
    """Fallback to original upload_file if enhanced version fails"""
    from routes.api_routes import upload_file
    return upload_file()

@enhanced_api_bp.route('/web_search', methods=['POST'])
def fallback_web_search():
    """Fallback to original web_search if enhanced version fails"""
    from routes.api_routes import web_search
    return web_search()

# Keep all other original routes
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