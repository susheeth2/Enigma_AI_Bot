# Enigma AI Bot with MCP Integration

A sophisticated AI chatbot application built with Flask, featuring Model Context Protocol (MCP) integration for enhanced tool calling and external service integration.

## Features

### Core Functionality
- **Multi-modal Chat Interface**: Text-based conversations with streaming responses
- **Image Generation**: AI-powered image creation from text prompts
- **Document Processing**: Upload and analyze DOCX files with vector search
- **Web Search**: Search the web for real-time information (placeholder implementation)
- **User Authentication**: Secure login and registration system
- **Session Management**: Persistent chat sessions with history

### MCP Integration
- **Model Context Protocol**: Standardized integration with external tools and services
- **Modular Architecture**: Separate MCP servers for different functionalities
- **Tool Calling**: Dynamic tool discovery and execution
- **Resource Management**: Structured access to external data sources

## Architecture

### Traditional Services
- `ChatService`: Core chat functionality
- `FileService`: File upload and processing
- `ImageService`: Image generation
- `LLMService`: Language model interactions

### MCP Components
- **MCP Servers**:
  - `database_server.py`: Database operations
  - `vector_server.py`: Vector store operations
  - `image_server.py`: Image generation and processing
  - `web_search_server.py`: Web search functionality

- **MCP Client**: Unified interface for server communication
- **Enhanced Services**: MCP-integrated versions of core services

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd enigma-ai-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file with:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=enigma_ai_bot

# LLM Configuration
LLM_SERVER_URL=http://localhost:8000/v1/chat/completions
LLM_MODEL_PATH=/path/to/your/model
OPENAI_API_KEY=your_openai_key

# Image Generation
GRADIO_CLIENT_URL=your_gradio_url

# Vector Store
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Search API (optional)
SEARCH_API_KEY=your_search_api_key
```

4. **Initialize the database**
```bash
mysql -u root -p < database_setup.sql
```

5. **Download NLTK data**
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

## Usage

### Starting the Application

#### Option 1: With MCP Integration (Recommended)
```bash
python app.py
```
This automatically starts MCP servers and the Flask application.

#### Option 2: Manual MCP Management
```bash
# Start MCP servers
python mcp_startup.py start

# Start Flask application
python app.py

# Stop MCP servers when done
python mcp_startup.py stop
```

### MCP Server Management

```bash
# Check server status
python mcp_startup.py status

# Start specific server
python mcp_startup.py start --server database

# Restart all servers
python mcp_startup.py restart
```

### API Endpoints

#### Enhanced Endpoints (with MCP)
- `POST /enhanced/send_message` - Send chat message with tool calling
- `POST /enhanced/upload_file` - Upload file with MCP processing
- `POST /enhanced/generate_image` - Generate image using MCP
- `POST /enhanced/web_search` - Web search using MCP

#### MCP Management
- `GET /mcp/status` - Get MCP server status
- `GET /mcp/tools` - List available tools
- `POST /mcp/test_tool` - Test MCP tools
- `GET /mcp/health` - Health check

#### Traditional Endpoints
- `POST /send_message` - Basic chat functionality
- `POST /upload_file` - File upload
- `POST /generate` - Image generation
- `GET /chat` - Chat interface

## MCP Integration Details

### Server Architecture
Each MCP server exposes:
- **Tools**: Functions the LLM can call
- **Resources**: Data sources the LLM can access
- **Capabilities**: Server-specific features

### Tool Categories
1. **Database Tools**: Message storage, retrieval, user management
2. **Vector Tools**: Document processing, similarity search
3. **Image Tools**: Generation, analysis, processing
4. **Search Tools**: Web search, content extraction

### Client Integration
The MCP client provides:
- Automatic server discovery
- Tool execution
- Resource access
- Error handling and fallbacks

## Development

### Adding New MCP Tools

1. **Create a new tool in the appropriate server**:
```python
Tool(
    name="your_tool_name",
    description="Tool description",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param"]
    }
)
```

2. **Implement the tool handler**:
```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "your_tool_name":
        # Tool implementation
        result = your_function(arguments["param"])
        return [TextContent(type="text", text=str(result))]
```

3. **Update the enhanced LLM service** to recognize when to use the tool.

### Project Structure
```
├── app.py                 # Main application
├── mcp/                   # MCP integration
│   ├── servers/          # MCP servers
│   └── client.py         # MCP client
├── services/             # Core services
│   ├── enhanced_*        # MCP-enhanced services
│   └── mcp_service.py    # MCP service wrapper
├── routes/               # Flask routes
├── utils/                # Utilities
├── static/               # Frontend assets
└── templates/            # HTML templates
```

## Troubleshooting

### MCP Server Issues
1. Check server status: `python mcp_startup.py status`
2. View server logs in the console output
3. Ensure all dependencies are installed
4. Verify environment variables are set

### Database Connection
1. Ensure MySQL is running
2. Check database credentials in `.env`
3. Verify database exists and tables are created

### Vector Store
1. Ensure Milvus is running on the specified port
2. Check Milvus connection settings
3. Verify embedding model is available

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.