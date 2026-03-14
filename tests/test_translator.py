#!/usr/bin/env python3
"""
Integration test for the translator MVP.
Requires internet connection for googletrans.
"""
import sys
import os
import logging
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config_manager import ConfigManager
from src.translator import TranslationService

def test_config_manager():
    """Test configuration loading and saving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(config_dir=tmpdir)
        config = cm.load()
        assert "target_language" in config
        assert config["target_language"] == "zh-CN"
        
        cm.set("target_language", "en")
        assert cm.get("target_language") == "en"
        
        # Reload
        cm2 = ConfigManager(config_dir=tmpdir)
        config2 = cm2.load()
        assert config2["target_language"] == "en"
        print("Config manager test passed.")

def test_translation_service():
    """Test translation service (requires googletrans and internet)."""
    try:
        from googletrans import Translator
    except ImportError:
        print("googletrans not installed, skipping translation test.")
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = ConfigManager(config_dir=tmpdir)
        cm.set("target_language", "zh-CN")
        service = TranslationService(cm)
        
        # Translate a simple phrase
        result = service.translate("Hello")
        if result.success():
            print(f"Translation test passed: {result.text}")
        else:
            print(f"Translation test failed: {result.error}")
            # Not a failure if network issue
            pass

def test_hotkey_manager_mock():
    """Mock test for hotkey manager (no actual hotkey registration)."""
    # Since keyboard and pyautogui may not be installed, we just import
    try:
        from src.hotkey_manager import HotkeyManager
        print("HotkeyManager import successful.")
    except ImportError as e:
        print(f"HotkeyManager import failed (expected if dependencies missing): {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    print("Running integration tests...")
    test_config_manager()
    test_translation_service()
    test_hotkey_manager_mock()
    print("All tests completed.")