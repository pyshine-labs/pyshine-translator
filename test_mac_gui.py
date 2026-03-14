#!/usr/bin/env python3
import sys
import os
import traceback

print("=== Testing pyshine-translator on macOS ===")
print(f"Python: {sys.version}")
print(f"Platform: {sys.platform}")

# Test 1: Check PySide6
print("\n[1] Testing PySide6 imports...")
try:
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon
    from PySide6.QtGui import QIcon
    from PySide6.QtCore import Qt
    print("✓ PySide6 imported successfully")
except Exception as e:
    print(f"✗ PySide6 import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check config manager
print("\n[2] Testing ConfigManager...")
try:
    from src.config_manager import ConfigManager
    config = ConfigManager()
    print(f"✓ ConfigManager created")
    print(f"  Config dir: {config.config_dir}")
    print(f"  Config path: {config.config_path}")
except Exception as e:
    print(f"✗ ConfigManager failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check icon
print("\n[3] Testing icon loading...")
icon_path = os.path.join(os.path.dirname(__file__), "icons", "translate.png")
print(f"  Icon path: {icon_path}")
print(f"  Icon exists: {os.path.exists(icon_path)}")

# Test 4: Create QApplication
print("\n[4] Creating QApplication...")
try:
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    print("✓ QApplication created")
    print(f"  Platform: {app.platformName()}")
    print(f"  System tray available: {QSystemTrayIcon.isSystemTrayAvailable()}")
except Exception as e:
    print(f"✗ QApplication creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Create system tray icon
print("\n[5] Creating system tray icon...")
try:
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        print("✓ Icon loaded from file")
    else:
        icon = QIcon.fromTheme("document-edit")
        print("✓ Icon loaded from theme fallback")
    
    tray_icon = QSystemTrayIcon(icon)
    tray_icon.setToolTip("Test Tray Icon")
    tray_icon.show()
    print("✓ System tray icon created and shown")
    print(f"  Is visible: {tray_icon.isVisible()}")
except Exception as e:
    print(f"✗ System tray icon failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 6: Create full SystemTrayApp
print("\n[6] Creating SystemTrayApp...")
try:
    from src.tray_app import SystemTrayApp
    tray_app = SystemTrayApp()
    print("✓ SystemTrayApp created successfully")
except Exception as e:
    print(f"✗ SystemTrayApp creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n=== All tests passed! ===")
print("App is running. Check your menu bar for the tray icon.")
print("Press Ctrl+C to exit.")

try:
    sys.exit(app.exec())
except KeyboardInterrupt:
    print("\nExiting...")
    sys.exit(0)
