#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, '/Users/mac/.local/lib/python3.12/site-packages')

print("=== Debugging pyshine-translator ===")
print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")

try:
    from PySide6.QtWidgets import QApplication
    print("✓ PySide6.QtWidgets imported")
except Exception as e:
    print(f"✗ PySide6.QtWidgets import failed: {e}")
    sys.exit(1)

try:
    from PySide6.QtGui import QIcon, QAction
    print("✓ PySide6.QtGui imported")
except Exception as e:
    print(f"✗ PySide6.QtGui import failed: {e}")
    sys.exit(1)

try:
    from PySide6.QtCore import Qt
    print("✓ PySide6.QtCore imported")
except Exception as e:
    print(f"✗ PySide6.QtCore import failed: {e}")
    sys.exit(1)

try:
    from src.config_manager import ConfigManager
    print("✓ ConfigManager imported")
except Exception as e:
    print(f"✗ ConfigManager import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from src.translator import TranslationService
    print("✓ TranslationService imported")
except Exception as e:
    print(f"✗ TranslationService import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from src.hotkey_manager import HotkeyManager
    print("✓ HotkeyManager imported")
except Exception as e:
    print(f"✗ HotkeyManager import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from src.tray_app import SystemTrayApp
    print("✓ SystemTrayApp imported")
except Exception as e:
    print(f"✗ SystemTrayApp import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== Creating QApplication ===")
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    print("✓ QApplication created")
    print(f"  Platform: {app.platformName()}")
    print(f"  System tray available: {app.isSessionRestored()}")
except Exception as e:
    print(f"✗ QApplication creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== Creating SystemTrayApp ===")
try:
    tray_app = SystemTrayApp()
    print("✓ SystemTrayApp created")
except Exception as e:
    print(f"✗ SystemTrayApp creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== Starting app.exec() ===")
print("Press Ctrl+C to exit")
try:
    sys.exit(app.exec())
except KeyboardInterrupt:
    print("\nExiting...")
    sys.exit(0)
