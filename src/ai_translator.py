"""
AI-based translation service supporting OpenAI, Ollama, custom API providers, and offline translation.
"""
import json
import logging
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_URL = "http://localhost:11434"
OPENAI_DEFAULT_URL = "https://api.openai.com/v1"

OFFLINE_TRANSLATOR_AVAILABLE = False
try:
    import argostranslate.translate
    import argostranslate.package
    OFFLINE_TRANSLATOR_AVAILABLE = True
except ImportError:
    logger.debug("argostranslate not installed. Install with: pip install argostranslate")


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


class OfflineTranslator:
    """Offline translator using argostranslate (CPU-compatible, no internet required)."""
    
    LANGUAGE_MAP = {
        "en": "English",
        "zh": "Chinese",
        "zh-CN": "Chinese",
        "zh-TW": "Chinese Traditional",
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
        "vi": "Vietnamese",
        "nl": "Dutch",
        "pl": "Polish",
        "tr": "Turkish",
        "id": "Indonesian",
        "ms": "Malay",
        "cs": "Czech",
        "sv": "Swedish",
        "da": "Danish",
        "fi": "Finnish",
        "hu": "Hungarian",
        "ro": "Romanian",
        "uk": "Ukrainian",
        "he": "Hebrew",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
        "ml": "Malayalam"
    }
    
    _installed_languages = None
    _translation_cache = {}
    
    def __init__(self):
        self._ensure_packages_updated()
    
    def _ensure_packages_updated(self):
        """Ensure argostranslate package index is updated."""
        if OFFLINE_TRANSLATOR_AVAILABLE:
            try:
                argostranslate.package.update_package_index()
            except Exception as e:
                logger.debug("Could not update argostranslate package index: %s", e)
    
    def _normalize_lang_code(self, lang_code: str) -> str:
        """Normalize language code for argostranslate."""
        lang_code = lang_code.lower()
        if lang_code.startswith("zh"):
            return "zh"
        return lang_code
    
    def get_installed_languages(self) -> List[Dict[str, Any]]:
        """Get list of installed language pairs for offline translation."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            return []
        
        try:
            if self._installed_languages is None:
                self._installed_languages = argostranslate.translate.get_installed_languages()
            
            languages = []
            seen_pairs = set()
            
            for from_lang in self._installed_languages:
                for to_lang in from_lang.translations:
                    pair_key = f"{from_lang.code}->{to_lang.code}"
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        languages.append({
                            "from": from_lang.code,
                            "from_name": from_lang.name,
                            "to": to_lang.code,
                            "to_name": to_lang.name,
                            "pair": f"{from_lang.name} → {to_lang.name}"
                        })
            
            logger.info("Found %d installed offline translation pairs", len(languages))
            return languages
        except Exception as e:
            logger.error("Failed to get installed languages: %s", e)
            return []
    
    def get_available_packages(self) -> List[Dict[str, Any]]:
        """Get list of available packages that can be installed."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            return []
        
        try:
            available_packages = argostranslate.package.get_available_packages()
            installed_codes = set()
            
            for lang in argostranslate.translate.get_installed_languages():
                installed_codes.add(lang.code)
            
            packages = []
            for pkg in available_packages:
                packages.append({
                    "from": pkg.from_code,
                    "to": pkg.to_code,
                    "from_name": pkg.from_name,
                    "to_name": pkg.to_name,
                    "installed": pkg.from_code in installed_codes and pkg.to_code in installed_codes
                })
            
            return packages
        except Exception as e:
            logger.error("Failed to get available packages: %s", e)
            return []
    
    def install_language_pair(self, from_code: str, to_code: str) -> bool:
        """Install a language pair for offline translation."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            logger.error("argostranslate not available")
            return False
        
        try:
            available_packages = argostranslate.package.get_available_packages()
            
            package_to_install = None
            for pkg in available_packages:
                if pkg.from_code == from_code and pkg.to_code == to_code:
                    package_to_install = pkg
                    break
            
            if package_to_install:
                argostranslate.package.install_from_path(package_to_install.download())
                self._installed_languages = None
                logger.info("Installed offline translation: %s -> %s", from_code, to_code)
                return True
            else:
                logger.warning("Package not found: %s -> %s", from_code, to_code)
                return False
        except Exception as e:
            logger.error("Failed to install language pair: %s", e)
            return False
    
    def is_available(self) -> bool:
        """Check if offline translation is available."""
        return OFFLINE_TRANSLATOR_AVAILABLE
    
    def can_translate(self, source_lang: str, target_lang: str) -> bool:
        """Check if a specific translation pair is available."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            return False
        
        try:
            source = self._normalize_lang_code(source_lang)
            target = self._normalize_lang_code(target_lang)
            
            if self._installed_languages is None:
                self._installed_languages = argostranslate.translate.get_installed_languages()
            
            for from_lang in self._installed_languages:
                if from_lang.code == source:
                    for to_lang in from_lang.translations:
                        if to_lang.code == target:
                            return True
            return False
        except Exception as e:
            logger.error("Error checking translation availability: %s", e)
            return False
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Translate text using offline argostranslate."""
        if not OFFLINE_TRANSLATOR_AVAILABLE:
            logger.error("argostranslate not installed")
            return None
        
        try:
            source = self._normalize_lang_code(source_lang)
            target = self._normalize_lang_code(target_lang)
            
            cache_key = f"{source}->{target}:{text}"
            if cache_key in self._translation_cache:
                return self._translation_cache[cache_key]
            
            if self._installed_languages is None:
                self._installed_languages = argostranslate.translate.get_installed_languages()
            
            from_language = None
            to_language = None
            
            for lang in self._installed_languages:
                if lang.code == source:
                    from_language = lang
                if lang.code == target:
                    to_language = lang
            
            if from_language is None:
                logger.error("Source language not installed: %s", source)
                return None
            
            if to_language is None:
                logger.error("Target language not installed: %s", target)
                return None
            
            translation = from_language.get_translation(to_language)
            if translation is None:
                logger.error("No translation found for %s -> %s", source, target)
                return None
            
            result = translation.translate(text)
            
            if len(self._translation_cache) < 1000:
                self._translation_cache[cache_key] = result
            
            logger.info("Offline translated %d chars from %s to %s", len(text), source, target)
            return result
            
        except Exception as e:
            logger.error("Offline translation failed: %s", e)
            return None


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


_offline_translator_instance = None

def get_offline_translator() -> OfflineTranslator:
    """Get or create the global offline translator instance."""
    global _offline_translator_instance
    if _offline_translator_instance is None:
        _offline_translator_instance = OfflineTranslator()
    return _offline_translator_instance


def is_offline_available() -> bool:
    """Check if offline translation is available."""
    return OFFLINE_TRANSLATOR_AVAILABLE


def get_offline_languages() -> List[Dict[str, Any]]:
    """Get list of installed offline translation language pairs."""
    translator = get_offline_translator()
    return translator.get_installed_languages()


def get_offline_available_packages() -> List[Dict[str, Any]]:
    """Get list of available offline translation packages."""
    translator = get_offline_translator()
    return translator.get_available_packages()


def install_offline_language(from_code: str, to_code: str) -> bool:
    """Install an offline translation language pair."""
    translator = get_offline_translator()
    return translator.install_language_pair(from_code, to_code)
