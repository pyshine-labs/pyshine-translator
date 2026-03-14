#!/usr/bin/env python3
"""Test improved language detection."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager
from src.translator import TranslationService
import logging

logging.basicConfig(level=logging.DEBUG)

def test_detection():
    config = ConfigManager()
    service = TranslationService(config)
    
    test_cases = [
        ("Hello world", "en"),
        ("This is a test", "en"),
        ("你好世界", "zh-CN"),
        ("这是一个测试", "zh-CN"),
        ("Hello 你好", "en"),  # mixed, heuristic may detect Chinese
        ("Short", "en"),
        ("A", "en"),
        ("中", "zh-CN"),
        ("", None),
    ]
    
    for text, expected in test_cases:
        detected = service.detect_language(text)
        match = "PASS" if detected == expected else "FAIL"
        print(f"Text: {repr(text):20} Expected: {expected} Detected: {detected} {match}")
        if detected != expected:
            # check if heuristic fallback worked
            pass

if __name__ == "__main__":
    test_detection()