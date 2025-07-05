"""
MCP Server for Database Operations
Exposes database functionality as MCP tools and resources
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.database import DatabaseManager

class DatabaseMCPServer:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.server = Server("database-server")
        self.setup_tools()
        self.setup_resources()

    def setup_tools(self):
        """Setup MCP tools for database operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="save_message",
                    description="Save a chat message to the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "User ID"},
                            "session_id": {"type": "string", "description": "Session ID"},
                            "role": {"type": "string", "enum": ["user", "assistant"], "description": "Message role"},
                            "message": {"type": "string", "description": "Message content"}
                        },
                        "required": ["user_id", "session_id", "role", "message"]
                    }
                ),
                Tool(
                    name="get_chat_history",
                    description="Retrieve chat history for a user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "User ID"},
                            "limit": {"type": "integer", "description": "Number of messages to retrieve", "default": 100}
                        },
                        "required": ["user_id"]
                    }
                ),
                Tool(
                    name="get_session_messages",
                    description="Get all messages for a specific session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "User ID"},
                            "session_id": {"type": "string", "description": "Session ID"}
                        },
                        "required": ["user_id", "session_id"]
                    }
                ),
                Tool(
                    name="save_document",
                    description="Save document metadata to database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "integer", "description": "User ID"},
                            "session_id": {"type": "string", "description": "Session ID"},
                            "filename": {"type": "string", "description": "Document filename"},
                            "file_type": {"type": "string", "description": "File type"},
                            "file_size": {"type": "integer", "description": "File size in bytes"}
                        },
                        "required": ["user_id", "session_id", "filename", "file_type", "file_size"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "save_message":
                    message_id = self.db_manager.save_message(
                        arguments["user_id"],
                        arguments["session_id"],
                        arguments["role"],
                        arguments["message"]
                    )
                    return [TextContent(
                        type="text",
                        text=f"Message saved successfully with ID: {message_id}"
                    )]
                
                elif name == "get_chat_history":
                    history = self.db_manager.get_chat_history(
                        arguments["user_id"],
                        arguments.get("limit", 100)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(history, default=str, indent=2)
                    )]
                
                elif name == "get_session_messages":
                    messages = self.db_manager.get_session_messages(
                        arguments["user_id"],
                        arguments["session_id"]
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(messages, default=str, indent=2)
                    )]
                
                elif name == "save_document":
                    doc_id = self.db_manager.save_document(
                        arguments["user_id"],
                        arguments["session_id"],
                        arguments["filename"],
                        arguments["file_type"],
                        arguments["file_size"]
                    )
                    return [TextContent(
                        type="text",
                        text=f"Document saved successfully with ID: {doc_id}"
                    )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )]

    def setup_resources(self):
        """Setup MCP resources for database data"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="database://users",
                    name="Users",
                    description="Access user information",
                    mimeType="application/json"
                ),
                Resource(
                    uri="database://sessions",
                    name="Chat Sessions",
                    description="Access chat session information",
                    mimeType="application/json"
                ),
                Resource(
                    uri="database://documents",
                    name="Documents",
                    description="Access document metadata",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            try:
                if uri == "database://users":
                    # Return basic user statistics (no sensitive data)
                    return json.dumps({
                        "resource": "users",
                        "description": "User management system",
                        "available_operations": ["authenticate", "create", "get_info"]
                    })
                
                elif uri == "database://sessions":
                    return json.dumps({
                        "resource": "sessions",
                        "description": "Chat session management",
                        "available_operations": ["get_user_sessions", "get_session_messages"]
                    })
                
                elif uri == "database://documents":
                    return json.dumps({
                        "resource": "documents",
                        "description": "Document metadata storage",
                        "available_operations": ["save_document", "get_user_documents"]
                    })
                
                else:
                    return json.dumps({"error": f"Unknown resource: {uri}"})
                    
            except Exception as e:
                return json.dumps({"error": f"Error reading resource {uri}: {str(e)}"})

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="database-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )

async def main():
    server = DatabaseMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())