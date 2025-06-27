import os
import base64
from werkzeug.utils import secure_filename
from config.settings import Config
from utils.document_processor import DocumentProcessor
from utils.vector_store import VectorStore
from services.llm_service import LLMService

class FileService:
    """Service for handling file uploads and processing"""
    
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()

    def process_uploaded_file(self, file, session_id, user_id):
        """Process uploaded file based on type"""
        if not file or not file.filename:
            raise ValueError('No file uploaded')

        filename = secure_filename(file.filename or "uploaded_file")
        file_path = os.path.join(self.upload_folder, filename)
        file.save(file_path)

        try:
            if filename.lower().endswith('.docx'):
                return self._process_document(file_path, filename, session_id)
            elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return self._process_image(file_path, filename)
            else:
                raise ValueError('Unsupported file type')
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)

    def _process_document(self, file_path, filename, session_id):
        """Process document file"""
        processed_text = self.doc_processor.process_document(file_path)
        self.vector_store.add_documents(session_id, processed_text, filename)
        
        return {
            'type': 'document',
            'filename': filename,
            'message': f'Document "{filename}" processed successfully!',
            'chunks': len(processed_text)
        }

    def _process_image(self, file_path, filename):
        """Process image file"""
        with open(file_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode("utf-8")
        
        image_url = f"data:image/jpeg;base64,{encoded}"
        ai_response = self.llm_service.generate_response(
            "Describe this image. Identify any characters, people, or objects and give details about them.",
            image_url=image_url
        )
        
        return {
            'type': 'image',
            'filename': filename,
            'description': ai_response,
            'message': f'Image "{filename}" analyzed successfully!'
        }