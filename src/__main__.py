"""
Entry point wrapper for pyshine-translator.
Sets environment variables before importing any modules.
"""
import os
import sys

# Fix OpenMP conflict on Windows
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Now import and run the main app
from src.tray_app import main

if __name__ == '__main__':
    main()
