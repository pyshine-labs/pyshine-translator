#!/usr/bin/env python3
"""
Test bidirectional translation with mocked detection and translation.
"""
import sys
import os
import tempfile
import logging
from unittest.mock import Mock, patch, MagicMock

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
        
        # Create a mock translator that records calls and returns appropriate results
        mock_translator = MagicMock()
        # Map from text to detected language
        detection_map = {
            "Hello world": 'en',
            "你好": 'zh-cn',
            "Hola": 'es'
        }
        def detect_side_effect(text):
            lang = detection_map.get(text, 'en')
            # Return a detection object with lang attribute
            det = Mock()
            det.lang = lang
            return det
        mock_translator.detect.side_effect = detect_side_effect
        
        # Translate side effect: return result with dest as provided, src as detected language
        def translate_side_effect(text, dest):
            # Determine source language based on detection map (normalize)
            src = detection_map.get(text, 'en')
            # Ensure src matches dest? Not needed.
            result = Mock()
            result.text = f"TRANSLATED({src}->{dest})"
            result.src = src
            result.dest = dest
            return result
        mock_translator.translate.side_effect = translate_side_effect
        
        # Patch the translator creation
        with patch('src.translator.GoogleTransTranslator', return_value=mock_translator):
            # Ensure GOOGLETRANS_AVAILABLE is True
            with patch('src.translator.GOOGLETRANS_AVAILABLE', True):
                service = TranslationService(cm)
                
                # Override detect_language to use detection_map (optional)
                # but we already mocked translator.detect, which is used by detect_language
                # So detection will work.
                
                # Capture logs
                import io
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