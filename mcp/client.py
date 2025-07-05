"""
MCP Client for integrating with MCP servers
"""
import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self):
        self.sessions = {}
        self.servers = {
            'database': {
                'command': [sys.executable, 'mcp/servers/database_server.py'],
                'session': None
            },
            'vector': {
                'command': [sys.executable, 'mcp/servers/vector_server.py'],
                'session': None
            },
            'image': {
                'command': [sys.executable, 'mcp/servers/image_server.py'],
                'session': None
            },
            'web_search': {
                'command': [sys.executable, 'mcp/servers/web_search_server.py'],
                'session': None
            }
        }

    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to an MCP server"""
        try:
            if server_name not in self.servers:
                print(f"Unknown server: {server_name}")
                return False

            server_config = self.servers[server_name]
            
            # Start the server process
            process = await asyncio.create_subprocess_exec(
                *server_config['command'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Create client session
            read_stream, write_stream = stdio_client(process)
            session = ClientSession(read_stream, write_stream)
            
            # Initialize the session
            await session.initialize()
            
            server_config['session'] = session
            server_config['process'] = process
            
            print(f"✅ Connected to {server_name} MCP server")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to {server_name} server: {str(e)}")
            return False

    async def disconnect_from_server(self, server_name: str):
        """Disconnect from an MCP server"""
        try:
            if server_name in self.servers and self.servers[server_name]['session']:
                session = self.servers[server_name]['session']
                process = self.servers[server_name].get('process')
                
                # Close session
                await session.close()
                
                # Terminate process
                if process:
                    process.terminate()
                    await process.wait()
                
                self.servers[server_name]['session'] = None
                self.servers[server_name]['process'] = None
                
                print(f"✅ Disconnected from {server_name} MCP server")
                
        except Exception as e:
            print(f"❌ Error disconnecting from {server_name} server: {str(e)}")

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Call a tool on an MCP server"""
        try:
            if server_name not in self.servers:
                return f"Unknown server: {server_name}"

            session = self.servers[server_name]['session']
            if not session:
                # Try to connect if not connected
                if not await self.connect_to_server(server_name):
                    return f"Failed to connect to {server_name} server"
                session = self.servers[server_name]['session']

            # Call the tool
            result = await session.call_tool(tool_name, arguments)
            
            # Extract text content from result
            if result and hasattr(result, 'content') and result.content:
                return result.content[0].text if result.content[0].type == 'text' else str(result.content[0])
            
            return str(result)
            
        except Exception as e:
            return f"Error calling tool {tool_name} on {server_name}: {str(e)}"

    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on an MCP server"""
        try:
            if server_name not in self.servers:
                return []

            session = self.servers[server_name]['session']
            if not session:
                if not await self.connect_to_server(server_name):
                    return []
                session = self.servers[server_name]['session']

            tools = await session.list_tools()
            return [tool.model_dump() for tool in tools.tools] if tools else []
            
        except Exception as e:
            print(f"Error listing tools for {server_name}: {str(e)}")
            return []

    async def read_resource(self, server_name: str, uri: str) -> Optional[str]:
        """Read a resource from an MCP server"""
        try:
            if server_name not in self.servers:
                return f"Unknown server: {server_name}"

            session = self.servers[server_name]['session']
            if not session:
                if not await self.connect_to_server(server_name):
                    return f"Failed to connect to {server_name} server"
                session = self.servers[server_name]['session']

            result = await session.read_resource(uri)
            return result.contents[0].text if result and result.contents else None
            
        except Exception as e:
            return f"Error reading resource {uri} from {server_name}: {str(e)}"

    async def list_resources(self, server_name: str) -> List[Dict[str, Any]]:
        """List available resources on an MCP server"""
        try:
            if server_name not in self.servers:
                return []

            session = self.servers[server_name]['session']
            if not session:
                if not await self.connect_to_server(server_name):
                    return []
                session = self.servers[server_name]['session']

            resources = await session.list_resources()
            return [resource.model_dump() for resource in resources.resources] if resources else []
            
        except Exception as e:
            print(f"Error listing resources for {server_name}: {str(e)}")
            return []

    async def close_all_connections(self):
        """Close all MCP server connections"""
        for server_name in self.servers:
            await self.disconnect_from_server(server_name)

    def get_server_status(self) -> Dict[str, bool]:
        """Get connection status of all servers"""
        return {
            server_name: config['session'] is not None
            for server_name, config in self.servers.items()
        }

# Global MCP client instance
mcp_client = MCPClient()

# Convenience functions for common operations
async def save_message_mcp(user_id: int, session_id: str, role: str, message: str) -> str:
    """Save message using MCP database server"""
    return await mcp_client.call_tool('database', 'save_message', {
        'user_id': user_id,
        'session_id': session_id,
        'role': role,
        'message': message
    })

async def search_documents_mcp(session_id: str, query: str, top_k: int = 5) -> str:
    """Search documents using MCP vector server"""
    return await mcp_client.call_tool('vector', 'search_documents', {
        'session_id': session_id,
        'query': query,
        'top_k': top_k
    })

async def generate_image_mcp(prompt: str) -> str:
    """Generate image using MCP image server"""
    return await mcp_client.call_tool('image', 'generate_image', {
        'prompt': prompt
    })

async def web_search_mcp(query: str, num_results: int = 5) -> str:
    """Perform web search using MCP web search server"""
    return await mcp_client.call_tool('web_search', 'web_search', {
        'query': query,
        'num_results': num_results
    })