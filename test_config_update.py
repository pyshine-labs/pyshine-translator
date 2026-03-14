#!/usr/bin/env python3
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config_manager import ConfigManager

def test_config_update():
    config = ConfigManager()
    print("Original config:")
    original = config.load()
    for k, v in original.items():
        print(f"  {k}: {v}")
    
    # Modify settings as per UI test
    new_config = original.copy()
    new_config["source_language"] = "fr"
    new_config["target_language"] = "es"
    new_config["bidirectional"] = not new_config.get("bidirectional", True)  # toggle
    # Keep other settings
    
    # Save
    config.save(new_config)
    print("\nSaved new config.")
    
    # Reload to verify
    config2 = ConfigManager()
    reloaded = config2.load()
    print("Reloaded config:")
    for k, v in reloaded.items():
        print(f"  {k}: {v}")
    
    # Check changes
    success = (reloaded["source_language"] == "fr" and
               reloaded["target_language"] == "es" and
               reloaded["bidirectional"] == (not original.get("bidirectional", True)))
    if success:
        print("\nSUCCESS: Config updated correctly.")
    else:
        print("\nFAILURE: Config not updated as expected.")
        print(f"Expected source=fr, got {reloaded['source_language']}")
        print(f"Expected target=es, got {reloaded['target_language']}")
        print(f"Expected bidirectional={not original.get('bidirectional', True)}, got {reloaded['bidirectional']}")
    
    # Restore original config (optional)
    config.save(original)
    print("\nRestored original config.")
    return success

if __name__ == "__main__":
    try:
        success = test_config_update()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)