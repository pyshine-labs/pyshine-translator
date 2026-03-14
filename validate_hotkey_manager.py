#!/usr/bin/env python3
"""
Validate that the modified hotkey_manager.py loads without errors.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import logging
logging.basicConfig(level=logging.WARNING)

try:
    from src.hotkey_manager import HotkeyManager
    print("SUCCESS: HotkeyManager imported successfully")
    # Check that the class can be instantiated with dummy objects
    class DummyConfig:
        def get(self, key, default=None):
            return default
    class DummyTranslation:
        pass
    hm = HotkeyManager(DummyConfig(), DummyTranslation())
    print("SUCCESS: HotkeyManager instance created")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)