# PyShine Translator v1.1.0

A cross-platform desktop translator application that translates selected text using a global hotkey. Supports offline translation (CPU-compatible, no internet required), Google Translate, and AI providers (OpenAI, Ollama, and custom APIs).

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/pyshine-labs/pyshine-translator)

## Features

- **System Tray Application**: Runs in the background with a system tray icon
- **Global Hotkey**: Press `Ctrl+Shift+T` (default) to translate selected text
- **Multiple Translation Backends**:
  - **Offline (Default)**: CPU-compatible local translation using Argos Translate - works without internet!
  - Google Translate (free via googletrans)
  - AI Providers: OpenAI, Ollama, and custom OpenAI-compatible APIs
- **Offline First**: Default mode supports translations even without internet connection
- **Ollama Integration**: Automatically discovers and lists local Ollama models
- **Bidirectional Translation**: Auto-detects source language and translates accordingly
- **Multi-language Support**: English, Chinese, Japanese, Korean, Spanish, and more
- **Customizable Settings**: Configure hotkeys, languages, and AI providers via GUI
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### From PyPI (Recommended)

```bash
pip install pyshine-translator
```

### From Source

```bash
git clone https://github.com/pyshine-labs/pyshine-translator.git
cd pyshine-translator
pip install -e .
```

## Quick Start

### Command Line

After installation, run the application:

```bash
pyshine-translator
```

### From Python

```python
from src import ConfigManager, TranslationService

config = ConfigManager()
service = TranslationService(config)
result = service.translate("Hello, world!")

if result.success():
    print(f"Translation: {result.text}")
    print(f"Backend: {result.backend}")
else:
    print(f"Error: {result.error}")
```

## Usage

1. **Launch the Application**: Run `pyshine-translator` from terminal/command prompt
2. **System Tray Icon**: Look for the translator icon in your system tray
3. **Right-click Menu**:
   - **Enable Translation**: Toggle the hotkey on/off
   - **Settings**: Open configuration window
   - **Exit**: Quit the application
4. **Translate Text**:
   - Select text in any application
   - Press `Ctrl+Shift+T` (or your custom hotkey)
   - The selected text will be replaced with the translation

## Configuration

### General Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Backend | Offline (Local), Google Translate, or AI Provider | Offline (Local) |
| Source Language | Source language for bidirectional translation | English |
| Target Language | Target language for translation | Chinese Simplified |
| Bidirectional | Auto-detect and swap translation direction | Enabled |
| Hotkey | Global hotkey combination | Ctrl+Shift+T |

### Offline Translation

The default backend uses **Argos Translate** for offline translation:
- Works without internet connection
- CPU-compatible (no GPU required)
- First run will download language models automatically
- Supports many language pairs

To install additional language models:
```python
from argostranslate import package
package.update_package_index()
package.install_from_path(package.get_available_packages()[0].download())
```

### AI Provider Settings

Navigate to the **AI Providers** tab in Settings to configure AI backends:

1. **Ollama Models**:
   - Automatically lists available local models
   - Double-click a model to add it as a provider
   - Requires Ollama to be running (`ollama serve`)

2. **Custom Providers**:
   - Click "Add Custom" to add OpenAI or custom API providers
   - Configure: Name, Type, API URL, API Key, Model Name
   - Use "Test Connection" to verify settings

### Supported AI Providers

| Provider | Type | API URL | API Key Required |
|----------|------|---------|------------------|
| OpenAI GPT-4 | openai | https://api.openai.com/v1 | Yes |
| OpenAI GPT-3.5 | openai | https://api.openai.com/v1 | Yes |
| Ollama | ollama | http://localhost:11434 | No |
| Custom | custom | Your URL | Depends |

## Project Structure

```
pyshine-translator/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── config_manager.py    # Configuration management
│   ├── translator.py        # Translation service
│   ├── ai_translator.py     # AI translation backends
│   ├── hotkey_manager.py    # Global hotkey handling
│   ├── logger.py            # Logging setup
│   └── tray_app.py          # System tray GUI
├── icons/
│   └── translate.png        # Application icon
├── main.py                  # Entry point
├── pyproject.toml           # Package configuration
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## Requirements

- Python 3.8 or higher
- Platform: Windows, macOS, or Linux

### Dependencies

- PySide6 >= 6.5.0 (GUI)
- googletrans == 4.0.0rc1 (Google Translate)
- langdetect >= 1.0.9 (Language detection)
- keyboard >= 0.13.5 (Global hotkeys)
- pyautogui >= 0.9.54 (Clipboard simulation)
- pynput >= 1.7.6 (Input handling)
- requests >= 2.31.0 (HTTP requests)

## Configuration Files

Configuration is stored in:
- **Windows**: `%APPDATA%\TranslateContextMenu\config.json`
- **macOS**: `~/Library/Application Support/TranslateContextMenu/config.json`
- **Linux**: `~/.config/TranslateContextMenu/config.json`

Logs are written to:
- **Windows**: `%APPDATA%\TranslateContextMenu\translation.log`
- **macOS**: `~/Library/Application Support/TranslateContextMenu/translation.log`
- **Linux**: `~/.config/TranslateContextMenu/translation.log`

## Acknowledgments

- [argostranslate](https://pypi.org/project/argostranslate/) - Offline translation library
- [googletrans](https://pypi.org/project/googletrans/) - Free Google Translate API
- [PySide6](https://pypi.org/project/PySide6/) - Qt for Python GUI
- [keyboard](https://pypi.org/project/keyboard/) - Global hotkey support
- [pyautogui](https://pypi.org/project/PyAutoGUI/) - GUI automation
- [Ollama](https://ollama.ai/) - Local LLM runtime

## Changelog

### v1.2.1 (2026)
- **Fixed bidirectional translation** for offline mode - now correctly uses detected language as source

### v1.2.0 (2026)
- **Auto-install language models**: Offline translation now auto-downloads required language pairs on first use
- Improved error handling for missing language models
- Fixed googletrans compatibility issues with newer httpcore versions

### v1.1.0 (2026)
- Added **offline translation** backend using Argos Translate
- CPU-compatible local translation - works without internet!
- Set offline as default backend for immediate use
- Supports multiple language pairs

### v1.0.0 (2024)
- Initial release
- Google Translate support
- AI provider support (OpenAI, Ollama, custom)
- Automatic Ollama model discovery
- Bidirectional translation
- Cross-platform support
- System tray integration
- Configurable hotkeys
- GUI settings panel
