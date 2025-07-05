"""
MCP Service for integrating MCP functionality into the Flask application
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.mcp_client import (
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

    def web_search(self, query: str, num_results: int = 5, search_type: str = "web") -> Dict[str, Any]:
        """Perform web search using MCP web search server with Serper.dev"""
        try:
            # Map search types to MCP tools
            tool_mapping = {
                "web": "web_search",
                "news": "search_news", 
                "images": "search_images",
                "videos": "search_videos",
                "places": "search_places"
            }
            
            tool_name = tool_mapping.get(search_type, "web_search")
            
            # Prepare arguments based on search type
            if search_type == "places":
                arguments = {
                    "query": query,
                    "num_results": num_results,
                    "location": "United States"  # Default location
                }
            else:
                arguments = {
                    "query": query,
                    "num_results": num_results
                }
            
            result = self._run_async(
                self.client.call_tool('web_search', tool_name, arguments)
            )
            
            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass
            
            return {
                'success': True,
                'results': result,
                'search_type': search_type
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'search_type': search_type
            }

    def search_news(self, query: str, num_results: int = 5, time_range: str = "qdr:d") -> Dict[str, Any]:
        """Search news using MCP web search server"""
        try:
            result = self._run_async(
                self.client.call_tool('web_search', 'search_news', {
                    'query': query,
                    'num_results': num_results,
                    'time_range': time_range
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
                'results': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_images(self, query: str, num_results: int = 5, safe_search: bool = True) -> Dict[str, Any]:
        """Search images using MCP web search server"""
        try:
            result = self._run_async(
                self.client.call_tool('web_search', 'search_images', {
                    'query': query,
                    'num_results': num_results,
                    'safe_search': safe_search
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
                'results': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_videos(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search videos using MCP web search server"""
        try:
            result = self._run_async(
                self.client.call_tool('web_search', 'search_videos', {
                    'query': query,
                    'num_results': num_results
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
                'results': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_places(self, query: str, location: str = None, num_results: int = 5) -> Dict[str, Any]:
        """Search places using MCP web search server"""
        try:
            arguments = {
                'query': query,
                'num_results': num_results
            }
            if location:
                arguments['location'] = location
                
            result = self._run_async(
                self.client.call_tool('web_search', 'search_places', arguments)
            )
            
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

    def get_webpage_content(self, url: str, max_length: int = 5000) -> Dict[str, Any]:
        """Extract webpage content using MCP web search server"""
        try:
            result = self._run_async(
                self.client.call_tool('web_search', 'get_webpage_content', {
                    'url': url,
                    'max_length': max_length
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