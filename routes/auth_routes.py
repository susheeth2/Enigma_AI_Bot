import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils.auth import AuthManager

auth_bp = Blueprint('auth', __name__)
auth_manager = AuthManager()

@auth_bp.route('/')
def index():
    return redirect(url_for('chat.chat_page')) if 'user_id' in session else redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')

        if action == 'login':
            user = auth_manager.authenticate_user(username, password)
            if user:
                session.update({
                    'user_id': user['id'],
                    'username': user['username'],
                    'session_id': f"sess_{str(uuid.uuid4()).replace('-', '')}"
                })
                flash('Login successful!', 'success')
                return redirect(url_for('chat.chat_page'))
            else:
                flash('Invalid credentials', 'error')
        elif action == 'register':
            email = request.form.get('email')
            if auth_manager.create_user(username, password, email):
                flash('Registration successful!', 'success')
            else:
                flash('Username already exists', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if 'user_id' in session and 'session_id' in session:
        try:
            from utils.vector_store import VectorStore
            vector_store = VectorStore()
            vector_store.delete_collection(session['session_id'])
        except Exception as e:
            print(f"[logout] Cleanup error: {e}")
        session.clear()
        flash('Logged out successfully!', 'success')
    return redirect(url_for('auth.login'))