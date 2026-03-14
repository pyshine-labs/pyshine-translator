#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager
from src.translator import TranslationService
import logging

logging.basicConfig(level=logging.INFO)

config = ConfigManager()
service = TranslationService(config)

texts = [
    ("Hello", "English"),
    ("你好", "Chinese"),
    ("Hola", "Spanish"),
    ("Bonjour", "French"),
]

for text, lang_name in texts:
    print(f"Testing '{text}' ({lang_name}):")
    detected = service.detect_language(text)
    print(f"  Detected: {detected}")
    # Also test translation with bidirectional
    result = service.translate(text)
    print(f"  Translation success: {result.success()}")
    if result.success():
        print(f"  Translated text: {result.text}")
        print(f"  Source language: {result.source_language}")
        print(f"  Target language: {result.target_language}")
    else:
        print(f"  Error: {result.error}")
    print()