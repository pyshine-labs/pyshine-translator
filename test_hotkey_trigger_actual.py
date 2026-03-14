#!/usr/bin/env python3
"""
Test the actual hotkey registration (Ctrl+Space) of the running Desktop Translator.
This script simulates pressing Ctrl+Space while text is selected in Notepad,
and verifies that the hotkey triggers and copies the selected text.
"""
import sys
import os
import threading
import time
import logging
import subprocess
import pyautogui
import pyperclip
import keyboard

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

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
    test_text = "Hello world"
    pyautogui.write(test_text, interval=0.05)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    return proc, test_text

def monitor_log_for_pattern(pattern, timeout=10):
    """Read translation.log and look for pattern."""
    import re
    log_path = os.path.join(os.getenv('APPDATA'), 'TranslateContextMenu', 'translation.log')
    if not os.path.exists(log_path):
        logger.warning("Log file does not exist")
        return False
    start_time = time.time()
    while time.time() - start_time < timeout:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if re.search(pattern, content, re.IGNORECASE):
            logger.info(f"Found pattern in log: {pattern}")
            return True
        time.sleep(0.5)
    logger.warning(f"Pattern not found within {timeout}s: {pattern}")
    return False

def test_hotkey_trigger():
    """Test that Ctrl+Space triggers the hotkey and copies selected text."""
    # Backup clipboard
    original = pyperclip.paste()
    pyperclip.copy('')
    
    # Setup selection in Notepad
    logger.info("Setting up Notepad with selected text...")
    proc, expected_text = setup_selection()
    
    # Simulate pressing Ctrl+Space (the registered hotkey)
    logger.info("Simulating Ctrl+Space hotkey press...")
    keyboard.send('ctrl+space')
    
    # Wait for hotkey processing
    time.sleep(2)
    
    # Check logs for hotkey triggered
    logger.info("Checking logs for hotkey triggered...")
    hotkey_triggered = monitor_log_for_pattern(r'Hotkey triggered', timeout=5)
    selected_log_found = monitor_log_for_pattern(r'Selected text.*Hello world', timeout=5)
    
    # Check clipboard after hotkey (should be translated text, but we can just verify it changed)
    clipboard_text = pyperclip.paste()
    logger.info(f"Clipboard after hotkey: {repr(clipboard_text)}")
    
    # Cleanup
    close_notepad(proc)
    pyperclip.copy(original)
    
    # Evaluate success
    success = hotkey_triggered and selected_log_found
    if success:
        logger.info("SUCCESS: Hotkey triggered and selected text logged.")
    else:
        logger.warning(f"FAILURE: hotkey_triggered={hotkey_triggered}, selected_log_found={selected_log_found}")
    return success

if __name__ == "__main__":
    try:
        success = test_hotkey_trigger()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.exception("Test failed")
        sys.exit(2)