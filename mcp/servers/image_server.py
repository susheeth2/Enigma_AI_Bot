"""
MCP Server for Image Operations
Exposes image generation and processing functionality as MCP tools
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

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from services.image_service import ImageService
from utils.image_processor import ImageProcessor

class ImageMCPServer:
    def __init__(self):
        self.image_service = ImageService()
        self.image_processor = ImageProcessor()
        self.server = Server("image-server")
        self.setup_tools()
        self.setup_resources()

    def setup_tools(self):
        """Setup MCP tools for image operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="generate_image",
                    description="Generate an image from text prompt",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "Text prompt for image generation"}
                        },
                        "required": ["prompt"]
                    }
                ),
                Tool(
                    name="analyze_image",
                    description="Analyze an image and provide description",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {"type": "string", "description": "Path to image file"}
                        },
                        "required": ["image_path"]
                    }
                ),
                Tool(
                    name="get_image_info",
                    description="Get technical information about an image",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {"type": "string", "description": "Path to image file"}
                        },
                        "required": ["image_path"]
                    }
                ),
                Tool(
                    name="resize_image",
                    description="Resize an image to specified dimensions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {"type": "string", "description": "Path to image file"},
                            "max_width": {"type": "integer", "description": "Maximum width", "default": 800},
                            "max_height": {"type": "integer", "description": "Maximum height", "default": 600}
                        },
                        "required": ["image_path"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "generate_image":
                    image_url = self.image_service.generate_image(arguments["prompt"])
                    if image_url:
                        return [TextContent(
                            type="text",
                            text=json.dumps({
                                "success": True,
                                "image_url": image_url,
                                "prompt": arguments["prompt"]
                            })
                        )]
                    else:
                        return [TextContent(
                            type="text",
                            text=json.dumps({
                                "success": False,
                                "error": "Failed to generate image"
                            })
                        )]
                
                elif name == "analyze_image":
                    description = self.image_processor.analyze_with_ai(arguments["image_path"])
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "image_path": arguments["image_path"],
                            "description": description
                        })
                    )]
                
                elif name == "get_image_info":
                    info = self.image_processor.get_image_info(arguments["image_path"])
                    return [TextContent(
                        type="text",
                        text=json.dumps(info if info else {"error": "Could not get image info"})
                    )]
                
                elif name == "resize_image":
                    max_size = (
                        arguments.get("max_width", 800),
                        arguments.get("max_height", 600)
                    )
                    success = self.image_processor.resize_image(
                        arguments["image_path"],
                        max_size
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": success,
                            "image_path": arguments["image_path"],
                            "max_size": max_size
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
        """Setup MCP resources for image data"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="image://generator",
                    name="Image Generator",
                    description="Access image generation capabilities",
                    mimeType="application/json"
                ),
                Resource(
                    uri="image://processor",
                    name="Image Processor",
                    description="Access image processing capabilities",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            try:
                if uri == "image://generator":
                    return json.dumps({
                        "resource": "generator",
                        "description": "AI-powered image generation from text prompts",
                        "available_operations": ["generate_image"],
                        "supported_formats": ["PNG", "JPEG", "WebP"]
                    })
                
                elif uri == "image://processor":
                    return json.dumps({
                        "resource": "processor",
                        "description": "Image analysis and processing tools",
                        "available_operations": ["analyze_image", "get_image_info", "resize_image"],
                        "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
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
                    server_name="image-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )

async def main():
    server = ImageMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())