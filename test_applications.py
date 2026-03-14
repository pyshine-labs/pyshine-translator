#!/usr/bin/env python3
"""
Test copy simulation across different applications (Notepad, WordPad).
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

def open_application(exe_path, args=None):
    """Open application and return process."""
    try:
        proc = subprocess.Popen([exe_path] + (args if args else []))
        time.sleep(3)  # wait for window
        return proc
    except Exception as e:
        logger.error(f"Failed to open {exe_path}: {e}")
        return None

def close_application(proc):
    """Close application window."""
    try:
        # Alt+F4 to close window
        pyautogui.hotkey('alt', 'f4')
        time.sleep(1)
        # If save dialog appears, press 'n' for don't save
        pyautogui.press('n')
        time.sleep(0.5)
    except Exception:
        pass
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            pass

def test_application(app_name, exe_path):
    """Test copy simulation in given application."""
    logger.info(f"Testing {app_name}...")
    # Backup clipboard
    original = pyperclip.paste()
    pyperclip.copy('')
    
    proc = open_application(exe_path)
    if not proc:
        logger.error(f"Could not start {app_name}")
        return False
    
    try:
        # Write some text
        test_text = f"Hello {app_name} test"
        pyautogui.write(test_text, interval=0.05)
        time.sleep(1)
        # Select all
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)
        
        # Simulate Ctrl+C via pyautogui (same as hotkey_manager)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.5)
        
        # Check clipboard
        copied = pyperclip.paste()
        logger.info(f"{app_name} clipboard: {repr(copied)}")
        
        success = copied.strip() == test_text.strip()
        if success:
            logger.info(f"SUCCESS: {app_name} copy works")
        else:
            logger.warning(f"FAILURE: {app_name} copy failed, got {copied}")
        return success
    finally:
        close_application(proc)
        pyperclip.copy(original)

def main():
    results = []
    
    # Notepad
    notepad_path = "C:\\Windows\\System32\\notepad.exe"
    if os.path.exists(notepad_path):
        results.append(("Notepad", test_application("Notepad", notepad_path)))
    else:
        logger.warning("Notepad not found")
    
    # WordPad
    wordpad_path = "C:\\Program Files\\Windows NT\\Accessories\\wordpad.exe"
    if not os.path.exists(wordpad_path):
        wordpad_path = "C:\\Windows\\System32\\write.exe"
    if os.path.exists(wordpad_path):
        results.append(("WordPad", test_application("WordPad", wordpad_path)))
    else:
        logger.warning("WordPad not found")
    
    # Summary
    logger.info("--- Summary ---")
    for app, success in results:
        logger.info(f"{app}: {'PASS' if success else 'FAIL'}")
    
    all_pass = all(success for _, success in results)
    return all_pass

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)