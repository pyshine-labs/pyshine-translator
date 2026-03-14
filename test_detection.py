#!/usr/bin/env python3
"""Test language detection accuracy."""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'src')

from googletrans import Translator

def test_detection():
    translator = Translator()
    samples = [
        ("Hello world", "en"),
        ("This is a test", "en"),
        ("How are you?", "en"),
        ("你好世界", "zh-CN"),
        ("这是一个测试", "zh-CN"),
        ("你吃了吗？", "zh-CN"),
        ("Short", "en"),
        ("A", "en"),
        ("中", "zh-CN"),
        ("Hello 你好", "en"),  # mixed, expect maybe Chinese or English
    ]
    for text, expected in samples:
        try:
            detection = translator.detect(text)
            lang = detection.lang
            confidence = detection.confidence
            print(f"Text: {repr(text):20} Expected: {expected:8} Detected: {lang:8} Confidence: {confidence:.2f} {'✓' if lang == expected else '✗'}")
        except Exception as e:
            print(f"Error: {text} -> {e}")

if __name__ == "__main__":
    test_detection()