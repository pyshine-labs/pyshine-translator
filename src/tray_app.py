"""
System tray application for the desktop translator.
"""
import sys
import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

try:
    from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget,
                                   QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                   QLineEdit, QPushButton, QCheckBox, QComboBox,
                                   QGroupBox, QFormLayout, QMessageBox, QListWidget,
                                   QListWidgetItem, QTabWidget, QSpinBox, QScrollArea,
                                   QFrame, QSizePolicy)
    from PySide6.QtGui import QIcon, QAction
    from PySide6.QtCore import Qt, Signal, Slot, QTimer
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    logger.error("PySide6 not installed. Install with: pip install PySide6")

from .config_manager import ConfigManager
from .translator import TranslationService
from .hotkey_manager import HotkeyManager
from .ai_translator import (AITranslator, AIProvider, get_ollama_models, 
                            is_ollama_running, get_default_providers, OLLAMA_DEFAULT_URL, OllamaClient)


class SettingsDialog(QDialog):
    """Settings dialog for configuring translation."""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.setWindowTitle("Translation Settings")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        self.ollama_models = []
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        api_group = QGroupBox("Google Translate API")
        api_layout = QFormLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        api_layout.addRow("API Key (optional):", self.api_key_edit)
        self.use_official_check = QCheckBox("Use official Google Cloud Translation API")
        self.use_official_check.toggled.connect(self.on_use_official_toggled)
        api_layout.addRow(self.use_official_check)
        api_group.setLayout(api_layout)
        general_layout.addWidget(api_group)
        
        trans_group = QGroupBox("Translation")
        trans_layout = QFormLayout()
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(["en (English)", "zh-CN (Chinese Simplified)", "ja (Japanese)", "ko (Korean)", "es (Spanish)"])
        trans_layout.addRow("Source language:", self.source_lang_combo)
        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(["zh-CN (Chinese Simplified)", "en (English)", "ja (Japanese)", "ko (Korean)", "es (Spanish)"])
        trans_layout.addRow("Target language:", self.target_lang_combo)
        self.bidirectional_check = QCheckBox("Enable bidirectional translation")
        trans_layout.addRow(self.bidirectional_check)
        trans_group.setLayout(trans_layout)
        general_layout.addWidget(trans_group)
        
        backend_group = QGroupBox("Translation Backend")
        backend_layout = QFormLayout()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["Offline (Local)", "Google Translate", "AI Provider"])
        self.backend_combo.currentIndexChanged.connect(self.on_backend_changed)
        backend_layout.addRow("Backend:", self.backend_combo)
        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.setMinimumWidth(200)
        backend_layout.addRow("AI Provider:", self.ai_provider_combo)
        backend_group.setLayout(backend_layout)
        general_layout.addWidget(backend_group)
        
        hotkey_group = QGroupBox("Hotkey")
        hotkey_layout = QFormLayout()
        self.hotkey_edit = QLineEdit()
        self.hotkey_edit.setPlaceholderText("e.g., ctrl+shift+t")
        hotkey_layout.addRow("Hotkey combination:", self.hotkey_edit)
        hotkey_group.setLayout(hotkey_layout)
        general_layout.addWidget(hotkey_group)
        
        self.enabled_check = QCheckBox("Enable translation")
        general_layout.addWidget(self.enabled_check)
        
        general_layout.addStretch()
        general_tab.setLayout(general_layout)
        
        ai_tab = QWidget()
        ai_layout = QVBoxLayout()
        
        ollama_group = QGroupBox("Ollama Local Models")
        ollama_layout = QVBoxLayout()
        ollama_status_layout = QHBoxLayout()
        self.ollama_status_label = QLabel("Checking Ollama status...")
        ollama_status_layout.addWidget(self.ollama_status_label)
        self.refresh_ollama_btn = QPushButton("Refresh")
        self.refresh_ollama_btn.clicked.connect(self.refresh_ollama_models)
        ollama_status_layout.addWidget(self.refresh_ollama_btn)
        ollama_status_layout.addStretch()
        ollama_layout.addLayout(ollama_status_layout)
        
        self.ollama_list = QListWidget()
        self.ollama_list.setMaximumHeight(120)
        self.ollama_list.itemDoubleClicked.connect(self.add_ollama_model_to_providers)
        ollama_layout.addWidget(self.ollama_list)
        ollama_help = QLabel("Double-click a model to add it to AI Providers")
        ollama_help.setStyleSheet("color: gray; font-size: 10px;")
        ollama_layout.addWidget(ollama_help)
        ollama_group.setLayout(ollama_layout)
        ai_layout.addWidget(ollama_group)
        
        providers_group = QGroupBox("AI Providers")
        providers_layout = QVBoxLayout()
        
        providers_list_layout = QHBoxLayout()
        self.providers_list = QListWidget()
        self.providers_list.currentRowChanged.connect(self.on_provider_selected)
        providers_list_layout.addWidget(self.providers_list)
        
        providers_btn_layout = QVBoxLayout()
        self.add_provider_btn = QPushButton("Add Custom")
        self.add_provider_btn.clicked.connect(self.add_custom_provider)
        self.remove_provider_btn = QPushButton("Remove")
        self.remove_provider_btn.clicked.connect(self.remove_provider)
        self.test_provider_btn = QPushButton("Test Connection")
        self.test_provider_btn.clicked.connect(self.test_provider)
        providers_btn_layout.addWidget(self.add_provider_btn)
        providers_btn_layout.addWidget(self.remove_provider_btn)
        providers_btn_layout.addWidget(self.test_provider_btn)
        providers_btn_layout.addStretch()
        providers_list_layout.addLayout(providers_btn_layout)
        
        providers_layout.addLayout(providers_list_layout)
        
        provider_edit_group = QGroupBox("Provider Details")
        provider_edit_layout = QFormLayout()
        
        self.provider_name_edit = QLineEdit()
        provider_edit_layout.addRow("Name:", self.provider_name_edit)
        
        self.provider_type_combo = QComboBox()
        self.provider_type_combo.addItems(["openai", "ollama", "custom"])
        self.provider_type_combo.currentTextChanged.connect(self.on_provider_type_changed)
        provider_edit_layout.addRow("Type:", self.provider_type_combo)
        
        self.provider_url_edit = QLineEdit()
        self.provider_url_edit.setPlaceholderText("e.g., http://localhost:11434 or https://api.openai.com/v1")
        self.provider_url_edit.textChanged.connect(self.on_url_changed)
        provider_edit_layout.addRow("API URL:", self.provider_url_edit)
        
        url_btn_layout = QHBoxLayout()
        self.fetch_models_btn = QPushButton("Fetch Models")
        self.fetch_models_btn.clicked.connect(self.fetch_models_from_url)
        self.fetch_models_btn.setEnabled(False)
        url_btn_layout.addWidget(self.fetch_models_btn)
        url_btn_layout.addStretch()
        provider_edit_layout.addRow("", url_btn_layout)
        
        self.provider_key_edit = QLineEdit()
        self.provider_key_edit.setEchoMode(QLineEdit.Password)
        provider_edit_layout.addRow("API Key:", self.provider_key_edit)
        
        self.provider_model_combo = QComboBox()
        self.provider_model_combo.setEditable(True)
        self.provider_model_combo.setPlaceholderText("e.g., gpt-4, llama2, etc.")
        provider_edit_layout.addRow("Model:", self.provider_model_combo)
        
        provider_edit_group.setLayout(provider_edit_layout)
        providers_layout.addWidget(provider_edit_group)
        
        providers_group.setLayout(providers_layout)
        ai_layout.addWidget(providers_group)
        
        ai_tab.setLayout(ai_layout)
        
        self.tab_widget.addTab(general_tab, "General")
        self.tab_widget.addTab(ai_tab, "AI Providers")
        
        layout.addWidget(self.tab_widget)
        
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        QTimer.singleShot(100, self.refresh_ollama_models)
    
    def on_use_official_toggled(self, checked):
        """Toggle API key field enabled state."""
        self.api_key_edit.setEnabled(checked)
    
    def on_backend_changed(self, index):
        """Handle backend selection change."""
        self.ai_provider_combo.setEnabled(index == 2)
    
    def on_provider_type_changed(self, provider_type):
        """Handle provider type change."""
        if provider_type == "ollama":
            self.provider_url_edit.setText(OLLAMA_DEFAULT_URL)
            self.provider_key_edit.setEnabled(False)
            self.on_url_changed(self.provider_url_edit.text())
        elif provider_type == "openai":
            self.provider_url_edit.setText("https://api.openai.com/v1")
            self.provider_key_edit.setEnabled(True)
            self.fetch_models_btn.setEnabled(False)
        else:
            self.provider_key_edit.setEnabled(True)
            self.fetch_models_btn.setEnabled(False)
    
    def refresh_ollama_models(self):
        """Refresh the list of available Ollama models."""
        self.ollama_list.clear()
        if is_ollama_running():
            self.ollama_status_label.setText("Ollama is running")
            self.ollama_status_label.setStyleSheet("color: green;")
            self.ollama_models = get_ollama_models()
            for model in self.ollama_models:
                name = model.get("name", "unknown")
                size = model.get("size", 0)
                size_mb = size / (1024 * 1024) if size else 0
                item = QListWidgetItem(f"{name} ({size_mb:.1f} MB)")
                item.setData(Qt.UserRole, name)
                self.ollama_list.addItem(item)
            if not self.ollama_models:
                self.ollama_list.addItem("No models found. Pull models with: ollama pull <model>")
        else:
            self.ollama_status_label.setText("Ollama not running")
            self.ollama_status_label.setStyleSheet("color: red;")
            self.ollama_list.addItem("Install and start Ollama from https://ollama.ai")
    
    def add_ollama_model_to_providers(self, item):
        """Add an Ollama model to the providers list."""
        model_name = item.data(Qt.UserRole)
        if not model_name:
            return
        
        provider = {
            "name": f"Ollama: {model_name}",
            "provider_type": "ollama",
            "api_url": OLLAMA_DEFAULT_URL,
            "api_key": "",
            "model": model_name,
            "model_type": "chat"
        }
        
        self.add_provider_to_list(provider)
    
    def add_custom_provider(self):
        """Add a new custom provider."""
        provider = {
            "name": "New Provider",
            "provider_type": "openai",
            "api_url": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-3.5-turbo",
            "model_type": "chat"
        }
        self.add_provider_to_list(provider)
    
    def add_provider_to_list(self, provider: dict):
        """Add a provider to the list widget."""
        item = QListWidgetItem(provider.get("name", "Unknown"))
        item.setData(Qt.UserRole, provider)
        self.providers_list.addItem(item)
        self.providers_list.setCurrentRow(self.providers_list.count() - 1)
    
    def remove_provider(self):
        """Remove the selected provider."""
        current_row = self.providers_list.currentRow()
        if current_row >= 0:
            self.providers_list.takeItem(current_row)
    
    def test_provider(self):
        """Test connection to the selected provider."""
        current_row = self.providers_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Provider", "Please select a provider to test.")
            return
        
        self.save_current_provider()
        
        item = self.providers_list.item(current_row)
        provider_data = item.data(Qt.UserRole)
        provider = AIProvider.from_dict(provider_data)
        
        translator = AITranslator(provider)
        success, message = translator.test_connection()
        
        if success:
            QMessageBox.information(self, "Connection Test", message)
        else:
            QMessageBox.warning(self, "Connection Test Failed", message)
    
    def on_provider_selected(self, row):
        """Handle provider selection."""
        if row < 0:
            return
        
        item = self.providers_list.item(row)
        if item:
            provider = item.data(Qt.UserRole)
            self.provider_name_edit.setText(provider.get("name", ""))
            self.provider_type_combo.setCurrentText(provider.get("provider_type", "openai"))
            self.provider_url_edit.setText(provider.get("api_url", ""))
            self.provider_key_edit.setText(provider.get("api_key", ""))
            model = provider.get("model", "")
            self.provider_model_combo.setCurrentText(model)
    
    def on_url_changed(self, text):
        """Handle URL text change."""
        is_ollama = self.provider_type_combo.currentText() == "ollama"
        self.fetch_models_btn.setEnabled(is_ollama and len(text.strip()) > 0)
    
    def fetch_models_from_url(self):
        """Fetch available models from the entered Ollama URL."""
        url = self.provider_url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "No URL", "Please enter an Ollama URL first.")
            return
        
        self.fetch_models_btn.setEnabled(False)
        self.fetch_models_btn.setText("Fetching...")
        
        try:
            client = OllamaClient(url)
            models = client.list_models()
            
            if models:
                self.provider_model_combo.clear()
                for model in models:
                    name = model.get("name", "")
                    size = model.get("size", 0)
                    size_mb = size / (1024 * 1024) if size else 0
                    display_name = f"{name} ({size_mb:.1f} MB)"
                    self.provider_model_combo.addItem(display_name, name)
                
                if models:
                    self.provider_model_combo.setCurrentIndex(0)
                    QMessageBox.information(
                        self, 
                        "Models Found", 
                        f"Found {len(models)} model(s) from {url}\n\nSelect a model from the dropdown."
                    )
                else:
                    QMessageBox.warning(
                        self, 
                        "No Models", 
                        f"Connected to {url} but no models found.\n\nPull a model with: ollama pull <model>"
                    )
            else:
                QMessageBox.warning(
                    self, 
                    "Connection Failed", 
                    f"Could not connect to Ollama at {url}\n\nMake sure Ollama is running and the URL is correct."
                )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to fetch models: {str(e)}"
            )
        finally:
            self.fetch_models_btn.setEnabled(True)
            self.fetch_models_btn.setText("Fetch Models")
    
    def save_current_provider(self):
        """Save the currently edited provider details to the list."""
        current_row = self.providers_list.currentRow()
        if current_row < 0:
            return
        
        model = self.provider_model_combo.currentData()
        if not model:
            model = self.provider_model_combo.currentText()
        
        if model is None:
            model = ""
        
        provider = {
            "name": self.provider_name_edit.text().strip(),
            "provider_type": self.provider_type_combo.currentText(),
            "api_url": self.provider_url_edit.text().strip(),
            "api_key": self.provider_key_edit.text().strip(),
            "model": model.strip() if model else "",
            "model_type": "chat"
        }
        
        item = self.providers_list.item(current_row)
        item.setText(provider["name"])
        item.setData(Qt.UserRole, provider)
    
    def load_settings(self):
        """Load current settings into UI."""
        config = self.config.get_all()
        self.api_key_edit.setText(config.get("api_key", ""))
        self.use_official_check.setChecked(config.get("use_official_api", False))
        self.api_key_edit.setEnabled(self.use_official_check.isChecked())
        
        source_lang = config.get("source_language", "en")
        source_lang_map = {"en": 0, "zh-CN": 1, "ja": 2, "ko": 3, "es": 4}
        idx = source_lang_map.get(source_lang, 0)
        self.source_lang_combo.setCurrentIndex(idx)
        
        target_lang = config.get("target_language", "zh-CN")
        target_lang_map = {"zh-CN": 0, "en": 1, "ja": 2, "ko": 3, "es": 4}
        idx = target_lang_map.get(target_lang, 0)
        self.target_lang_combo.setCurrentIndex(idx)
        
        self.bidirectional_check.setChecked(config.get("bidirectional", True))
        self.hotkey_edit.setText(config.get("hotkey", "ctrl+shift+t"))
        self.enabled_check.setChecked(config.get("enabled", True))
        
        backend = config.get("translation_backend", "offline")
        backend_map = {"offline": 0, "google": 1, "ai": 2}
        self.backend_combo.setCurrentIndex(backend_map.get(backend, 0))
        
        providers = config.get("ai_providers", [])
        self.providers_list.clear()
        for provider in providers:
            self.add_provider_to_list(provider)
        
        current_idx = config.get("current_ai_provider")
        if current_idx is not None and 0 <= current_idx < self.providers_list.count():
            self.providers_list.setCurrentRow(current_idx)
        
        self.update_ai_provider_combo()
    
    def update_ai_provider_combo(self):
        """Update the AI provider dropdown in General tab."""
        self.ai_provider_combo.clear()
        for i in range(self.providers_list.count()):
            item = self.providers_list.item(i)
            provider = item.data(Qt.UserRole)
            self.ai_provider_combo.addItem(provider.get("name", f"Provider {i+1}"))
    
    def save_settings(self):
        """Save settings from UI to config."""
        self.save_current_provider()
        
        config = {}
        config["api_key"] = self.api_key_edit.text().strip()
        config["use_official_api"] = self.use_official_check.isChecked()
        
        src_idx = self.source_lang_combo.currentIndex()
        src_lang_codes = ["en", "zh-CN", "ja", "ko", "es"]
        config["source_language"] = src_lang_codes[src_idx]
        
        tgt_idx = self.target_lang_combo.currentIndex()
        tgt_lang_codes = ["zh-CN", "en", "ja", "ko", "es"]
        config["target_language"] = tgt_lang_codes[tgt_idx]
        
        config["bidirectional"] = self.bidirectional_check.isChecked()
        config["hotkey"] = self.hotkey_edit.text().strip()
        config["enabled"] = self.enabled_check.isChecked()
        
        backend_idx = self.backend_combo.currentIndex()
        backend_codes = ["offline", "google", "ai"]
        config["translation_backend"] = backend_codes[backend_idx]
        
        providers = []
        for i in range(self.providers_list.count()):
            item = self.providers_list.item(i)
            providers.append(item.data(Qt.UserRole))
        config["ai_providers"] = providers
        
        config["current_ai_provider"] = self.ai_provider_combo.currentIndex() if backend_idx == 2 else None
        
        if not config["hotkey"]:
            QMessageBox.warning(self, "Invalid hotkey", "Hotkey cannot be empty")
            return
        
        if backend_idx == 2 and len(providers) == 0:
            QMessageBox.warning(self, "No AI Provider", "Please add at least one AI provider in the AI Providers tab.")
            return
        
        self.config.save(config)
        self.accept()


