import os

class Config:
    """Application configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    
    # Folder configurations
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    IMAGE_OUTPUT_FOLDER = 'static/generated_images'
    
    # API configurations
    GRADIO_CLIENT_URL = os.getenv("GRADIO_CLIENT_URL")
    LLM_SERVER_URL = os.getenv('LLM_SERVER_URL', 'http://localhost:8000/v1/chat/completions')
    LLM_MODEL_PATH = os.getenv('LLM_MODEL_PATH', '/root/.cache/huggingface/')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    @staticmethod
    def ensure_directories():
        """Create necessary directories"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.IMAGE_OUTPUT_FOLDER, exist_ok=True)

# Initialize directories
Config.ensure_directories()