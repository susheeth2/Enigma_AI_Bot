"""
MCP Server for Web Search Operations using Serper.dev
Exposes web search functionality as MCP tools
"""
import asyncio
import json
import requests
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
import os
from datetime import datetime, timedelta

class WebSearchMCPServer:
    def __init__(self):
        self.server = Server("web-search-server")
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        self.serper_base_url = "https://google.serper.dev"
        self.setup_tools()
        self.setup_resources()

    def setup_tools(self):
        """Setup MCP tools for web search operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="web_search",
                    description="Search the web using Google Search via Serper.dev",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "num_results": {"type": "integer", "description": "Number of results (1-100)", "default": 10, "minimum": 1, "maximum": 100},
                            "country": {"type": "string", "description": "Country code (e.g., 'us', 'uk', 'ca')", "default": "us"},
                            "location": {"type": "string", "description": "Location for localized results", "default": "United States"},
                            "language": {"type": "string", "description": "Language code (e.g., 'en', 'es', 'fr')", "default": "en"}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="search_news",
                    description="Search for recent news articles using Serper.dev",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "News search query"},
                            "num_results": {"type": "integer", "description": "Number of results (1-100)", "default": 10, "minimum": 1, "maximum": 100},
                            "country": {"type": "string", "description": "Country code for news", "default": "us"},
                            "time_range": {"type": "string", "description": "Time range", "enum": ["qdr:h", "qdr:d", "qdr:w", "qdr:m", "qdr:y"], "default": "qdr:d"}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="search_images",
                    description="Search for images using Serper.dev",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Image search query"},
                            "num_results": {"type": "integer", "description": "Number of results (1-100)", "default": 10, "minimum": 1, "maximum": 100},
                            "safe_search": {"type": "boolean", "description": "Enable safe search", "default": True}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="search_videos",
                    description="Search for videos using Serper.dev",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Video search query"},
                            "num_results": {"type": "integer", "description": "Number of results (1-100)", "default": 10, "minimum": 1, "maximum": 100}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="search_places",
                    description="Search for places and local businesses using Serper.dev",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Place search query"},
                            "location": {"type": "string", "description": "Location to search around"},
                            "num_results": {"type": "integer", "description": "Number of results (1-100)", "default": 10, "minimum": 1, "maximum": 100}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_webpage_content",
                    description="Extract content from a webpage",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to extract content from"},
                            "max_length": {"type": "integer", "description": "Maximum content length", "default": 5000}
                        },
                        "required": ["url"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            try:
                if name == "web_search":
                    results = await self._perform_web_search(
                        arguments["query"],
                        arguments.get("num_results", 10),
                        arguments.get("country", "us"),
                        arguments.get("location", "United States"),
                        arguments.get("language", "en")
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "search_news":
                    results = await self._search_news(
                        arguments["query"],
                        arguments.get("num_results", 10),
                        arguments.get("country", "us"),
                        arguments.get("time_range", "qdr:d")
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "search_images":
                    results = await self._search_images(
                        arguments["query"],
                        arguments.get("num_results", 10),
                        arguments.get("safe_search", True)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "search_videos":
                    results = await self._search_videos(
                        arguments["query"],
                        arguments.get("num_results", 10)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "search_places":
                    results = await self._search_places(
                        arguments["query"],
                        arguments.get("location"),
                        arguments.get("num_results", 10)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(results, indent=2)
                    )]
                
                elif name == "get_webpage_content":
                    content = await self._extract_webpage_content(
                        arguments["url"],
                        arguments.get("max_length", 5000)
                    )
                    return [TextContent(
                        type="text",
                        text=json.dumps(content, indent=2)
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

    async def _perform_web_search(self, query: str, num_results: int, country: str, location: str, language: str) -> Dict[str, Any]:
        """Perform web search using Serper.dev API"""
        if not self.serper_api_key:
            return {
                "error": "SERPER_API_KEY not configured",
                "message": "Please set SERPER_API_KEY environment variable"
            }

        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'q': query,
                'num': min(num_results, 100),
                'gl': country,
                'hl': language,
                'location': location
            }

            response = requests.post(
                f"{self.serper_base_url}/search",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response
            formatted_results = {
                "query": query,
                "total_results": data.get("searchInformation", {}).get("totalResults", "0"),
                "search_time": data.get("searchInformation", {}).get("searchTime", "0"),
                "organic_results": [],
                "knowledge_graph": data.get("knowledgeGraph"),
                "answer_box": data.get("answerBox"),
                "people_also_ask": data.get("peopleAlsoAsk", []),
                "related_searches": data.get("relatedSearches", [])
            }

            # Process organic results
            for result in data.get("organic", []):
                formatted_results["organic_results"].append({
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "displayed_link": result.get("displayedLink"),
                    "date": result.get("date"),
                    "sitelinks": result.get("sitelinks", [])
                })

            return formatted_results

        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request failed: {str(e)}",
                "query": query
            }
        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "query": query
            }

    async def _search_news(self, query: str, num_results: int, country: str, time_range: str) -> Dict[str, Any]:
        """Search for news using Serper.dev API"""
        if not self.serper_api_key:
            return {
                "error": "SERPER_API_KEY not configured",
                "message": "Please set SERPER_API_KEY environment variable"
            }

        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'q': query,
                'num': min(num_results, 100),
                'gl': country,
                'tbm': 'nws',
                'tbs': time_range
            }

            response = requests.post(
                f"{self.serper_base_url}/search",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response
            formatted_results = {
                "query": query,
                "time_range": time_range,
                "news_results": []
            }

            # Process news results
            for result in data.get("news", []):
                formatted_results["news_results"].append({
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "date": result.get("date"),
                    "source": result.get("source"),
                    "image_url": result.get("imageUrl")
                })

            return formatted_results

        except requests.exceptions.RequestException as e:
            return {
                "error": f"News search API request failed: {str(e)}",
                "query": query
            }
        except Exception as e:
            return {
                "error": f"News search failed: {str(e)}",
                "query": query
            }

    async def _search_images(self, query: str, num_results: int, safe_search: bool) -> Dict[str, Any]:
        """Search for images using Serper.dev API"""
        if not self.serper_api_key:
            return {
                "error": "SERPER_API_KEY not configured",
                "message": "Please set SERPER_API_KEY environment variable"
            }

        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'q': query,
                'num': min(num_results, 100),
                'tbm': 'isch',
                'safe': 'active' if safe_search else 'off'
            }

            response = requests.post(
                f"{self.serper_base_url}/search",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response
            formatted_results = {
                "query": query,
                "image_results": []
            }

            # Process image results
            for result in data.get("images", []):
                formatted_results["image_results"].append({
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "image_url": result.get("imageUrl"),
                    "image_width": result.get("imageWidth"),
                    "image_height": result.get("imageHeight"),
                    "thumbnail_url": result.get("thumbnailUrl"),
                    "source": result.get("source"),
                    "domain": result.get("domain"),
                    "link": result.get("link")
                })

            return formatted_results

        except requests.exceptions.RequestException as e:
            return {
                "error": f"Image search API request failed: {str(e)}",
                "query": query
            }
        except Exception as e:
            return {
                "error": f"Image search failed: {str(e)}",
                "query": query
            }

    async def _search_videos(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search for videos using Serper.dev API"""
        if not self.serper_api_key:
            return {
                "error": "SERPER_API_KEY not configured",
                "message": "Please set SERPER_API_KEY environment variable"
            }

        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'q': query,
                'num': min(num_results, 100),
                'tbm': 'vid'
            }

            response = requests.post(
                f"{self.serper_base_url}/search",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response
            formatted_results = {
                "query": query,
                "video_results": []
            }

            # Process video results
            for result in data.get("videos", []):
                formatted_results["video_results"].append({
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "channel": result.get("channel"),
                    "duration": result.get("duration"),
                    "date": result.get("date"),
                    "thumbnail": result.get("thumbnail")
                })

            return formatted_results

        except requests.exceptions.RequestException as e:
            return {
                "error": f"Video search API request failed: {str(e)}",
                "query": query
            }
        except Exception as e:
            return {
                "error": f"Video search failed: {str(e)}",
                "query": query
            }

    async def _search_places(self, query: str, location: str, num_results: int) -> Dict[str, Any]:
        """Search for places using Serper.dev API"""
        if not self.serper_api_key:
            return {
                "error": "SERPER_API_KEY not configured",
                "message": "Please set SERPER_API_KEY environment variable"
            }

        try:
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'q': query,
                'num': min(num_results, 100),
                'tbm': 'lcl'
            }

            if location:
                payload['location'] = location

            response = requests.post(
                f"{self.serper_base_url}/search",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response
            formatted_results = {
                "query": query,
                "location": location,
                "place_results": []
            }

            # Process place results
            for result in data.get("places", []):
                formatted_results["place_results"].append({
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "address": result.get("address"),
                    "latitude": result.get("latitude"),
                    "longitude": result.get("longitude"),
                    "rating": result.get("rating"),
                    "rating_count": result.get("ratingCount"),
                    "category": result.get("category"),
                    "phone_number": result.get("phoneNumber"),
                    "website": result.get("website"),
                    "cid": result.get("cid")
                })

            return formatted_results

        except requests.exceptions.RequestException as e:
            return {
                "error": f"Places search API request failed: {str(e)}",
                "query": query
            }
        except Exception as e:
            return {
                "error": f"Places search failed: {str(e)}",
                "query": query
            }

    async def _extract_webpage_content(self, url: str, max_length: int) -> Dict[str, Any]:
        """Extract content from webpage (basic implementation)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Basic text extraction (in a real implementation, you'd use BeautifulSoup or similar)
            content = response.text[:max_length]
            
            return {
                "url": url,
                "status_code": response.status_code,
                "content_length": len(content),
                "content": content,
                "headers": dict(response.headers)
            }
            
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "status": "failed"
            }

    def setup_resources(self):
        """Setup MCP resources for web search data"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="web://search",
                    name="Web Search",
                    description="Access web search capabilities via Serper.dev",
                    mimeType="application/json"
                ),
                Resource(
                    uri="web://news",
                    name="News Search",
                    description="Access news search capabilities via Serper.dev",
                    mimeType="application/json"
                ),
                Resource(
                    uri="web://images",
                    name="Image Search",
                    description="Access image search capabilities via Serper.dev",
                    mimeType="application/json"
                ),
                Resource(
                    uri="web://videos",
                    name="Video Search",
                    description="Access video search capabilities via Serper.dev",
                    mimeType="application/json"
                ),
                Resource(
                    uri="web://places",
                    name="Places Search",
                    description="Access places search capabilities via Serper.dev",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            try:
                if uri == "web://search":
                    return json.dumps({
                        "resource": "search",
                        "description": "Web search functionality via Serper.dev Google Search API",
                        "available_operations": ["web_search", "get_webpage_content"],
                        "api_provider": "Serper.dev",
                        "search_engine": "Google",
                        "status": "active" if self.serper_api_key else "inactive - API key required"
                    })
                
                elif uri == "web://news":
                    return json.dumps({
                        "resource": "news",
                        "description": "News search functionality via Serper.dev",
                        "available_operations": ["search_news"],
                        "api_provider": "Serper.dev",
                        "search_engine": "Google News",
                        "status": "active" if self.serper_api_key else "inactive - API key required"
                    })
                
                elif uri == "web://images":
                    return json.dumps({
                        "resource": "images",
                        "description": "Image search functionality via Serper.dev",
                        "available_operations": ["search_images"],
                        "api_provider": "Serper.dev",
                        "search_engine": "Google Images",
                        "status": "active" if self.serper_api_key else "inactive - API key required"
                    })
                
                elif uri == "web://videos":
                    return json.dumps({
                        "resource": "videos",
                        "description": "Video search functionality via Serper.dev",
                        "available_operations": ["search_videos"],
                        "api_provider": "Serper.dev",
                        "search_engine": "Google Videos",
                        "status": "active" if self.serper_api_key else "inactive - API key required"
                    })
                
                elif uri == "web://places":
                    return json.dumps({
                        "resource": "places",
                        "description": "Places search functionality via Serper.dev",
                        "available_operations": ["search_places"],
                        "api_provider": "Serper.dev",
                        "search_engine": "Google Places",
                        "status": "active" if self.serper_api_key else "inactive - API key required"
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
                    server_name="web-search-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )

async def main():
    server = WebSearchMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())