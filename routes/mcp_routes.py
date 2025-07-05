"""
Routes for MCP management and monitoring
"""
from flask import Blueprint, request, jsonify, session
from services.mcp_service import MCPService

mcp_bp = Blueprint('mcp', __name__)
mcp_service = MCPService()

@mcp_bp.route('/mcp/status')
def mcp_status():
    """Get MCP server status"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        status = mcp_service.get_server_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mcp_bp.route('/mcp/tools')
def list_mcp_tools():
    """List all available MCP tools"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        tools = mcp_service.list_available_tools()
        return jsonify(tools)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mcp_bp.route('/mcp/test_tool', methods=['POST'])
def test_mcp_tool():
    """Test an MCP tool"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        tool_type = data.get('tool_type')
        
        if tool_type == 'web_search':
            query = data.get('query', 'test search')
            result = mcp_service.web_search(query)
            return jsonify(result)
        
        elif tool_type == 'image_generation':
            prompt = data.get('prompt', 'a beautiful sunset')
            result = mcp_service.generate_image(prompt)
            return jsonify(result)
        
        elif tool_type == 'document_search':
            session_id = data.get('session_id', session.get('session_id'))
            query = data.get('query', 'test query')
            result = mcp_service.search_documents(session_id, query)
            return jsonify(result)
        
        else:
            return jsonify({'error': 'Unknown tool type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@mcp_bp.route('/mcp/health')
def mcp_health():
    """Health check for MCP services"""
    try:
        status = mcp_service.get_server_status()
        
        health_status = {
            'overall': 'healthy' if any(status.get('servers', {}).values()) else 'unhealthy',
            'servers': status.get('servers', {}),
            'timestamp': '2024-01-15T10:00:00Z'
        }
        
        return jsonify(health_status)
    except Exception as e:
        return jsonify({
            'overall': 'unhealthy',
            'error': str(e),
            'timestamp': '2024-01-15T10:00:00Z'
        }), 500