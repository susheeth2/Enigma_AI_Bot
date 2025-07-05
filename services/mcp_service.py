"""
MCP Service for integrating MCP functionality into the Flask application
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.client import (
    mcp_client,
    save_message_mcp,
    search_documents_mcp,
    generate_image_mcp,
    web_search_mcp
)

class MCPService:
    """Service for handling MCP operations in Flask context"""
    
    def __init__(self):
        self.client = mcp_client
        self._loop = None

    def _get_event_loop(self):
        """Get or create event loop for async operations"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def _run_async(self, coro):
        """Run async coroutine in sync context"""
        loop = self._get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)

    def save_message(self, user_id: int, session_id: str, role: str, message: str) -> Dict[str, Any]:
        """Save message using MCP database server"""
        try:
            result = self._run_async(save_message_mcp(user_id, session_id, role, message))
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_documents(self, session_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search documents using MCP vector server"""
        try:
            result = self._run_async(search_documents_mcp(session_id, query, top_k))
            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': True,
                'documents': result if isinstance(result, list) else [],
                'raw_result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'documents': []
            }

    def generate_image(self, prompt: str) -> Dict[str, Any]:
        """Generate image using MCP image server"""
        try:
            result = self._run_async(generate_image_mcp(prompt))
            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Perform web search using MCP web search server"""
        try:
            result = self._run_async(web_search_mcp(query, num_results))
            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': True,
                'results': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def add_documents_to_vector_store(self, session_id: str, documents: List[Dict], filename: str) -> Dict[str, Any]:
        """Add documents to vector store using MCP vector server"""
        try:
            result = self._run_async(
                self.client.call_tool('vector', 'add_documents', {
                    'session_id': session_id,
                    'documents': documents,
                    'filename': filename
                })
            )
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process document using MCP vector server"""
        try:
            result = self._run_async(
                self.client.call_tool('vector', 'process_document', {
                    'file_path': file_path
                })
            )
            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using MCP image server"""
        try:
            result = self._run_async(
                self.client.call_tool('image', 'analyze_image', {
                    'image_path': image_path
                })
            )
            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        try:
            status = self.client.get_server_status()
            return {
                'success': True,
                'servers': status
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'servers': {}
            }

    def list_available_tools(self) -> Dict[str, Any]:
        """List all available tools across all servers"""
        try:
            all_tools = {}
            for server_name in ['database', 'vector', 'image', 'web_search']:
                tools = self._run_async(self.client.list_tools(server_name))
                all_tools[server_name] = tools
            
            return {
                'success': True,
                'tools': all_tools
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tools': {}
            }

    def close_connections(self):
        """Close all MCP connections"""
        try:
            self._run_async(self.client.close_all_connections())
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}