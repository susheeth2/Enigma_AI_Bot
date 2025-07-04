import uuid
from flask import Blueprint, request, jsonify, session, Response
from services.chat_service import ChatService
from services.file_service import FileService
from utils.database import DatabaseManager
import json
import time

api_bp = Blueprint('api', __name__)
chat_service = ChatService()
file_service = FileService()
db_manager = DatabaseManager()

@api_bp.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        stream = data.get('stream', False)

        if stream:
            return Response(
                stream_chat_response(user_message, session['user_id'], session['session_id']),
                mimetype='text/stream'
            )
        else:
            result = chat_service.process_message(
                user_message, 
                session['user_id'], 
                session['session_id']
            )
            return jsonify(result)

    except Exception as e:
        print(f"[send_message] Error: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

def stream_chat_response(user_message, user_id, session_id):
    """Generator function for streaming chat responses"""
    try:
        # Save user message
        db_manager.save_message(user_id, session_id, 'user', user_message)

        # Get chat history for context
        history = db_manager.get_session_messages(user_id, session_id)
        memory_context = "\n".join([f"{m['role'].capitalize()}: {m['message']}" for m in history[-10:]])

        # Get relevant documents from vector store
        vector_context = ""
        if chat_service.vector_store.collection_exists(session_id):
            relevant_docs = chat_service.vector_store.search_documents(session_id, user_message)
            vector_context = "\n".join([doc.get('text', '') for doc in relevant_docs])

        # Combine contexts
        full_context = f"Chat History:\n{memory_context.strip()}\n\nRelevant Docs:\n{vector_context.strip()}"
        
        # Generate streaming response
        full_response = ""
        for chunk in chat_service.llm_service.generate_streaming_response(user_message, full_context):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
            time.sleep(0.05)  # Small delay to simulate realistic streaming

        # Save complete AI response
        db_manager.save_message(user_id, session_id, 'assistant', full_response)
        
        yield f"data: [DONE]\n\n"

    except Exception as e:
        print(f"[stream_chat_response] Error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@api_bp.route('/web_search', methods=['POST'])
def web_search():
    """Placeholder for web search functionality"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        # TODO: Implement actual web search functionality
        # This could integrate with search APIs like Google, Bing, or DuckDuckGo
        
        result = {
            'query': query,
            'results': [
                {
                    'title': 'Web Search Coming Soon',
                    'url': '#',
                    'snippet': f'Web search functionality for "{query}" will be implemented soon.'
                }
            ],
            'message': f'🔍 Web search for "{query}" - Feature coming soon!'
        }
        
        return jsonify(result)

    except Exception as e:
        print(f"[web_search] Error: {e}")
        return jsonify({'error': 'Failed to perform web search'}), 500

@api_bp.route('/upload_file', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        file = request.files.get('file')
        result = file_service.process_uploaded_file(
            file, 
            session['session_id'], 
            session['user_id']
        )

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
        print(f"[upload_file] Error: {e}")
        return jsonify({'error': str(e)}), 400

@api_bp.route('/get_chat_sessions')
def get_chat_sessions():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        sessions = chat_service.get_user_sessions(session['user_id'])
        return jsonify(sessions)
    except Exception as e:
        print(f"[get_chat_sessions] Error: {e}")
        return jsonify({'error': 'Failed to get chat sessions'}), 500

@api_bp.route('/load_session/<session_id>')
def load_session(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    try:
        messages = chat_service.get_session_messages(session['user_id'], session_id)
        return jsonify(messages)
    except Exception as e:
        print(f"[load_session] Error: {e}")
        return jsonify({'error': 'Failed to load session'}), 500

@api_bp.route('/new_session')
def new_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    session['session_id'] = f"sess_{str(uuid.uuid4()).replace('-', '')}"
    return jsonify({'session_id': session['session_id']})

# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500