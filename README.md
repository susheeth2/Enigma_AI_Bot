# Enigma AI Bot with MCP Integration & Serper.dev Web Search

A sophisticated AI chatbot application built with Flask, featuring Model Context Protocol (MCP) integration and real-time web search capabilities powered by Serper.dev.

## Features

### Core Functionality
- **Multi-modal Chat Interface**: Text-based conversations with streaming responses
- **Image Generation**: AI-powered image creation from text prompts
- **Document Processing**: Upload and analyze DOCX files with vector search
- **Real-time Web Search**: Powered by Serper.dev Google Search API
- **User Authentication**: Secure login and registration system
- **Session Management**: Persistent chat sessions with history

### MCP Integration
- **Model Context Protocol**: Standardized integration with external tools and services
- **Modular Architecture**: Separate MCP servers for different functionalities
- **Tool Calling**: Dynamic tool discovery and execution
- **Resource Management**: Structured access to external data sources

### Web Search Capabilities (Serper.dev)
- **Web Search**: General Google search results
- **News Search**: Recent news articles with time filtering
- **Image Search**: Google Images with safe search options
- **Video Search**: Video content from various platforms
- **Places Search**: Local businesses and location data
- **Webpage Content**: Extract and analyze webpage content

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
  - `web_search_server.py`: Web search functionality with Serper.dev

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

# Search API - Serper.dev (Required for web search)
SERPER_API_KEY=your_serper_api_key

# Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=true
```

4. **Get Serper.dev API Key**
   - Visit [Serper.dev](https://serper.dev)
   - Sign up for an account
   - Get your API key from the dashboard
   - Add it to your `.env` file as `SERPER_API_KEY`

5. **Initialize the database**
```bash
mysql -u root -p < database_setup.sql
```

6. **Download NLTK data**
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
python mcp_startup.py start --server web_search

# Restart all servers
python mcp_startup.py restart
```

### API Endpoints

#### Enhanced Endpoints (with MCP & Serper.dev)
- `POST /enhanced/send_message` - Send chat message with tool calling
- `POST /enhanced/upload_file` - Upload file with MCP processing
- `POST /enhanced/generate_image` - Generate image using MCP
- `POST /enhanced/web_search` - Web search using Serper.dev
- `POST /enhanced/search_news` - News search using Serper.dev
- `POST /enhanced/search_images` - Image search using Serper.dev
- `POST /enhanced/search_videos` - Video search using Serper.dev
- `POST /enhanced/search_places` - Places search using Serper.dev
- `POST /enhanced/get_webpage_content` - Extract webpage content

#### MCP Management
- `GET /mcp/status` - Get MCP server status
- `GET /mcp/tools` - List available tools
- `POST /mcp/test_tool` - Test MCP tools
- `GET /mcp/health` - Health check

#### Traditional Endpoints (Fallback)
- `POST /send_message` - Basic chat functionality
- `POST /upload_file` - File upload
- `POST /generate` - Image generation
- `GET /chat` - Chat interface

## Web Search Integration

### Serper.dev Features

The application integrates with Serper.dev to provide comprehensive web search capabilities:

1. **Web Search**: General Google search results with organic results, knowledge graphs, and answer boxes
2. **News Search**: Recent news articles with time filtering (hour, day, week, month, year)
3. **Image Search**: Google Images with safe search and filtering options
4. **Video Search**: Video content from various platforms
5. **Places Search**: Local businesses and location-based results
6. **Webpage Content**: Extract and analyze content from any webpage

### Search Parameters

- **Query**: Search terms
- **Number of Results**: 1-100 results per search
- **Country/Location**: Localized results
- **Language**: Search in specific languages
- **Time Range**: For news searches (recent, day, week, month, year)
- **Safe Search**: Enable/disable safe search for images

### Example Usage

```javascript
// Web search
fetch('/enhanced/web_search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: 'artificial intelligence trends 2024',
        num_results: 10,
        search_type: 'web'
    })
});

// News search
fetch('/enhanced/search_news', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        query: 'AI breakthrough',
        num_results: 5,
        time_range: 'qdr:d'  // Last day
    })
});
```

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
4. **Search Tools**: Web search, news, images, videos, places

### Client Integration
The MCP client provides:
- Automatic server discovery
- Tool execution
- Resource access
- Error handling and fallbacks

## Development

### Adding New Search Features

1. **Add new tool to web_search_server.py**:
```python
Tool(
    name="search_scholarly",
    description="Search academic papers and scholarly articles",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Academic search query"},
            "year_range": {"type": "string", "description": "Publication year range"}
        },
        "required": ["query"]
    }
)
```

2. **Implement the search method**:
```python
async def _search_scholarly(self, query: str, year_range: str = None) -> Dict[str, Any]:
    # Implementation using Serper.dev or other academic search APIs
    pass
```

3. **Add to MCP service** and **create API endpoint**.

### Project Structure
```
├── app.py                 # Main application
├── mcp/                   # MCP integration
│   ├── servers/          # MCP servers
│   │   └── web_search_server.py  # Serper.dev integration
│   └── client.py         # MCP client
├── services/             # Core services
│   ├── enhanced_*        # MCP-enhanced services
│   └── mcp_service.py    # MCP service wrapper
├── routes/               # Flask routes
│   └── enhanced_api_routes.py  # Enhanced API with search
├── utils/                # Utilities
├── static/               # Frontend assets
└── templates/            # HTML templates
```

## Troubleshooting

### Serper.dev API Issues
1. **Check API key**: Ensure `SERPER_API_KEY` is set correctly
2. **Rate limits**: Serper.dev has rate limits - check your usage
3. **API status**: Check Serper.dev status page for service issues
4. **Request format**: Ensure requests match API specifications

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

## API Rate Limits

### Serper.dev Limits
- **Free Plan**: 2,500 searches/month
- **Pro Plan**: 10,000 searches/month
- **Business Plan**: 100,000 searches/month

Monitor your usage through the Serper.dev dashboard.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues related to:
- **Serper.dev API**: Check [Serper.dev documentation](https://serper.dev/docs)
- **MCP Integration**: See MCP documentation
- **Application Issues**: Create an issue in this repository