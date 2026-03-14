#!/usr/bin/env python3
"""
Test the improved copy mechanism with actual hotkey registration.
"""
import sys
import os
import time
import threading
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(__file__))

import pyautogui
import pyperclip
import subprocess

# Mock translation service
from src.translator import TranslationResult
class MockTranslationService:
    def translate(self, text):
        # Return a successful translation (just echo with suffix)
        return TranslationResult(text=text + " [translated]", source_language="en", target_language="zh-CN")

# Mock config manager
class MockConfigManager:
    def __init__(self):
        self._config = {"enabled": True, "hotkey": "Ctrl+Shift+Y"}
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
    test_text = "Hello world hotkey improvement test"
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
    # notification callback
    notification_called = []
    def notification_callback(title, msg, is_error):
        notification_called.append((title, msg, is_error))
        logger.info(f"Notification: {title} - {msg}")
    
    hm = HotkeyManager(config, translation, notification_callback)
    
    # Start hotkey manager
    logger.info("Starting hotkey manager...")
    if not hm.start():
        logger.error("Failed to start hotkey manager")
        close_notepad(proc)
        return False
    
    # Wait a moment for registration
    time.sleep(1)
    
    # Simulate pressing the hotkey via pyautogui (might trigger)
    logger.info("Simulating hotkey Ctrl+Shift+Y via pyautogui...")
    pyautogui.hotkey('ctrl', 'shift', 'y')
    
    # Wait for callback to execute (should happen quickly)
    time.sleep(2)
    
    # Check clipboard
    clipboard_text = pyperclip.paste()
    logger.info(f"Clipboard after hotkey: {repr(clipboard_text)}")
    
    # Stop hotkey manager
    hm.stop()
    
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