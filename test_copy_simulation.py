#!/usr/bin/env python3
"""
Test the Ctrl+C simulation used in hotkey_manager.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

import time
import pyautogui
import keyboard
import pyperclip

def simulate_ctrl_c():
    """Simulate Ctrl+C using the same method as hotkey_manager."""
    # Backup clipboard
    original = pyperclip.paste()
    # Clear clipboard to see if it gets filled
    pyperclip.copy('')
    # Simulate Ctrl+C
    logger.info("Simulating Ctrl+C via pyautogui")
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.2)
    # Check clipboard
    after = pyperclip.paste()
    logger.info(f"Clipboard after simulation: {repr(after)}")
    # Restore
    pyperclip.copy(original)
    return after

def test_with_selected_text():
    """
    Requires user to have selected text in the active window.
    Prints instructions.
    """
    print("Please open Notepad (or any text editor), write some text, select it.")
    print("Keep the window active (in foreground).")
    print("Press Enter when ready...")
    input()
    text = simulate_ctrl_c()
    if text and not text.isspace():
        print(f"SUCCESS: Selected text copied: {text[:100]}")
        return True
    else:
        print("FAILURE: Clipboard empty or whitespace.")
        return False

if __name__ == "__main__":
    # First test without selection (should be empty)
    print("Testing with no selection (should be empty)...")
    empty = simulate_ctrl_c()
    if empty == '':
        print("OK: clipboard empty as expected.")
    else:
        print(f"Unexpected clipboard content: {empty}")
    
    # Test with selection
    print("\n--- Test with selected text ---")
    success = test_with_selected_text()
    sys.exit(0 if success else 1)