"""
Enhanced Chat Service with MCP integration
"""
from datetime import datetime
from utils.database import DatabaseManager
from utils.vector_store import VectorStore
from services.enhanced_llm_service import EnhancedLLMService
from services.mcp_service import MCPService

class EnhancedChatService:
    """Enhanced service for handling chat functionality with MCP integration"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.vector_store = VectorStore()
        self.llm_service = EnhancedLLMService()
        self.mcp_service = MCPService()

    def process_message(self, user_message: str, user_id: int, session_id: str) -> dict:
        """Process user message with MCP-enhanced AI response"""
        try:
            # Save user message using MCP
            save_result = self.mcp_service.save_message(user_id, session_id, 'user', user_message)
            if not save_result['success']:
                print(f"[MCP Save Error] {save_result['error']}")
                # Fallback to direct database save
                self.db_manager.save_message(user_id, session_id, 'user', user_message)

            # Get chat history for context
            history = self.db_manager.get_session_messages(user_id, session_id)
            memory_context = "\n".join([f"{m['role'].capitalize()}: {m['message']}" for m in history[-10:]])

            # Get relevant documents from vector store using MCP
            vector_context = ""
            if self.vector_store.collection_exists(session_id):
                doc_search_result = self.mcp_service.search_documents(session_id, user_message)
                if doc_search_result['success'] and doc_search_result['documents']:
                    vector_context = "\n".join([
                        doc.get('text', '') for doc in doc_search_result['documents']
                    ])

            # Combine contexts
            full_context = f"Chat History:\n{memory_context.strip()}\n\nRelevant Docs:\n{vector_context.strip()}"
            
            # Generate AI response with MCP tool capabilities
            ai_response = self.llm_service.generate_response_with_tools(
                user_message, 
                full_context,
                user_id,
                session_id
            )

            # Save AI response using MCP
            save_result = self.mcp_service.save_message(user_id, session_id, 'assistant', ai_response)
            if not save_result['success']:
                print(f"[MCP Save Error] {save_result['error']}")
                # Fallback to direct database save
                self.db_manager.save_message(user_id, session_id, 'assistant', ai_response)

            return {
                'user_message': user_message,
                'ai_response': ai_response,
                'timestamp': datetime.now().isoformat(),
                'mcp_enabled': True
            }

        except Exception as e:
            print(f"[Enhanced Chat Service Error] {e}")
            # Fallback to original chat service behavior
            return self._fallback_process_message(user_message, user_id, session_id)

    def _fallback_process_message(self, user_message: str, user_id: int, session_id: str) -> dict:
        """Fallback to original chat processing without MCP"""
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
            'timestamp': datetime.now().isoformat(),
            'mcp_enabled': False
        }

    def get_chat_history(self, user_id: int) -> list:
        """Get chat history for user"""
        return self.db_manager.get_chat_history(user_id)

    def get_user_sessions(self, user_id: int) -> list:
        """Get all sessions for user"""
        return self.db_manager.get_user_sessions(user_id)

    def get_session_messages(self, user_id: int, session_id: str) -> list:
        """Get messages for specific session"""
        return self.db_manager.get_session_messages(user_id, session_id)

    def get_mcp_status(self) -> dict:
        """Get MCP service status"""
        return self.mcp_service.get_server_status()

    def list_available_tools(self) -> dict:
        """List all available MCP tools"""
        return self.mcp_service.list_available_tools()

    def process_file_with_mcp(self, file_path: str, session_id: str, user_id: int) -> dict:
        """Process uploaded file using MCP services"""
        try:
            # Process document using MCP vector server
            process_result = self.mcp_service.process_document(file_path)
            
            if process_result['success']:
                result_data = process_result['result']
                if isinstance(result_data, dict) and 'chunks' in result_data:
                    # Add documents to vector store using MCP
                    add_result = self.mcp_service.add_documents_to_vector_store(
                        session_id,
                        result_data['chunks'],
                        file_path
                    )
                    
                    return {
                        'success': True,
                        'chunks_processed': result_data.get('chunks_processed', 0),
                        'mcp_enabled': True,
                        'add_result': add_result
                    }
            
            return {
                'success': False,
                'error': process_result.get('error', 'Unknown error'),
                'mcp_enabled': True
            }
            
        except Exception as e:
            print(f"[MCP File Processing Error] {e}")
            return {
                'success': False,
                'error': str(e),
                'mcp_enabled': False
            }

    def analyze_image_with_mcp(self, image_path: str) -> dict:
        """Analyze image using MCP image server"""
        try:
            result = self.mcp_service.analyze_image(image_path)
            return {
                'success': result['success'],
                'description': result.get('result', {}).get('description', 'No description available'),
                'mcp_enabled': True
            }
        except Exception as e:
            print(f"[MCP Image Analysis Error] {e}")
            return {
                'success': False,
                'error': str(e),
                'mcp_enabled': False
            }