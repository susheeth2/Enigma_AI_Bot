"""
Simplified MCP Client that avoids event loop conflicts
"""
import subprocess
import sys
import json
import tempfile
import os
from typing import Any, Dict, List, Optional

class MCPClient:
    """Simplified MCP Client that uses subprocess calls to avoid event loop issues"""
    
    def __init__(self):
        self.servers = {
            'database': 'mcp/servers/database_server.py',
            'vector': 'mcp/servers/vector_server.py',
            'image': 'mcp/servers/image_server.py',
            'web_search': 'mcp/servers/web_search_server.py'
        }

    def call_tool_sync(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool synchronously using subprocess"""
        try:
            if server_name not in self.servers:
                return f"Unknown server: {server_name}"

            # Create a simple script to call the MCP server
            script_content = f'''
import asyncio
import json
import sys
import subprocess
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async def call_tool():
    try:
        # Start the MCP server
        process = await asyncio.create_subprocess_exec(
            sys.executable, '{self.servers[server_name]}',
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
        result = await session.call_tool('{tool_name}', {json.dumps(arguments)})
        
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
    result = asyncio.run(call_tool())
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
                        print(f"[MCP Tool Error] {output}")
                        return None
                    return output
                else:
                    print(f"[MCP Script Error] {result.stderr}")
                    return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"[MCP Call Tool Error] {e}")
            return None

    def get_server_status(self) -> Dict[str, bool]:
        """Get connection status of all servers using process check"""
        try:
            import psutil
            
            status = {}
            for server_name in self.servers:
                status[server_name] = False
                
                # Check if server process is running
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if cmdline and len(cmdline) > 1:
                            script_path = cmdline[-1] if cmdline else ''
                            if f'{server_name}_server.py' in script_path:
                                status[server_name] = True
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            return status
        except ImportError:
            # Fallback if psutil is not available
            return {server_name: True for server_name in self.servers}
        except Exception as e:
            print(f"[MCP Status Error] {e}")
            return {server_name: False for server_name in self.servers}

# Global MCP client instance
mcp_client = MCPClient()

# Simplified convenience functions
def save_message_mcp(user_id: int, session_id: str, role: str, message: str) -> str:
    """Save message using MCP database server"""
    result = mcp_client.call_tool_sync('database', 'save_message', {
        'user_id': user_id,
        'session_id': session_id,
        'role': role,
        'message': message
    })
    return result if result is not None else ""

def search_documents_mcp(session_id: str, query: str, top_k: int = 5) -> str:
    """Search documents using MCP vector server"""
    result = mcp_client.call_tool_sync('vector', 'search_documents', {
        'session_id': session_id,
        'query': query,
        'top_k': top_k
    })
    return result if result is not None else ""

def generate_image_mcp(prompt: str) -> str:
    """Generate image using MCP image server"""
    result = mcp_client.call_tool_sync('image', 'generate_image', {
        'prompt': prompt
    })
    return result if result is not None else ""

def web_search_mcp(query: str, num_results: int = 5) -> str:
    """Perform web search using MCP web search server"""
    result = mcp_client.call_tool_sync('web_search', 'web_search', {
        'query': query,
        'num_results': num_results
    })
    return result if result is not None else ""