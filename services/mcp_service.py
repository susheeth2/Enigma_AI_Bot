"""
Enhanced MCP Service with complete event loop isolation
"""
import asyncio
import json
import threading
import concurrent.futures
import time
from typing import Any, Dict, List, Optional

class MCPService:
    """Enhanced service for handling MCP operations with complete event loop isolation"""
    
    def __init__(self):
        self.fallback_mode = False
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self._lock = threading.Lock()

    def _run_in_isolated_thread(self, func, *args, **kwargs):
        """Run function in completely isolated thread with its own event loop"""
        def isolated_runner():
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = loop.run_until_complete(func(*args, **kwargs))
                    else:
                        result = func(*args, **kwargs)
                    return {'success': True, 'result': result}
                finally:
                    loop.close()
                    
            except Exception as e:
                print(f"[MCP Isolated Thread Error] {e}")
                return {'success': False, 'error': str(e)}
        
        try:
            future = self.executor.submit(isolated_runner)
            result = future.result(timeout=30)
            return result
        except concurrent.futures.TimeoutError:
            return {'success': False, 'error': 'Operation timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def save_message(self, user_id: int, session_id: str, role: str, message: str) -> Dict[str, Any]:
        """Save message using MCP database server with complete isolation"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
        
        with self._lock:
            try:
                # Use direct HTTP call instead of async MCP client
                result = self._direct_mcp_call('database', 'save_message', {
                    'user_id': user_id,
                    'session_id': session_id,
                    'role': role,
                    'message': message
                })
                return result
            except Exception as e:
                print(f"[MCP Save Message Error] {e}")
                self.fallback_mode = True
                return {'success': False, 'error': str(e)}

    def search_documents(self, session_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search documents using MCP vector server with complete isolation"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode', 'documents': []}
        
        with self._lock:
            try:
                result = self._direct_mcp_call('vector', 'search_documents', {
                    'session_id': session_id,
                    'query': query,
                    'top_k': top_k
                })
                
                if result['success']:
                    # Parse the result if it's a string
                    documents = result.get('result', [])
                    if isinstance(documents, str):
                        try:
                            documents = json.loads(documents)
                        except json.JSONDecodeError:
                            documents = []
                    
                    return {
                        'success': True,
                        'documents': documents if isinstance(documents, list) else [],
                        'raw_result': result.get('result')
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Unknown error'),
                        'documents': []
                    }
            except Exception as e:
                print(f"[MCP Search Documents Error] {e}")
                return {'success': False, 'error': str(e), 'documents': []}

    def generate_image(self, prompt: str) -> Dict[str, Any]:
        """Generate image using MCP image server with complete isolation"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
        
        with self._lock:
            try:
                result = self._direct_mcp_call('image', 'generate_image', {
                    'prompt': prompt
                })
                
                if result['success']:
                    image_result = result.get('result')
                    if isinstance(image_result, str):
                        try:
                            image_result = json.loads(image_result)
                        except json.JSONDecodeError:
                            pass
                    
                    return {
                        'success': True,
                        'result': image_result
                    }
                else:
                    return result
            except Exception as e:
                print(f"[MCP Generate Image Error] {e}")
                return {'success': False, 'error': str(e)}

    def web_search(self, query: str, num_results: int = 5, search_type: str = "web") -> Dict[str, Any]:
        """Perform web search using MCP web search server with complete isolation"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode', 'search_type': search_type}
        
        with self._lock:
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
                        "location": "United States"
                    }
                else:
                    arguments = {
                        "query": query,
                        "num_results": num_results
                    }
                
                result = self._direct_mcp_call('web_search', tool_name, arguments)
                
                if result['success']:
                    search_result = result.get('result')
                    if isinstance(search_result, str):
                        try:
                            search_result = json.loads(search_result)
                        except json.JSONDecodeError:
                            pass
                    
                    return {
                        'success': True,
                        'results': search_result,
                        'search_type': search_type
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Unknown error'),
                        'search_type': search_type
                    }
            except Exception as e:
                print(f"[MCP Web Search Error] {e}")
                return {'success': False, 'error': str(e), 'search_type': search_type}

    def _direct_mcp_call(self, server: str, tool: str, arguments: dict) -> Dict[str, Any]:
        """Make direct call to MCP server without async client"""
        try:
            import subprocess
            import json
            import tempfile
            import os
            
            # Create a simple script to call MCP server
            script_content = f'''
import asyncio
import json
import sys
import subprocess
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async def call_mcp_tool():
    try:
        # Start the MCP server
        process = await asyncio.create_subprocess_exec(
            sys.executable, 'mcp/servers/{server}_server.py',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Create client session
        read_stream, write_stream = stdio_client(process)
        session = ClientSession(read_stream, write_stream)
        
        # Initialize session
        await session.initialize()
        
        # Call the tool
        result = await session.call_tool('{tool}', {json.dumps(arguments)})
        
        # Close session
        await session.close()
        process.terminate()
        await process.wait()
        
        # Return result
        if hasattr(result, 'content') and result.content:
            return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
        return str(result)
        
    except Exception as e:
        return f"Error: {{str(e)}}"

if __name__ == "__main__":
    result = asyncio.run(call_mcp_tool())
    print(result)
'''
            
            # Write script to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            try:
                # Run the script
                result = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.getcwd()
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output.startswith('Error:'):
                        return {'success': False, 'error': output[6:]}
                    else:
                        return {'success': True, 'result': output}
                else:
                    return {'success': False, 'error': f'Script failed: {result.stderr}'}
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"[Direct MCP Call Error] {e}")
            return {'success': False, 'error': str(e)}

    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers using simple process check"""
        try:
            import psutil
            
            server_processes = {
                'database': False,
                'vector': False,
                'image': False,
                'web_search': False
            }
            
            # Check if MCP server processes are running
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and len(cmdline) > 1:
                        script_path = cmdline[-1] if cmdline else ''
                        
                        for server_name in server_processes:
                            if f'{server_name}_server.py' in script_path:
                                server_processes[server_name] = True
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'success': True,
                'servers': server_processes
            }
        except ImportError:
            # Fallback if psutil is not available
            return {
                'success': True,
                'servers': {
                    'database': not self.fallback_mode,
                    'vector': not self.fallback_mode,
                    'image': not self.fallback_mode,
                    'web_search': not self.fallback_mode
                }
            }
        except Exception as e:
            print(f"[MCP Get Server Status Error] {e}")
            return {
                'success': False,
                'error': str(e),
                'servers': {}
            }

    def list_available_tools(self) -> Dict[str, Any]:
        """List all available tools (simplified)"""
        return {
            'success': True,
            'tools': {
                'database': ['save_message', 'get_chat_history', 'get_session_messages'],
                'vector': ['search_documents', 'add_documents', 'process_document'],
                'image': ['generate_image', 'analyze_image'],
                'web_search': ['web_search', 'search_news', 'search_images', 'search_videos', 'search_places']
            }
        }

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

    # Simplified methods for other operations
    def search_news(self, query: str, num_results: int = 5, time_range: str = "qdr:d") -> Dict[str, Any]:
        """Search news using simplified approach"""
        return self.web_search(query, num_results, "news")

    def search_images(self, query: str, num_results: int = 5, safe_search: bool = True) -> Dict[str, Any]:
        """Search images using simplified approach"""
        return self.web_search(query, num_results, "images")

    def search_videos(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Search videos using simplified approach"""
        return self.web_search(query, num_results, "videos")

    def search_places(self, query: str, location: str = None, num_results: int = 5) -> Dict[str, Any]:
        """Search places using simplified approach"""
        return self.web_search(query, num_results, "places")

    def get_webpage_content(self, url: str, max_length: int = 5000) -> Dict[str, Any]:
        """Extract webpage content using simplified approach"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
        
        try:
            result = self._direct_mcp_call('web_search', 'get_webpage_content', {
                'url': url,
                'max_length': max_length
            })
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_documents_to_vector_store(self, session_id: str, documents: List[Dict], filename: str) -> Dict[str, Any]:
        """Add documents to vector store using simplified approach"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
        
        try:
            result = self._direct_mcp_call('vector', 'add_documents', {
                'session_id': session_id,
                'documents': documents,
                'filename': filename
            })
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process document using simplified approach"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
        
        try:
            result = self._direct_mcp_call('vector', 'process_document', {
                'file_path': file_path
            })
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using simplified approach"""
        if self.fallback_mode:
            return {'success': False, 'error': 'MCP in fallback mode'}
        
        try:
            result = self._direct_mcp_call('image', 'analyze_image', {
                'image_path': image_path
            })
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def close_connections(self):
        """Close all MCP connections"""
        try:
            self.executor.shutdown(wait=True)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}