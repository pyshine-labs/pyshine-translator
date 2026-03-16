"""
Translation service using googletrans (free), Google Cloud Translation API, or AI providers.
"""
import logging
import time
import threading
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from googletrans import Translator as GoogleTransTranslator, LANGUAGES
    GOOGLETRANS_AVAILABLE = True
except (ImportError, AttributeError) as e:
    GOOGLETRANS_AVAILABLE = False
    logger.warning("googletrans not available: %s. Google Translate backend disabled.", e)

try:
    from google.cloud import translate_v2 as google_translate
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False

try:
    from langdetect import detect, DetectorFactory
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    from .ai_translator import AITranslator, AIProvider, get_ollama_models, is_ollama_running, get_offline_translator, is_offline_available, install_offline_translator, OFFLINE_BACKEND
    AI_TRANSLATOR_AVAILABLE = True
except ImportError:
    AI_TRANSLATOR_AVAILABLE = False
    logger.warning("AI translator module not available")

@dataclass
class TranslationResult:
    """Result of a translation."""
    text: str
    source_language: str
    target_language: str
    confidence: Optional[float] = None
    error: Optional[str] = None
    backend: str = "google"
    
    def success(self) -> bool:
        return self.error is None

class TranslationService:
    """
    Translation service that uses googletrans (free), Google Cloud Translation API, or AI providers.
    """
    DETECTION_CONFIDENCE_THRESHOLD = 0.5

    def __init__(self, config_manager):
        self.config = config_manager
        self._googletrans_translator = None
        self._cloud_client = None
        self._ai_translator = None
        self._last_request_time = 0
        self._min_request_interval = 0.5
        self._lock = threading.Lock()
        
    def _get_googletrans_translator(self):
        """Lazy initialization of googletrans translator."""
        if self._googletrans_translator is None and GOOGLETRANS_AVAILABLE:
            self._googletrans_translator = GoogleTransTranslator()
        return self._googletrans_translator
    
    def _get_ai_translator(self):
        """Lazy initialization of AI translator based on current config."""
        if not AI_TRANSLATOR_AVAILABLE:
            return None
        
        backend = self.config.get("translation_backend", "ai")
        if backend == "google":
            return None
        
        providers = self.config.get("ai_providers", [])
        current_idx = self.config.get("current_ai_provider")
        
        # If no provider selected but providers exist, use the first one
        if current_idx is None and len(providers) > 0:
            current_idx = 0
        
        if current_idx is not None and 0 <= current_idx < len(providers):
            provider_data = providers[current_idx]
            provider = AIProvider.from_dict(provider_data)
            self._ai_translator = AITranslator(provider)
            return self._ai_translator
        
        return None
    
    def _rate_limit(self):
        """Simple rate limiting to avoid being blocked."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _detect_language_heuristic(self, text: str) -> Optional[str]:
        """
        Detect language based on character set.
        Returns 'zh-CN' if text contains Chinese characters,
        'en' if text is mostly ASCII letters,
        None otherwise.
        """
        import re
        # Chinese Unicode range (CJK Unified Ideographs)
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'zh-CN'
        # ASCII letters with possible punctuation/numbers
        # If the text contains only ASCII characters, assume English
        if all(ord(c) < 128 for c in text):
            return 'en'
        return None
    
    def _detect_with_langdetect(self, text: str) -> Optional[str]:
        """Detect language using langdetect library."""
        if not LANGDETECT_AVAILABLE:
            return None
        try:
            from langdetect import detect
            lang = detect(text)
            # Map langdetect codes to our language codes
            if lang.startswith('zh'):
                return 'zh-CN'
            elif lang.startswith('en'):
                return 'en'
            else:
                return None
        except Exception as e:
            logger.debug("langdetect failed: %s", e)
            return None
    
    def translate(self, text: str, target_language: str = None, source_language: str = None) -> TranslationResult:
        """
        Translate text to target language with optional bidirectional detection.
        
        Args:
            text: Text to translate.
            target_language: Target language code (e.g., 'zh-CN'). If None, uses config.
            source_language: Source language code (e.g., 'en'). If None, uses config.
        
        Returns:
            TranslationResult object.
        """
        with self._lock:
            return self._translate_impl(text, target_language, source_language)
    
    def _translate_impl(self, text: str, target_language: str = None, source_language: str = None) -> TranslationResult:
        """Internal translate implementation (not thread-safe, use translate() instead)."""
        if not text or not text.strip():
            return TranslationResult(
                text="",
                source_language="",
                target_language="",
                error="No text provided"
            )
        
        if target_language is None:
            target_language = self.config.get("target_language", "zh-CN")
        if source_language is None:
            source_language = self.config.get("source_language", "en")
        
        bidirectional = self.config.get("bidirectional", True)
        use_official = self.config.get("use_official_api", False)
        
        # Determine translation direction based on detected language
        detected_lang = None
        if bidirectional:
            detected_lang = self.detect_language(text)
            logger.info("Detected language: %s", detected_lang)
        
        final_target = target_language
        if bidirectional and detected_lang:
            # Normalize language codes for comparison
            def normalize(lang):
                return lang.lower().replace('_', '-')
            src_norm = normalize(source_language)
            tgt_norm = normalize(target_language)
            det_norm = normalize(detected_lang)
            
            if det_norm == src_norm:
                # Text is in source language, translate to target
                final_target = target_language
                logger.info("Detected source language, translating to target: %s", final_target)
            elif det_norm == tgt_norm:
                # Text is in target language, translate back to source
                final_target = source_language
                logger.info("Detected target language, translating back to source: %s", final_target)
            else:
                # Language doesn't match either, default to target
                final_target = target_language
                logger.info("Detected language %s not matching source/target, default to target: %s", detected_lang, final_target)
        else:
            if not bidirectional:
                logger.info("Bidirectional disabled, translating to target: %s", final_target)
            else:
                logger.info("Language detection failed, translating to target: %s", final_target)
        
        self._rate_limit()
        
        backend = self.config.get("translation_backend", "google")
        
        actual_source_lang = detected_lang if (bidirectional and detected_lang) else source_language
        
        if backend == "offline":
            if AI_TRANSLATOR_AVAILABLE:
                if not is_offline_available():
                    logger.info("Offline translation not available, installing...")
                    if install_offline_translator():
                        logger.info("Offline translator installed, please restart the app")
                        return TranslationResult(
                            text="",
                            source_language=actual_source_lang,
                            target_language=final_target,
                            error="Offline translator installed successfully. Please restart the app to use offline translation.",
                            backend="Offline"
                        )
                    else:
                        return TranslationResult(
                            text="",
                            source_language=actual_source_lang,
                            target_language=final_target,
                            error="Failed to install offline translator (SSL/Network error). Try manually: pip install translatepy OR pip install argostranslate",
                            backend="Offline"
                        )
                
                offline_translator = get_offline_translator()
                try:
                    result_text = offline_translator.translate(text, actual_source_lang, final_target)
                    if result_text:
                        logger.info("Offline translated %d chars from %s to %s", len(text), actual_source_lang, final_target)
                        return TranslationResult(
                            text=result_text,
                            source_language=actual_source_lang,
                            target_language=final_target,
                            confidence=None,
                            backend=f"Offline ({OFFLINE_BACKEND})"
                        )
                except Exception as e:
                    logger.exception("Offline translation failed: %s", e)
                    return TranslationResult(
                        text="",
                        source_language=actual_source_lang,
                        target_language=final_target,
                        error=f"Offline translation error: {str(e)}",
                        backend="Offline"
                    )
            
            return TranslationResult(
                text="",
                source_language=actual_source_lang,
                target_language=final_target,
                error="Offline translation error. Try a different backend.",
                backend="Offline"
            )
        
        if backend == "ai":
            ai_translator = self._get_ai_translator()
            logger.info("AI backend=%s, ai_translator=%s", backend, ai_translator)
            if ai_translator:
                try:
                    result_text = ai_translator.translate(text, source_language, final_target)
                    provider_name = ai_translator.provider.name
                    if result_text:
                        logger.info("AI translated %d chars to %s", len(text), final_target)
                        return TranslationResult(
                            text=result_text,
                            source_language=source_language,
                            target_language=final_target,
                            confidence=None,
                            backend=provider_name
                        )
                    else:
                        return TranslationResult(
                            text="",
                            source_language=source_language,
                            target_language=final_target,
                            error="AI translation returned empty result",
                            backend=provider_name
                        )
                except Exception as e:
                    logger.exception("AI translation failed: %s", e)
                    return TranslationResult(
                        text="",
                        source_language=source_language,
                        target_language=final_target,
                        error=f"AI translation error: {str(e)}",
                        backend="ai"
                    )
            else:
                return TranslationResult(
                    text="",
                    source_language=source_language,
                    target_language=final_target,
                    error="AI translator not configured. Add an AI provider in Settings.",
                    backend="ai"
                )
        
        if use_official and GOOGLE_CLOUD_AVAILABLE:
            logger.warning("Google Cloud Translation not fully implemented, falling back to googletrans")
        
        if not GOOGLETRANS_AVAILABLE:
            return TranslationResult(
                text="",
                source_language="",
                target_language=final_target,
                error="No translation backend available. Install googletrans or configure AI provider.",
                backend="none"
            )
        
        translator = self._get_googletrans_translator()
        try:
            target_lang = final_target.lower().replace('_', '-')
            result = translator.translate(text, dest=target_lang)
            logger.info(
                "Translated %d chars from %s to %s",
                len(text),
                result.src,
                result.dest
            )
            return TranslationResult(
                text=result.text,
                source_language=result.src,
                target_language=result.dest,
                confidence=None,
                backend="Google Translate"
            )
        except Exception as e:
            logger.exception("Translation failed: %s", e)
            return TranslationResult(
                text="",
                source_language="",
                target_language=final_target,
                error=str(e),
                backend="Google Translate"
            )
    def detect_language(self, text: str) -> Optional[str]:
        """Detect language of text with fallback strategies."""
        if GOOGLETRANS_AVAILABLE:
            translator = self._get_googletrans_translator()
            try:
                detection = translator.detect(text)
                confidence = getattr(detection, 'confidence', None)
                if confidence is None:
                    confidence = 1.0
                logger.info("googletrans detection: lang=%s, confidence=%.2f", detection.lang, confidence)
                if confidence >= self.DETECTION_CONFIDENCE_THRESHOLD:
                    return detection.lang
                else:
                    logger.warning("googletrans confidence too low (%.2f < %.2f), using fallback", confidence, self.DETECTION_CONFIDENCE_THRESHOLD)
            except Exception as e:
                logger.error("googletrans detection failed: %s", e)
        
        heuristic_lang = self._detect_language_heuristic(text)
        if heuristic_lang:
            logger.info("heuristic detection: %s", heuristic_lang)
            return heuristic_lang
        
        langdetect_lang = self._detect_with_langdetect(text)
        if langdetect_lang:
            logger.info("langdetect detection: %s", langdetect_lang)
            return langdetect_lang
        
        logger.warning("Language detection failed for text: %s", text[:50])
        return None



# Singleton instance for easy import
_service_instance = None

def get_translation_service(config_manager=None):
    """Get or create the global translation service instance."""
    global _service_instance
    if _service_instance is None and config_manager is not None:
        _service_instance = TranslationService(config_manager)
    return _service_instance


if __name__ == "__main__":
    # Quick test
    import sys
    sys.path.insert(0, '.')
    from config_manager import ConfigManager
    
    logging.basicConfig(level=logging.INFO)
    cm = ConfigManager()
    service = TranslationService(cm)
    result = service.translate("Hello world", "zh-CN")
    if result.success():
        print(f"Translated: {result.text}")
        print(f"Source language: {result.source_language}")
    else:
        print(f"Error: {result.error}")