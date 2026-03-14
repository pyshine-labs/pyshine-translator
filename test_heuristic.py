#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from src.translator import TranslationService
from src.config_manager import ConfigManager
import logging
logging.basicConfig(level=logging.WARNING)

config = ConfigManager()
service = TranslationService(config)
# Temporarily disable googletrans by mocking GOOGLETRANS_AVAILABLE
import src.translator as trans_module
orig = trans_module.GOOGLETRANS_AVAILABLE
trans_module.GOOGLETRANS_AVAILABLE = False

try:
    # Test heuristic detection
    texts = [
        ("Hello", "en"),
        ("你好", "zh-CN"),
        ("Hello 你好", "zh-CN"),  # contains Chinese characters
        ("Test with no Chinese", "en"),
        ("中", "zh-CN"),
    ]
    for text, expected in texts:
        detected = service.detect_language(text)
        print(f"{repr(text):30} -> {detected} (expected {expected}) {'OK' if detected == expected else 'FAIL'}")
finally:
    trans_module.GOOGLETRANS_AVAILABLE = orig