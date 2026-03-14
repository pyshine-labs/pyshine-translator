#!/usr/bin/env python3
import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s %(message)s')

from src.config_manager import ConfigManager
from src.translator import TranslationService

config = ConfigManager()
print("Current config:")
print(f"  source_language: {config.get('source_language')}")
print(f"  target_language: {config.get('target_language')}")
print(f"  bidirectional: {config.get('bidirectional')}")
print()

service = TranslationService(config)

texts = [
    ("Hello", "English"),
    ("你好", "Chinese"),
    ("Hola", "Spanish"),
]

for text, lang_name in texts:
    print(f"\n--- Testing '{text}' ({lang_name}) ---")
    detected = service.detect_language(text)
    print(f"Detected language: {detected}")
    # Simulate the logic from translate method to see direction decision
    source_language = config.get("source_language", "en")
    target_language = config.get("target_language", "zh-CN")
    bidirectional = config.get("bidirectional", True)
    
    if bidirectional and detected:
        def normalize(lang):
            return lang.lower().replace('_', '-')
        src_norm = normalize(source_language)
        tgt_norm = normalize(target_language)
        det_norm = normalize(detected)
        
        if det_norm == src_norm:
            final_target = target_language
            direction = "source -> target"
        elif det_norm == tgt_norm:
            final_target = source_language
            direction = "target -> source"
        else:
            final_target = target_language
            direction = "other -> target"
        print(f"Direction: {direction}")
        print(f"Final target language: {final_target}")
    else:
        print(f"Bidirectional disabled or detection failed, target: {target_language}")
    
    # Try translation (may fail due to network)
    result = service.translate(text)
    if result.success():
        print(f"Translation success: {result.text}")
    else:
        print(f"Translation failed: {result.error}")