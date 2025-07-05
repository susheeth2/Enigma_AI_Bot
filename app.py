import os
from flask import Flask
from dotenv import load_dotenv
from config.settings import Config
from routes import register_routes
from utils.database import DatabaseManager

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register all routes (including enhanced routes)
    register_routes(app)
    
    return app

def main():
    app = create_app()
    
    try:
        db_manager = DatabaseManager()
        db_manager.init_database()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
    
    # Optional: Start MCP servers automatically
    try:
        from mcp_startup import MCPServerManager
        mcp_manager = MCPServerManager()
        print("\n🤖 Starting MCP servers...")
        mcp_manager.start_all_servers()
        
        # Register cleanup on app shutdown
        import atexit
        atexit.register(lambda: mcp_manager.stop_all_servers())
        
    except Exception as e:
        print(f"⚠️  MCP servers could not be started: {str(e)}")
        print("   Application will run without MCP integration")
    
    # Add error handler for better debugging
    @app.errorhandler(500)
    def internal_error(error):
        print(f"Internal server error: {error}")
        return "Internal server error", 500
    
    app.run(
        debug=os.getenv('DEBUG', 'true').lower() == 'true',
        host='0.0.0.0',
        port=5000,
        threaded=True  # Enable threading for better async handling
    )

if __name__ == '__main__':
    main()