#!/usr/bin/env python3

import requests
import json
import time
import os
from typing import Dict, List, Optional, Any
import logging
from abc import ABC, abstractmethod
import model_validation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass

class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using Ollama"""
        if not self.is_available():
            return "Ollama is not available. Please start Ollama service."
        
        # Build context-aware prompt
        full_prompt = self._build_context_prompt(prompt, context)
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', 'No response generated')
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_context_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Build context-aware prompt"""
        if not context:
            return prompt
        
        context_parts = []
        
        # Add conversation summary
        if context.get('summary'):
            context_parts.append(f"Conversation context: {context['summary']}")
        
        # Add emotional state
        if context.get('emotional_state'):
            context_parts.append(f"User emotional state: {context['emotional_state']}")
        
        # Add topics
        if context.get('topics'):
            topics = ', '.join(context['topics'])
            context_parts.append(f"Current topics: {topics}")
        
        # Add recent messages
        if context.get('recent_messages'):
            recent = context['recent_messages'][-3:]  # Last 3 messages
            messages = []
            for msg in recent:
                role = msg.get('role', 'user')
                content = msg.get('content', '')[:100]  # Truncate long messages
                messages.append(f"{role}: {content}")
            if messages:
                context_parts.append(f"Recent conversation:\n" + "\n".join(messages))
        
        # Build final prompt
        if context_parts:
            context_str = "\n".join(context_parts)
            return f"{context_str}\n\nUser: {prompt}\nAssistant:"
        else:
            return f"User: {prompt}\nAssistant:"

    def set_model_name(self, model_name: str) -> str:
        """
        Validate and set the Ollama model name. Auto-corrects to closest match if needed.
        Returns the model actually set.
        """
        is_valid, valid_model, suggestions = model_validation.validate_ollama_model(model_name)
        if is_valid:
            self.model_name = model_name
            logger.info(f"Ollama model set to '{model_name}' (validated)")
            return model_name
        elif valid_model:
            self.model_name = valid_model
            logger.warning(f"Model '{model_name}' not found. Auto-corrected to '{valid_model}'. Suggestions: {suggestions}")
            return valid_model
        else:
            logger.error(f"Model '{model_name}' not found. No valid alternatives. Available: {suggestions}")
            return self.model_name  # Keep previous

class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return bool(self.api_key)
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using Gemini API"""
        if not self.is_available():
            return "Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
        
        # Build context-aware prompt
        full_prompt = self._build_context_prompt(prompt, context)
        
        try:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                    "maxOutputTokens": 500
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and result['candidates']:
                content = result['candidates'][0]['content']
                if 'parts' in content and content['parts']:
                    return content['parts'][0]['text']
            
            return "No response generated"
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_context_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Build context-aware prompt for Gemini"""
        if not context:
            return prompt
        
        context_parts = []
        
        # Add conversation summary
        if context.get('summary'):
            context_parts.append(f"Conversation context: {context['summary']}")
        
        # Add emotional state
        if context.get('emotional_state'):
            context_parts.append(f"User emotional state: {context['emotional_state']}")
        
        # Add topics
        if context.get('topics'):
            topics = ', '.join(context['topics'])
            context_parts.append(f"Current topics: {topics}")
        
        # Add recent messages
        if context.get('recent_messages'):
            recent = context['recent_messages'][-3:]  # Last 3 messages
            messages = []
            for msg in recent:
                role = msg.get('role', 'user')
                content = msg.get('content', '')[:100]  # Truncate long messages
                messages.append(f"{role}: {content}")
            if messages:
                context_parts.append(f"Recent conversation:\n" + "\n".join(messages))
        
        # Build final prompt
        if context_parts:
            context_str = "\n".join(context_parts)
            return f"{context_str}\n\nUser: {prompt}\nAssistant:"
        else:
            return f"User: {prompt}\nAssistant:"

class OpenAIProvider(LLMProvider):
    """OpenAI GPT API provider"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        return bool(self.api_key)
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using OpenAI API"""
        if not self.is_available():
            return "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        
        try:
            # Build messages array
            messages = []
            
            # Add system message with context
            if context:
                system_context = self._build_system_context(context)
                messages.append({"role": "system", "content": system_context})
            
            # Add user message
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": "gpt-3.5-turbo",  # Can be changed to gpt-4
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content']
            
            return "No response generated"
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_system_context(self, context: Dict[str, Any]) -> str:
        """Build system context message"""
        context_parts = []
        
        if context.get('summary'):
            context_parts.append(f"Conversation context: {context['summary']}")
        
        if context.get('emotional_state'):
            context_parts.append(f"User emotional state: {context['emotional_state']}")
        
        if context.get('topics'):
            topics = ', '.join(context['topics'])
            context_parts.append(f"Current topics: {topics}")
        
        if context_parts:
            return "You are a helpful AI assistant. " + " ".join(context_parts)
        else:
            return "You are a helpful AI assistant."

class LLMManager:
    """Manager for multiple LLM providers"""
    
    def __init__(self):
        self.providers = {
            'ollama': OllamaProvider(),
            'gemini': GeminiProvider(),
            'openai': OpenAIProvider()
        }
        self.current_provider = 'ollama'  # Default to Ollama (free)
        
    def set_provider(self, provider_name: str):
        """Set the current LLM provider"""
        if provider_name in self.providers:
            self.current_provider = provider_name
            logger.info(f"Switched to {provider_name} provider")
        else:
            logger.error(f"Provider {provider_name} not found")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        available = []
        for name, provider in self.providers.items():
            if provider.is_available():
                available.append(name)
        return available
    
    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using current provider"""
        provider = self.providers.get(self.current_provider)
        if not provider:
            return "No provider configured"
        
        if not provider.is_available():
            # Try to fallback to Ollama if available
            if self.current_provider != 'ollama' and self.providers['ollama'].is_available():
                logger.warning(f"{self.current_provider} not available, falling back to Ollama")
                self.current_provider = 'ollama'
                provider = self.providers['ollama']
            else:
                return f"{self.current_provider} provider not available"
        
        return provider.generate_response(prompt, context)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider"""
        provider = self.providers.get(self.current_provider)
        if not provider:
            return {"error": "No provider configured"}
        
        return {
            "name": self.current_provider,
            "available": provider.is_available(),
            "type": "local" if self.current_provider == 'ollama' else "api"
        }

    def set_ollama_model(self, model_name: str) -> str:
        """
        Set the Ollama model, with validation and auto-correction.
        Returns the model actually set.
        """
        if 'ollama' in self.providers:
            return self.providers['ollama'].set_model_name(model_name)
        else:
            logger.error("Ollama provider not available.")
            return None

# Global LLM manager instance
llm_manager = LLMManager()

def setup_llm_integration():
    """Setup LLM integration for the conversation system"""
    available = llm_manager.get_available_providers()
    logger.info(f"Available LLM providers: {available}")
    
    if not available:
        logger.warning("No LLM providers available. Install Ollama for free local models.")
        return False
    
    # Prefer Ollama if available (free)
    if 'ollama' in available:
        llm_manager.set_provider('ollama')
        logger.info("Using Ollama for free local LLM")
    else:
        # Use first available provider
        llm_manager.set_provider(available[0])
        logger.info(f"Using {available[0]} provider")
    
    return True

if __name__ == "__main__":
    # Test the LLM integration
    setup_llm_integration()
    
    test_prompt = "Hello! How are you today?"
    test_context = {
        "summary": "User is starting a new conversation",
        "emotional_state": "neutral",
        "topics": ["greeting"]
    }
    
    response = llm_manager.generate_response(test_prompt, test_context)
    print(f"Test response: {response}") 