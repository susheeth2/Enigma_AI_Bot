from flask import Blueprint, render_template, session, redirect, url_for
from services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__)
chat_service = ChatService()

@chat_bp.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    chat_history = chat_service.get_chat_history(session['user_id'])
    return render_template('chat.html', username=session['username'], chat_history=chat_history)