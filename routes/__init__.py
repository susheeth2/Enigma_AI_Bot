from .auth_routes import auth_bp
from .chat_routes import chat_bp
from .image_routes import image_bp
from .api_routes import api_bp

def register_routes(app):
    """Register all route blueprints"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(api_bp)