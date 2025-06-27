import uuid
from flask import Blueprint, request, jsonify, session
from services.chat_service import ChatService
from services.file_service import FileService
from utils.database import DatabaseManager

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

        result = chat_service.process_message(
            user_message, 
            session['user_id'], 
            session['session_id']
        )
        return jsonify(result)

    except Exception as e:
        print(f"[send_message] Error: {e}")
        return jsonify({'error': 'Failed to process message'}), 500

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