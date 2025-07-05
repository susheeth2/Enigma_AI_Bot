"""
Enhanced MCP Service with proper event loop handling
"""
import asyncio
import json
import threading
import concurrent.futures
from typing import Any, Dict, List, Optional
from mcp.mcp_client import (
    mcp_client,
    save_message_mcp,
    search_documents_mcp,
    generate_image_mcp,
    web_search_mcp
)

class MCPService:
    """Enhanced service for handling MCP operations in Flask context with proper event loop handling"""
    
    def __init__(self):
        self.client = mcp_client
        self.fallback_mode = False
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def _run_async_safe(self, coro):
        """Safely run async coroutine in sync context"""
        try:
            # Try to get the current event loop
            try:
                loop = asyncio.get_running_loop()
                # If there's already a running loop, use a thread executor
                future = self.executor.submit(asyncio.run, coro)
                return future.result(timeout=30)
            except RuntimeError:
                # No running loop, we can run directly
                return asyncio.run(coro)
        except Exception as e:
            print(f"[MCP Async Error] {e}")
            self.fallback_mode = True
            raise e

    def save_message(self, user_id: int, session_id: str, role: str, message: str) -> Dict[str, Any]:
        """Save message using MCP database server with fallback"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            result = self._run_async_safe(save_message_mcp(user_id, session_id, role, message))
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            print(f"[MCP Save Message Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_documents(self, session_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search documents using MCP vector server with fallback"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode', 'documents': []}
            
        try:
            result = self._run_async_safe(search_documents_mcp(session_id, query, top_k))
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
            print(f"[MCP Search Documents Error] {e}")
            return {
                'success': False,
                'error': str(e),
                'documents': []
            }

    def generate_image(self, prompt: str) -> Dict[str, Any]:
        """Generate image using MCP image server with fallback"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            result = self._run_async_safe(generate_image_mcp(prompt))
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
            print(f"[MCP Generate Image Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def web_search(self, query: str, num_results: int = 5, search_type: str = "web") -> Dict[str, Any]:
        """Perform web search using MCP web search server with Serper.dev"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode', 'search_type': search_type}
            
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
            
            # Create the coroutine for the tool call
            async def call_tool():
                return await self.client.call_tool('web_search', tool_name, arguments)
            
            result = self._run_async_safe(call_tool())
            
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
            print(f"[MCP Web Search Error] {e}")
            return {
                'success': False,
                'error': str(e),
                'search_type': search_type
            }

    def search_news(self, query: str, num_results: int = 5, time_range: str = "qdr:d") -> Dict[str, Any]:
        """Search news using MCP web search server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            async def call_tool():
                return await self.client.call_tool('web_search', 'search_news', {
                    'query': query,
                    'num_results': num_results,
                    'time_range': time_range
                })
            
            result = self._run_async_safe(call_tool())
            
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
            print(f"[MCP Search News Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_images(self, query: str, num_results: int = 5, safe_search: bool = True) -> Dict[str, Any]:
        """Search images using MCP web search server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            async def call_tool():
                return await self.client.call_tool('web_search', 'search_images', {
                    'query': query,
                    'num_results': num_results,
                    'safe_search': safe_search
                })
            
            result = self._run_async_safe(call_tool())
            
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
            print(f"[MCP Search Images Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_videos(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search videos using MCP web search server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            async def call_tool():
                return await self.client.call_tool('web_search', 'search_videos', {
                    'query': query,
                    'num_results': num_results
                })
            
            result = self._run_async_safe(call_tool())
            
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
            print(f"[MCP Search Videos Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search_places(self, query: str, location: str = None, num_results: int = 5) -> Dict[str, Any]:
        """Search places using MCP web search server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            arguments = {
                'query': query,
                'num_results': num_results
            }
            if location:
                arguments['location'] = location
            
            async def call_tool():
                return await self.client.call_tool('web_search', 'search_places', arguments)
                
            result = self._run_async_safe(call_tool())
            
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
            print(f"[MCP Search Places Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_webpage_content(self, url: str, max_length: int = 5000) -> Dict[str, Any]:
        """Extract webpage content using MCP web search server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            async def call_tool():
                return await self.client.call_tool('web_search', 'get_webpage_content', {
                    'url': url,
                    'max_length': max_length
                })
            
            result = self._run_async_safe(call_tool())
            
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
            print(f"[MCP Get Webpage Content Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def add_documents_to_vector_store(self, session_id: str, documents: List[Dict], filename: str) -> Dict[str, Any]:
        """Add documents to vector store using MCP vector server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            async def call_tool():
                return await self.client.call_tool('vector', 'add_documents', {
                    'session_id': session_id,
                    'documents': documents,
                    'filename': filename
                })
            
            result = self._run_async_safe(call_tool())
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            print(f"[MCP Add Documents Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process document using MCP vector server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            async def call_tool():
                return await self.client.call_tool('vector', 'process_document', {
                    'file_path': file_path
                })
            
            result = self._run_async_safe(call_tool())
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
            print(f"[MCP Process Document Error] {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using MCP image server"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
            
        try:
            async def call_tool():
                return await self.client.call_tool('image', 'analyze_image', {
                    'image_path': image_path
                })
            
            result = self._run_async_safe(call_tool())
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
            print(f"[MCP Analyze Image Error] {e}")
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
            print(f"[MCP Get Server Status Error] {e}")
            return {
                'success': False,
                'error': str(e),
                'servers': {}
            }

    def list_available_tools(self) -> Dict[str, Any]:
        """List all available tools across all servers"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode', 'tools': {}}
            
        try:
            all_tools = {}
            for server_name in ['database', 'vector', 'image', 'web_search']:
                try:
                    async def call_list_tools():
                        return await self.client.list_tools(server_name)
                    
                    tools = self._run_async_safe(call_list_tools())
                    all_tools[server_name] = tools
                except Exception as e:
                    print(f"[MCP List Tools Error for {server_name}] {e}")
                    all_tools[server_name] = []
            
            return {
                'success': True,
                'tools': all_tools
            }
        except Exception as e:
            print(f"[MCP List Available Tools Error] {e}")
            return {
                'success': False,
                'error': str(e),
                'tools': {}
            }

    def close_connections(self):
        """Close all MCP connections"""
        try:
            async def close_all():
                return await self.client.close_all_connections()
            
            self._run_async_safe(close_all())
            return {'success': True}
        except Exception as e:
            print(f"[MCP Close Connections Error] {e}")
            return {'success': False, 'error': str(e)}

    def reset_fallback_mode(self):
        """Reset fallback mode to try MCP again"""
        self.fallback_mode = False
        print("🔄 MCP fallback mode reset")

    def is_available(self) -> bool:
        """Check if MCP is available"""
        return not self.fallback_mode

    def __del__(self):
        """Cleanup executor on deletion"""
        try:
            self.executor.shutdown(wait=False)
        except:
            pass