class SystemTrayApp(QWidget):
    """Main system tray application."""
    
    def __init__(self):
        super().__init__()
        if not PYSIDE6_AVAILABLE:
            raise RuntimeError("PySide6 is required for the system tray GUI.")
        
        self.config = ConfigManager()
        self.translation_service = TranslationService(self.config)
        self.hotkey_manager = HotkeyManager(self.config, self.translation_service, self.show_notification)
        
        self.init_ui()
        self.start_services()
    
    def init_ui(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        # Load icon from file, fallback to theme
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icons", "translate.png")
        logger.info("Loading icon from %s", icon_path)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            logger.info("Icon loaded from file")
        else:
            icon = QIcon.fromTheme("document-edit")
            logger.info("Icon loaded from theme fallback")
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Desktop Translator")
        
        # Create tray menu
        self.tray_menu = QMenu()
        
        self.enable_action = QAction("Enable Translation", self)
        self.enable_action.setCheckable(True)
        self.enable_action.setChecked(self.config.get("enabled", True))
        self.enable_action.triggered.connect(self.toggle_enabled)
        self.tray_menu.addAction(self.enable_action)
        
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.show_settings)
        self.tray_menu.addAction(self.settings_action)
        
        self.tray_menu.addSeparator()
        
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(self.exit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # macOS-specific: Force tray icon to be visible
        import platform
        if platform.system() == 'Darwin':
            self.tray_icon.setVisible(True)
            logger.info("macOS: Forced tray icon visibility")
        
        self.tray_icon.show()
        logger.info("Tray icon shown, visible: %s", self.tray_icon.isVisible())
        
        hotkey = self.config.get("hotkey", "ctrl+shift+t")
        self.show_notification("Desktop Translator", f"Application started. Press {hotkey} to translate.")
        
        # Connect double-click
        self.tray_icon.activated.connect(self.on_tray_activated)
    
    def start_services(self):
        """Start hotkey manager if enabled."""
        if self.config.get("enabled", True):
            self.hotkey_manager.start()
        else:
            self.hotkey_manager.stop()
        logger.info("Services started (enabled=%s)", self.config.get("enabled"))
    
    def show_notification(self, title, message, is_error=False):
        """Show a system tray notification."""
        if not hasattr(self, 'tray_icon') or self.tray_icon is None:
            logger.warning("Cannot show notification: tray icon not available")
            return
        icon = QSystemTrayIcon.MessageIcon.Critical if is_error else QSystemTrayIcon.MessageIcon.Information
        logger.info("Showing notification: %s - %s", title, message)
        self.tray_icon.showMessage(title, message, icon, 3000)
    
    def toggle_enabled(self, checked):
        """Toggle translation on/off."""
        self.config.set("enabled", checked)
        if checked:
            self.hotkey_manager.start()
        else:
            self.hotkey_manager.stop()
        logger.info("Translation %s", "enabled" if checked else "disabled")
    
    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.hotkey_manager.stop()
            self.translation_service = TranslationService(self.config)
            self.hotkey_manager = HotkeyManager(self.config, self.translation_service, self.show_notification)
            if self.config.get("enabled", True):
                self.hotkey_manager.start()
            self.enable_action.setChecked(self.config.get("enabled", True))
            logger.info("Settings updated")
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation (e.g., double-click)."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_settings()
    
    def quit_app(self):
        """Clean up and quit."""
        logger.info("Shutting down...")
        self.hotkey_manager.stop()
        self.tray_icon.hide()
        QApplication.quit()


def main():
    """Entry point for the system tray application."""
    if not PYSIDE6_AVAILABLE:
        print("PySide6 is not installed. Please install it with: pip install PySide6")
        sys.exit(1)
    
    from .logger import setup_logging
    
    # Setup logging before creating app
    config = ConfigManager()
    setup_logging(config)
    
    # Suppress DPI scaling warnings
    QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Create system tray app and keep reference to prevent garbage collection
    tray_app = SystemTrayApp()
    
    # Keep reference to tray_app to prevent garbage collection
    app.tray_app = tray_app
    
    logger.info("Desktop Translator started")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()