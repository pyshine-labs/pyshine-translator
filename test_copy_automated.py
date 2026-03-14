#!/usr/bin/env python3
"""
Automated test for Ctrl+C simulation using Notepad.
"""
import sys
import os
import subprocess
import time
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import pyautogui
import pyperclip

def open_notepad():
    """Open Notepad and return process."""
    # On Windows
    proc = subprocess.Popen(['notepad.exe'])
    time.sleep(2)  # wait for window to appear
    return proc

def close_notepad(proc):
    """Close Notepad window."""
    # Send Alt+F4
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.5)
    # If save dialog appears, press 'n' for don't save
    pyautogui.press('n')
    proc.terminate()
    proc.wait()

def test_copy_selected():
    """Main test."""
    # Backup clipboard
    original = pyperclip.paste()
    # Clear clipboard
    pyperclip.copy('')
    
    # Open Notepad
    logger.info("Opening Notepad...")
    proc = open_notepad()
    time.sleep(1)
    
    # Type test text
    test_text = "Hello world test selection"
    pyautogui.write(test_text, interval=0.05)
    time.sleep(0.5)
    
    # Select all (Ctrl+A)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.5)
    
    # Now simulate Ctrl+C via the same method as hotkey_manager
    logger.info("Simulating Ctrl+C...")
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.5)
    
    # Check clipboard
    copied = pyperclip.paste()
    logger.info(f"Clipboard content: {repr(copied)}")
    
    # Verify
    success = copied.strip() == test_text.strip()
    
    # Clean up
    close_notepad(proc)
    
    # Restore clipboard
    pyperclip.copy(original)
    
    return success, copied

if __name__ == "__main__":
    try:
        success, copied = test_copy_selected()
        if success:
            print(f"SUCCESS: Text copied correctly: {copied}")
            sys.exit(0)
        else:
            print(f"FAILURE: Clipboard content mismatch. Expected 'Hello world test selection', got {copied}")
            sys.exit(1)
    except Exception as e:
        logger.exception("Test failed with exception")
        sys.exit(2)