#!/usr/bin/env python3
import sys
import os
import tempfile
import shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager

def test_default_hotkey():
    # Create a temporary config directory
    tmpdir = tempfile.mkdtemp()
    try:
        cm = ConfigManager(config_dir=tmpdir)
        config = cm.load()
        hotkey = config.get("hotkey")
        print(f"Default hotkey: {hotkey}")
        assert hotkey == "ctrl+shift+t", f"Expected 'ctrl+shift+t', got {hotkey}"
        print("SUCCESS: Default hotkey is correct.")
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    success = test_default_hotkey()
    sys.exit(0 if success else 1)