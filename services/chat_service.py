from datetime import datetime
from utils.database import DatabaseManager
from utils.vector_store import VectorStore
from services.llm_service import LLMService

class ChatService:
    """Service for handling chat functionality"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.vector_store = VectorStore()
        self.llm_service = LLMService()

    def process_message(self, user_message, user_id, session_id):
        """Process user message and generate AI response"""
        # Save user message
        self.db_manager.save_message(user_id, session_id, 'user', user_message)

        # Get chat history for context
        history = self.db_manager.get_session_messages(user_id, session_id)
        memory_context = "\n".join([f"{m['role'].capitalize()}: {m['message']}" for m in history[-10:]])

        # Get relevant documents from vector store
        vector_context = ""
        if self.vector_store.collection_exists(session_id):
            relevant_docs = self.vector_store.search_documents(session_id, user_message)
            vector_context = "\n".join([doc.get('text', '') for doc in relevant_docs])

        # Combine contexts
        full_context = f"Chat History:\n{memory_context.strip()}\n\nRelevant Docs:\n{vector_context.strip()}"
        
        # Generate AI response
        ai_response = self.llm_service.generate_response(user_message, full_context)

        # Save AI response
        self.db_manager.save_message(user_id, session_id, 'assistant', ai_response)

        return {
            'user_message': user_message,
            'ai_response': ai_response,
            'timestamp': datetime.now().isoformat()
        }

    def get_chat_history(self, user_id):
        """Get chat history for user"""
        return self.db_manager.get_chat_history(user_id)

    def get_user_sessions(self, user_id):
        """Get all sessions for user"""
        return self.db_manager.get_user_sessions(user_id)

    def get_session_messages(self, user_id, session_id):
        """Get messages for specific session"""
        return self.db_manager.get_session_messages(user_id, session_id)