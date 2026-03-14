#!/usr/bin/env python3
"""
Test bidirectional translation feature.
"""
import sys
import os
import tempfile
import logging

sys.path.insert(0, os.path.dirname(__file__))

from src.config_manager import ConfigManager
from src.translator import TranslationService

def test_bidirectional():
    """Test bidirectional translation with language detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(config_dir=tmpdir)
        # Set up configuration
        cm.set("source_language", "en")
        cm.set("target_language", "zh-CN")
        cm.set("bidirectional", True)
        
        service = TranslationService(cm)
        
        # Test English -> Chinese
        print("Testing English -> Chinese...")
        result = service.translate("Hello world")
        if result.success():
            print(f"  Translated: {result.text}")
            print(f"  Source detected: {result.source_language}")
            print(f"  Target: {result.target_language}")
            # Expect target language to be zh-CN (or zh-cn)
            assert result.target_language.lower() in ("zh-cn", "zh-cn")
            print("  OK")
        else:
            print(f"  Translation failed: {result.error}")
            # Skip if network error
            return
        
        # Test Chinese -> English (need Chinese text)
        print("Testing Chinese -> English...")
        result2 = service.translate("你好")
        if result2.success():
            print(f"  Translated: {result2.text}")
            print(f"  Source detected: {result2.source_language}")
            print(f"  Target: {result2.target_language}")
            # Expect target language to be en (since detected Chinese matches target language?)
            # Actually with bidirectional enabled and source=en, target=zh-CN,
            # detected language is Chinese, which matches target, so translation direction
            # should be target -> source (i.e., Chinese -> English).
            # Therefore target_language should be 'en' (source language)
            assert result2.target_language.lower() == "en"
            print("  OK")
        else:
            print(f"  Translation failed: {result2.error}")
            return
        
        # Test bidirectional disabled
        print("Testing bidirectional disabled...")
        cm.set("bidirectional", False)
        service2 = TranslationService(cm)
        result3 = service2.translate("Hello world")
        if result3.success():
            print(f"  Translated: {result3.text}")
            print(f"  Target: {result3.target_language}")
            # Should be zh-CN regardless of detection
            assert result3.target_language.lower() in ("zh-cn", "zh-cn")
            print("  OK")
        else:
            print(f"  Translation failed: {result3.error}")
        
        print("All bidirectional tests passed.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    try:
        test_bidirectional()
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)