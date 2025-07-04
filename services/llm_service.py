import os
import requests
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
from config.settings import Config

class LLMService:
    """Service for handling LLM interactions with streaming support"""
    
    def __init__(self):
        self.llm_server_url = Config.LLM_SERVER_URL
        self.llm_model_path = Config.LLM_MODEL_PATH
        self.openai_api_key = Config.OPENAI_API_KEY
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    def generate_response(self, user_message, context="", image_url=None, max_tokens=10000, temperature=0.1):
        """Generate response using local LLM or OpenAI as fallback"""
        try:
            local_response = self._call_local_llm(user_message, context, image_url, max_tokens, temperature)
            if local_response:
                return local_response
        except Exception as e:
            print(f"[Local LLM Error] {e}")

        try:
            if not self.openai_client:
                raise ValueError("OpenAI client is not initialized")
            return self._call_openai_gpt4o(user_message, context, image_url, max_tokens, temperature)
        except Exception as e:
            print(f"[OpenAI GPT-4o Error] {e}")

        return "I'm sorry, I'm currently unable to process your request. Please try again later."

    def generate_streaming_response(self, user_message, context="", max_tokens=10000, temperature=0.1):
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
                for chunk in self._call_openai_streaming(user_message, context, max_tokens, temperature):
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

    def _call_local_llm_streaming(self, user_message, context="", max_tokens=10000, temperature=0.1):
        """Call local LLM server with streaming"""
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
            timeout=60,
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
                            import json
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

    def _call_openai_streaming(self, user_message, context="", max_tokens=1000, temperature=0.1):
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

    def _call_local_llm(self, user_message, context="", image_url=None, max_tokens=10000, temperature=0.1):
        """Call local LLM server"""
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

        response = requests.post(self.llm_server_url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        print(f"[Local LLM] HTTP {response.status_code} - {response.text}")
        return None

    def _call_openai_gpt4o(self, user_message, context="", image_url=None, max_tokens=1000, temperature=0.1):
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

    def _get_system_prompt(self):
        """Get system prompt for LLM"""
        return (
            "You are a helpful assistant. "
            "Answer only based on the document chunks provided in the context. "
            "If the answer is not clearly present in the context, respond with: "
            "\"This information is not found in the uploaded document.\" "
            "Do not use any external knowledge."
        )

    def _format_message_with_context(self, user_message, context=""):
        """Format message with context"""
        return f"Context:\n{context}\n\nUser Question: {user_message}" if context.strip() else user_message