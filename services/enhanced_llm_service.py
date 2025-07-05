"""
Enhanced LLM Service with improved token limits and better error handling
"""
import os
import json
import requests
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
from config.settings import Config
from services.mcp_service import MCPService

class EnhancedLLMService:
    """Enhanced LLM Service with MCP tool calling capabilities and higher token limits"""
    
    def __init__(self):
        self.llm_server_url = Config.LLM_SERVER_URL
        self.llm_model_path = Config.LLM_MODEL_PATH
        self.openai_api_key = Config.OPENAI_API_KEY
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.mcp_service = MCPService()

    def generate_response_with_tools(self, user_message: str, context: str = "", user_id: int = None, session_id: str = None, max_tokens: int = 50000) -> str:
        """Generate response with MCP tool calling capabilities"""
        try:
            # First, determine if the user message requires tool usage
            tool_analysis = self._analyze_tool_requirements(user_message)
            
            if tool_analysis['requires_tools']:
                # Execute required tools
                tool_results = self._execute_tools(tool_analysis['tools'], user_message, user_id, session_id)
                
                # Enhance context with tool results
                enhanced_context = self._build_enhanced_context(context, tool_results)
                
                # Generate response with enhanced context
                return self.generate_response(user_message, enhanced_context, max_tokens=max_tokens)
            else:
                # Generate normal response
                return self.generate_response(user_message, context, max_tokens=max_tokens)
                
        except Exception as e:
            print(f"[Enhanced LLM Error] {e}")
            return self.generate_response(user_message, context, max_tokens=max_tokens)

    def _analyze_tool_requirements(self, user_message: str) -> dict:
        """Analyze if the user message requires tool usage"""
        message_lower = user_message.lower()
        
        required_tools = []
        
        # Image generation keywords
        if any(keyword in message_lower for keyword in ['generate image', 'create image', 'draw', 'picture of', 'image of', 'make an image']):
            required_tools.append({
                'type': 'image_generation',
                'server': 'image',
                'tool': 'generate_image'
            })
        
        # Web search keywords
        if any(keyword in message_lower for keyword in ['search for', 'find information', 'what is happening', 'latest news', 'current events', 'search web', 'google']):
            required_tools.append({
                'type': 'web_search',
                'server': 'web_search',
                'tool': 'web_search'
            })
        
        # Document search (if context suggests uploaded documents)
        if any(keyword in message_lower for keyword in ['in the document', 'from the file', 'according to the document', 'document says']):
            required_tools.append({
                'type': 'document_search',
                'server': 'vector',
                'tool': 'search_documents'
            })
        
        return {
            'requires_tools': len(required_tools) > 0,
            'tools': required_tools
        }

    def _execute_tools(self, tools: list, user_message: str, user_id: int = None, session_id: str = None) -> dict:
        """Execute the required tools"""
        results = {}
        
        for tool in tools:
            try:
                if tool['type'] == 'image_generation':
                    # Extract prompt from user message
                    prompt = self._extract_image_prompt(user_message)
                    result = self.mcp_service.generate_image(prompt)
                    results['image_generation'] = result
                
                elif tool['type'] == 'web_search':
                    # Extract search query from user message
                    query = self._extract_search_query(user_message)
                    result = self.mcp_service.web_search(query, num_results=5)
                    results['web_search'] = result
                
                elif tool['type'] == 'document_search' and session_id:
                    # Search in uploaded documents
                    result = self.mcp_service.search_documents(session_id, user_message, top_k=5)
                    results['document_search'] = result
                    
            except Exception as e:
                print(f"[Tool Execution Error] {tool['type']}: {e}")
                results[tool['type']] = {'success': False, 'error': str(e)}
        
        return results

    def _extract_image_prompt(self, user_message: str) -> str:
        """Extract image generation prompt from user message"""
        message_lower = user_message.lower()
        
        # Remove common prefixes
        for prefix in ['generate image of', 'create image of', 'draw', 'picture of', 'image of', 'generate', 'make an image of']:
            if prefix in message_lower:
                start_idx = message_lower.find(prefix) + len(prefix)
                return user_message[start_idx:].strip()
        
        return user_message

    def _extract_search_query(self, user_message: str) -> str:
        """Extract search query from user message"""
        message_lower = user_message.lower()
        
        # Remove common prefixes
        for prefix in ['search for', 'find information about', 'what is', 'tell me about', 'search web for', 'google']:
            if prefix in message_lower:
                start_idx = message_lower.find(prefix) + len(prefix)
                return user_message[start_idx:].strip()
        
        return user_message

    def _build_enhanced_context(self, original_context: str, tool_results: dict) -> str:
        """Build enhanced context with tool results"""
        enhanced_context = original_context
        
        if 'web_search' in tool_results and tool_results['web_search']['success']:
            search_data = tool_results['web_search']['results']
            enhanced_context += f"\n\nWeb Search Results:\n{json.dumps(search_data, indent=2)}"
        
        if 'document_search' in tool_results and tool_results['document_search']['success']:
            doc_data = tool_results['document_search']['documents']
            enhanced_context += f"\n\nRelevant Documents:\n{json.dumps(doc_data, indent=2)}"
        
        if 'image_generation' in tool_results and tool_results['image_generation']['success']:
            img_data = tool_results['image_generation']['result']
            enhanced_context += f"\n\nImage Generation Result:\n{json.dumps(img_data, indent=2)}"
        
        return enhanced_context

    def generate_response(self, user_message: str, context: str = "", image_url: str = None, max_tokens: int = 50000, temperature: float = 0.1) -> str:
        """Generate response using local LLM or OpenAI as fallback with higher token limits"""
        try:
            local_response = self._call_local_llm(user_message, context, image_url, max_tokens, temperature)
            if local_response:
                return local_response
        except Exception as e:
            print(f"[Local LLM Error] {e}")

        try:
            if not self.openai_client:
                raise ValueError("OpenAI client is not initialized")
            # Use a reasonable token limit for OpenAI (they have limits)
            openai_max_tokens = min(max_tokens, 4000)
            return self._call_openai_gpt4o(user_message, context, image_url, openai_max_tokens, temperature)
        except Exception as e:
            print(f"[OpenAI GPT-4o Error] {e}")

        return "I'm sorry, I'm currently unable to process your request. Please try again later."

    def generate_streaming_response(self, user_message: str, context: str = "", max_tokens: int = 50000, temperature: float = 0.1):
        """Generate streaming response - yields chunks of text"""
        try:
            # Try local LLM streaming first
            for chunk in self._call_local_llm_streaming(user_message, context, max_tokens, temperature):
                yield chunk
            return
        except Exception as e:
            print(f"[Local LLM Streaming Error] {e}")

        try:
            # Fallback to OpenAI streaming
            if self.openai_client:
                openai_max_tokens = min(max_tokens, 4000)
                for chunk in self._call_openai_streaming(user_message, context, openai_max_tokens, temperature):
                    yield chunk
                return
        except Exception as e:
            print(f"[OpenAI Streaming Error] {e}")

        # Fallback to non-streaming response
        response = self.generate_response(user_message, context, None, max_tokens, temperature)
        # Simulate streaming by yielding words
        words = response.split()
        for word in words:
            yield word + " "

    def _call_local_llm_streaming(self, user_message: str, context: str = "", max_tokens: int = 50000, temperature: float = 0.1):
        """Call local LLM server with streaming and higher token limits"""
        system_prompt = self._get_system_prompt()
        message_content = self._format_message_with_context(user_message, context)

        payload = {
            "model": self.llm_model_path,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_content}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }

        response = requests.post(
            self.llm_server_url, 
            json=payload, 
            timeout=120,  # Increased timeout for longer responses
            stream=True
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk_data = json.loads(data)
                            if 'choices' in chunk_data and chunk_data['choices']:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        else:
            raise Exception(f"HTTP {response.status_code} - {response.text}")

    def _call_openai_streaming(self, user_message: str, context: str = "", max_tokens: int = 4000, temperature: float = 0.1):
        """Call OpenAI with streaming"""
        system_prompt = self._get_system_prompt()
        message_content = self._format_message_with_context(user_message, context)

        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=system_prompt),
            ChatCompletionUserMessageParam(role="user", content=message_content)
        ]

        stream = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def _call_local_llm(self, user_message: str, context: str = "", image_url: str = None, max_tokens: int = 50000, temperature: float = 0.1):
        """Call local LLM server with higher token limits"""
        system_prompt = self._get_system_prompt()

        if image_url:
            message_content = [
                {"type": "text", "text": self._format_message_with_context(user_message, context)},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        else:
            message_content = self._format_message_with_context(user_message, context)

        payload = {
            "model": self.llm_model_path,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_content}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response = requests.post(self.llm_server_url, json=payload, timeout=120)
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        print(f"[Local LLM] HTTP {response.status_code} - {response.text}")
        return None

    def _call_openai_gpt4o(self, user_message: str, context: str = "", image_url: str = None, max_tokens: int = 4000, temperature: float = 0.1):
        """Call OpenAI GPT-4o"""
        system_prompt = self._get_system_prompt()

        messages: list[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(role="system", content=system_prompt)
        ]

        if image_url:
            messages.append(ChatCompletionUserMessageParam(
                role="user",
                content=[
                    {"type": "text", "text": self._format_message_with_context(user_message, context)},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            ))
        else:
            messages.append(ChatCompletionUserMessageParam(
                role="user",
                content=self._format_message_with_context(user_message, context)
            ))

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()

    def _get_system_prompt(self) -> str:
        """Get enhanced system prompt for LLM"""
        return (
            "You are an advanced AI assistant with access to various tools and capabilities. "
            "You can help with chat conversations, generate images, search the web, and analyze documents. "
            "When users request specific actions like image generation or web searches, "
            "the system will automatically use the appropriate tools and provide you with the results. "
            "Use the provided context and tool results to give comprehensive and helpful responses. "
            "If tool results are included in the context, incorporate them naturally into your response. "
            "Always be helpful, accurate, and provide detailed responses when appropriate. "
            "If you don't have enough information, clearly state what you need or suggest alternatives."
        )

    def _format_message_with_context(self, user_message: str, context: str = "") -> str:
        """Format message with context"""
        return f"Context:\n{context}\n\nUser Question: {user_message}" if context.strip() else user_message

    def get_mcp_status(self) -> dict:
        """Get MCP service status"""
        return self.mcp_service.get_server_status()

    def list_available_tools(self) -> dict:
        """List all available MCP tools"""
        return self.mcp_service.list_available_tools()