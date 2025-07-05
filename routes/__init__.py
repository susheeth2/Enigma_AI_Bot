from .auth_routes import auth_bp
from .chat_routes import chat_bp
from .image_routes import image_bp
from .enhanced_api_routes import enhanced_api_bp
from .mcp_routes import mcp_bp

def register_routes(app):
    """Register all route blueprints"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(enhanced_api_bp)
    app.register_blueprint(mcp_bp)