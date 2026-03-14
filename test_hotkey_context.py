#!/usr/bin/env python3
"""
Test the hotkey callback context: register a hotkey and see if simulated Ctrl+C works.
"""
import sys
import os
import threading
import time
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(threadName)s %(message)s')
logger = logging.getLogger(__name__)

import keyboard
import pyautogui
import pyperclip
import subprocess

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
    """Open Notepad, write text, select all, return process."""
    proc = open_notepad()
    time.sleep(1)
    test_text = "Hello world hotkey test"
    pyautogui.write(test_text, interval=0.05)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    return proc, test_text

def test_hotkey_callback():
    """Register a hotkey and trigger it via simulated press."""
    # Backup clipboard
    original = pyperclip.paste()
    pyperclip.copy('')
    
    # Setup selection
    logger.info("Setting up Notepad with selected text...")
    proc, expected_text = setup_selection()
    
    # Define callback
    callback_called = threading.Event()
    clipboard_after = None
    
    def on_hotkey():
        logger.info("Hotkey callback invoked")
        callback_called.set()
        # Simulate Ctrl+C (same as hotkey_manager)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        clipboard_after = pyperclip.paste()
        logger.info(f"Clipboard after callback simulation: {repr(clipboard_after)}")
    
    # Register hotkey Ctrl+Shift+U (to avoid conflict with actual hotkey)
    hotkey = 'Ctrl+Shift+U'
    keyboard.add_hotkey(hotkey, on_hotkey)
    logger.info(f"Registered hotkey {hotkey}")
    
    # Simulate pressing the hotkey
    logger.info("Simulating hotkey press...")
    keyboard.send(hotkey)
    time.sleep(0.5)
    
    # Wait for callback
    if callback_called.wait(timeout=2):
        logger.info("Callback was called")
    else:
        logger.warning("Callback not called within timeout")
    
    # Check clipboard
    final_clipboard = pyperclip.paste()
    logger.info(f"Final clipboard: {repr(final_clipboard)}")
    
    # Cleanup
    keyboard.remove_hotkey(hotkey)
    close_notepad(proc)
    pyperclip.copy(original)
    
    # Evaluate success
    if final_clipboard.strip() == expected_text.strip():
        logger.info("SUCCESS: Selected text copied via hotkey callback")
        return True
    else:
        logger.warning(f"FAILURE: Expected {expected_text!r}, got {final_clipboard!r}")
        return False

if __name__ == "__main__":
    try:
        success = test_hotkey_callback()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception("Test failed")
        sys.exit(2)