"""
AI-based translation service supporting OpenAI, Ollama, and custom API providers.
"""
import json
import logging
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_URL = "http://localhost:11434"
OPENAI_DEFAULT_URL = "https://api.openai.com/v1"


@dataclass
class AIProvider:
    """Configuration for an AI provider."""
    name: str
    provider_type: str  # openai, ollama, custom
    api_url: str
    api_key: str
    model: str
    model_type: str  # chat, completion
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "api_url": self.api_url,
            "api_key": self.api_key,
            "model": self.model,
            "model_type": self.model_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIProvider':
        return cls(
            name=data.get("name", "Unknown"),
            provider_type=data.get("provider_type", "custom"),
            api_url=data.get("api_url", ""),
            api_key=data.get("api_key", ""),
            model=data.get("model", ""),
            model_type=data.get("model_type", "chat")
        )


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = OLLAMA_DEFAULT_URL):
        self.base_url = base_url.rstrip('/')
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append({
                        "name": model.get("name", ""),
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "details": model.get("details", {})
                    })
                logger.info("Found %d Ollama models", len(models))
                return models
            else:
                logger.warning("Ollama returned status %d", response.status_code)
                return []
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama not running at %s", self.base_url)
            return []
        except requests.exceptions.Timeout:
            logger.warning("Ollama request timed out")
            return []
        except Exception as e:
            logger.error("Failed to list Ollama models: %s", e)
            return []
    
    def is_running(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Optional[str]:
        """Send a chat request to Ollama."""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                logger.error("Ollama chat error: %s", response.text)
                return None
        except Exception as e:
            logger.error("Ollama chat failed: %s", e)
            return None


class OpenAIClient:
    """Client for OpenAI-compatible APIs (OpenAI, custom endpoints)."""
    
    def __init__(self, api_url: str = OPENAI_DEFAULT_URL, api_key: str = ""):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
    
    def chat(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Send a chat request to OpenAI-compatible API."""
        if not self.api_key:
            logger.error("API key required for OpenAI-compatible API")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3
            }
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return None
            else:
                logger.error("OpenAI API error: %s", response.text)
                return None
        except Exception as e:
            logger.error("OpenAI chat failed: %s", e)
            return None
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models from OpenAI-compatible API."""
        if not self.api_key:
            return []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.get(
                f"{self.api_url}/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("data", []):
                    models.append({
                        "name": model.get("id", ""),
                        "owned_by": model.get("owned_by", "")
                    })
                return models
            return []
        except Exception as e:
            logger.error("Failed to list OpenAI models: %s", e)
            return []


class AITranslator:
    """AI-based translator supporting multiple providers."""
    
    TRANSLATION_PROMPT = """You are a professional translator. Translate the following text from {source_lang} to {target_lang}. 
Only provide the translation, no explanations or additional text.

Text to translate:
{text}

Translation:"""
    
    LANGUAGE_NAMES = {
        "en": "English",
        "zh-CN": "Simplified Chinese",
        "zh-TW": "Traditional Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ru": "Russian",
        "pt": "Portuguese",
        "it": "Italian",
        "ar": "Arabic",
        "hi": "Hindi",
        "th": "Thai",
        "vi": "Vietnamese"
    }
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self._client = None
    
    def _get_client(self):
        """Get the appropriate client based on provider type."""
        if self._client is None:
            if self.provider.provider_type == "ollama":
                self._client = OllamaClient(self.provider.api_url or OLLAMA_DEFAULT_URL)
            else:
                self._client = OpenAIClient(
                    self.provider.api_url or OPENAI_DEFAULT_URL,
                    self.provider.api_key
                )
        return self._client
    
    def _get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name."""
        return self.LANGUAGE_NAMES.get(lang_code, lang_code)
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate text using the AI provider."""
        client = self._get_client()
        
        source_name = self._get_language_name(source_lang)
        target_name = self._get_language_name(target_lang)
        
        prompt = self.TRANSLATION_PROMPT.format(
            source_lang=source_name,
            target_lang=target_name,
            text=text
        )
        
        messages = [{"role": "user", "content": prompt}]
        
        if self.provider.provider_type == "ollama":
            return client.chat(self.provider.model, messages)
        else:
            return client.chat(self.provider.model, messages)
    
    def test_connection(self) -> tuple:
        """Test the connection to the AI provider."""
        client = self._get_client()
        
        if self.provider.provider_type == "ollama":
            if client.is_running():
                models = client.list_models()
                if any(m["name"] == self.provider.model or m["name"].startswith(self.provider.model + ":") for m in models):
                    return True, f"Connected to Ollama. Model '{self.provider.model}' available."
                else:
                    return False, f"Ollama running but model '{self.provider.model}' not found."
            else:
                return False, "Cannot connect to Ollama. Make sure it's running."
        else:
            result = client.chat(self.provider.model, [{"role": "user", "content": "Hi"}])
            if result:
                return True, f"Successfully connected to {self.provider.name}."
            else:
                return False, f"Failed to connect to {self.provider.name}. Check API key and URL."


def get_ollama_models(base_url: str = OLLAMA_DEFAULT_URL) -> List[Dict[str, Any]]:
    """Get list of available Ollama models."""
    client = OllamaClient(base_url)
    return client.list_models()


def is_ollama_running(base_url: str = OLLAMA_DEFAULT_URL) -> bool:
    """Check if Ollama is running."""
    client = OllamaClient(base_url)
    return client.is_running()


def get_default_providers() -> List[Dict[str, Any]]:
    """Get list of default/predefined AI providers."""
    return [
        {
            "name": "OpenAI GPT-4",
            "provider_type": "openai",
            "api_url": OPENAI_DEFAULT_URL,
            "api_key": "",
            "model": "gpt-4",
            "model_type": "chat"
        },
        {
            "name": "OpenAI GPT-3.5 Turbo",
            "provider_type": "openai",
            "api_url": OPENAI_DEFAULT_URL,
            "api_key": "",
            "model": "gpt-3.5-turbo",
            "model_type": "chat"
        }
    ]
