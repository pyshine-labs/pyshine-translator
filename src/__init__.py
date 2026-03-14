"""
PyShine Translator - A desktop translator with AI support.

A system tray application that translates selected text using a global hotkey.
Supports Google Translate and AI providers (OpenAI, Ollama, custom).
"""

__version__ = "1.3.0"
__author__ = "PyShine"
__email__ = "python2ai@gmail.com"
__description__ = "Desktop translator with AI support - translate selected text with a hotkey"
__url__ = "https://github.com/pyshine-labs/pyshine-translator"

from .config_manager import ConfigManager
from .translator import TranslationService, TranslationResult
from .ai_translator import AITranslator, AIProvider

__all__ = [
    "ConfigManager",
    "TranslationService", 
    "TranslationResult",
    "AITranslator",
    "AIProvider",
    "__version__",
]
