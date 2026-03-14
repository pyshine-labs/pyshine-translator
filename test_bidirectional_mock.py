#!/usr/bin/env python3
"""
Test bidirectional translation with mocked detection and translation.
"""
import sys
import os
import tempfile
import logging
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(__file__))

from src.config_manager import ConfigManager
from src.translator import TranslationService

def test_bidirectional_mock():
    """Test bidirectional translation with mocked detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(config_dir=tmpdir)
        cm.set("source_language", "en")
        cm.set("target_language", "zh-CN")
        cm.set("bidirectional", True)
        
        # Mock googletrans module
        mock_translator = Mock()
        # Mock detection results
        mock_translator.detect.side_effect = lambda text: Mock(lang='en' if text == "Hello world" else 'zh-cn' if text == "你好" else 'es')
        # Mock translation result
        mock_translator.translate.return_value = Mock(
            text="TRANSLATED_TEXT",
            src='en',
            dest='zh-cn'
        )
        
        # Patch the translator creation
        with patch('src.translator.GoogleTransTranslator', return_value=mock_translator):
            service = TranslationService(cm)
            
            # Override detection method to use our mock detection
            def mock_detect(text):
                if text == "Hello world":
                    return 'en'
                elif text == "你好":
                    return 'zh-cn'
                else:
                    return 'es'
            service.detect_language = mock_detect
            
            # Capture logs
            import io
            import contextlib
            log_capture = io.StringIO()
            handler = logging.StreamHandler(log_capture)
            handler.setLevel(logging.INFO)
            logger = logging.getLogger('src.translator')
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
            # Test English -> Chinese
            print("Testing English -> Chinese...")
            result = service.translate("Hello world")
            print(f"  Result target language: {result.target_language}")
            # Expect target language to be zh-CN (since detected source matches source)
            assert result.target_language.lower() in ('zh-cn', 'zh-cn'), f"Expected zh-cn got {result.target_language}"
            print("  OK")
            
            # Test Chinese -> English
            print("Testing Chinese -> English...")
            result2 = service.translate("你好")
            print(f"  Result target language: {result2.target_language}")
            # Expect target language to be en (since detected Chinese matches target)
            assert result2.target_language.lower() == 'en', f"Expected en got {result2.target_language}"
            print("  OK")
            
            # Test other language (Spanish) -> default target (Chinese)
            print("Testing Spanish -> default target...")
            result3 = service.translate("Hola")
            print(f"  Result target language: {result3.target_language}")
            # Expect target language to be zh-CN (since detected language doesn't match source or target)
            assert result3.target_language.lower() in ('zh-cn', 'zh-cn'), f"Expected zh-cn got {result3.target_language}"
            print("  OK")
            
            # Print captured logs
            print("\n--- Logs ---")
            print(log_capture.getvalue())
            
            print("All bidirectional mock tests passed.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    try:
        test_bidirectional_mock()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)