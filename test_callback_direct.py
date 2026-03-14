#!/usr/bin/env python3
"""
Directly call _on_hotkey_triggered to see if copy works.
"""
import sys
import os
import time
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(__file__))

import pyautogui
import pyperclip
import subprocess

# Mock translation service
class MockTranslationService:
    def translate(self, text):
        from src.translator import TranslationResult
        # Return a successful translation (just echo text)
        return TranslationResult(text=text + " [translated]", source_language="en", target_language="zh-CN")

# Mock config manager
class MockConfigManager:
    def __init__(self):
        self._config = {"enabled": True, "hotkey": "Ctrl+Shift+T"}
    def get(self, key, default=None):
        return self._config.get(key, default)
    def set(self, key, value):
        self._config[key] = value

def open_notepad():
    proc = subprocess.Popen(['notepad.exe'])
    time.sleep(2)
    return proc

def close_notepad(proc):
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.5)
    pyautogui.press('n')
    proc.terminate()
    proc.wait()

def setup_selection():
    proc = open_notepad()
    time.sleep(1)
    test_text = "Hello world direct callback test"
    pyautogui.write(test_text, interval=0.05)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    return proc, test_text

def main():
    # Backup clipboard
    original = pyperclip.paste()
    pyperclip.copy('')
    
    # Setup selection
    logger.info("Setting up Notepad with selected text...")
    proc, expected_text = setup_selection()
    
    # Create hotkey manager with mocks
    from src.hotkey_manager import HotkeyManager
    config = MockConfigManager()
    translation = MockTranslationService()
    hm = HotkeyManager(config, translation, notification_callback=lambda title, msg, is_error: logger.info(f"Notification: {title} - {msg}"))
    
    # Call the callback directly
    logger.info("Calling _on_hotkey_triggered...")
    hm._on_hotkey_triggered()
    
    # Wait a bit for clipboard to be updated (callback does sleep)
    time.sleep(0.5)
    
    # Check clipboard
    clipboard_text = pyperclip.paste()
    logger.info(f"Clipboard after callback: {repr(clipboard_text)}")
    
    # Cleanup
    close_notepad(proc)
    pyperclip.copy(original)
    
    # Evaluate
    if clipboard_text and not clipboard_text.isspace():
        logger.info("SUCCESS: Clipboard contains text")
        # Check if it's the selected text or translation
        if expected_text in clipboard_text:
            logger.info("Selected text was copied (or translated)")
            return True
        else:
            logger.warning("Clipboard does not contain expected text")
            return False
    else:
        logger.warning("FAILURE: Clipboard empty")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)