#!/usr/bin/env python3
"""
Main entry point for the Desktop Translator application.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.logger import setup_logging
from src.config_manager import ConfigManager

def main():
    """Start the application."""
    # Setup logging first
    config = ConfigManager()
    setup_logging(config)
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Desktop Translator")
    print("Application started. Tray icon should be visible.")
    print("If tray icon not visible, check system tray overflow area.")
    
    # Import and run tray app
    from src.tray_app import main as tray_main
    tray_main()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Basic error handling
        import traceback
        print(f"Failed to start application: {e}")
        traceback.print_exc()
        sys.exit(1)