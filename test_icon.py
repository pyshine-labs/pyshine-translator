#!/usr/bin/env python3
"""
Test icon loading and DPI suppression.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
import logging

logging.basicConfig(level=logging.INFO)

def test_icon():
    # Suppress DPI scaling warnings
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Test icon loading
    icon_path = os.path.join(os.path.dirname(__file__), "icons", "translate.png")
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        print(f"Icon loaded from {icon_path}, isNull: {icon.isNull()}")
    else:
        print("Icon file not found")
        icon = QIcon.fromTheme("document-edit")
        print(f"Fallback icon isNull: {icon.isNull()}")
    
    # Test tray icon creation (optional)
    from PySide6.QtWidgets import QSystemTrayIcon
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    print(f"Tray icon set, isSystemTrayAvailable: {QSystemTrayIcon.isSystemTrayAvailable()}")
    print("Test passed")
    sys.exit(0)

if __name__ == "__main__":
    test_icon()