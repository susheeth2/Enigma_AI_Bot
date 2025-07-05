"""
MCP Server for Vector Store Operations
Exposes vector store functionality as MCP tools and resources
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
from utils.vector_store import VectorStore
from utils.document_processor import DocumentProcessor

class VectorMCPServer:
    def __init__(self):
        self.vector_store = VectorStore()
        self.doc_processor = DocumentProcessor()
        self.server = Server("vector-server")
        self.setup_tools()
        self.setup_resources()

    def setup_tools(self):
        """Setup MCP tools for vector store operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="add_documents",
                    description="Add documents to vector store",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID"},
                            "documents": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "original_text": {"type": "string"},
                                        "embedding": {"type": "array", "items": {"type": "number"}}
                                    }
                                }
                            },
                            "filename": {"type": "string", "description": "Source filename"}
                        },
                        "required": ["session_id", "documents", "filename"]
                    }
                ),
                Tool(
                    name="search_documents",
                    description="Search documents in vector store",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID"},
                            "query": {"type": "string", "description": "Search query"},
                            "top_k": {"type": "integer", "description": "Number of results", "default": 5}
                        },
                        "required": ["session_id", "query"]
                    }
                ),
                Tool(
                    name="process_document",
                    description="Process a document file and extract embeddings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to document file"}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="delete_collection",
                    description="Delete a vector collection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID"}
                        },
                        "required": ["session_id"]
                    }
                ),
                Tool(
                    name="get_embedding",
                    description="Get embedding for text",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to embed"}
                        },
                        "required": ["text"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "add_documents":
                    success = self.vector_store.add_documents(
                        arguments["session_id"],
                        arguments["documents"],
                        arguments["filename"]
                    )
                    return [TextContent(
                        type="text",
                        text=f"Documents added successfully: {success}"
                    )]
                
                elif name == "search_documents":
                    results = self.vector_store.search_documents(
                        arguments["session_id"],
                        arguments["query"],
                        arguments.get("top_k", 5)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "process_document":
                    processed_chunks = self.doc_processor.process_document(
                        arguments["file_path"]
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "chunks_processed": len(processed_chunks),
                            "chunks": processed_chunks
                        }, indent=2)
                    )]
                
                elif name == "delete_collection":
                    success = self.vector_store.delete_collection(
                        arguments["session_id"]
                    )
                    return [TextContent(
                        type="text",
                        text=f"Collection deleted successfully: {success}"
                    )]
                
                elif name == "get_embedding":
                    embedding = self.doc_processor.get_embedding(
                        arguments["text"]
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "embedding": embedding,
                            "dimension": len(embedding) if embedding else 0
                        })
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
        """Setup MCP resources for vector store data"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="vector://collections",
                    name="Vector Collections",
                    description="Access vector store collections",
                    mimeType="application/json"
                ),
                Resource(
                    uri="vector://embeddings",
                    name="Embeddings",
                    description="Access embedding functionality",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            try:
                if uri == "vector://collections":
                    return json.dumps({
                        "resource": "collections",
                        "description": "Vector store collection management",
                        "available_operations": ["create", "delete", "search", "add_documents"]
                    })
                
                elif uri == "vector://embeddings":
                    return json.dumps({
                        "resource": "embeddings",
                        "description": "Text embedding generation",
                        "model": "nomic-ai/nomic-embed-text-v1.5",
                        "dimension": 768
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
                    server_name="vector-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )

async def main():
    server = VectorMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())