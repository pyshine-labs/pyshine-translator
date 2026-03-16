# PyShine Translator

[![PyShine](https://img.shields.io/badge/PyShine.com-Official_Site-9cf)](https://pyshine.com)
[![PyPI version](https://img.shields.io/pypi/v/pyshine-translator.svg)](https://pypi.org/project/pyshine-translator/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/pyshine-labs/pyshine-translator)

**[🏠 PyShine.com](https://pyshine.com)** • **[📦 PyPI](https://pypi.org/project/pyshine-translator/)** • **[📖 GitHub](https://github.com/pyshine-labs/pyshine-translator)**

---

**A powerful cross-platform desktop translator that translates selected text instantly with a global hotkey.**

Select any text in any application, press `Ctrl+Shift+Space`, and get instant translation. Supports **16+ AI providers** including DeepSeek, OpenAI, Ollama, Moonshot, and more. Works offline with local translation models.

```bash
pip install pyshine-translator
pyshine-translator
```

---

## Why PyShine Translator?

- **🚀 Instant Translation**: Select text → Press hotkey → Get translation. That's it.
- **🤖 16+ AI Providers**: DeepSeek, OpenAI, Ollama, Moonshot, Zhipu, Alibaba Qwen, Baidu ERNIE, and more
- **🌐 Offline Support**: Works without internet using local translation models
- **🔄 Bidirectional**: Auto-detects language and translates both ways (English ↔ Chinese, etc.)
- **💻 Cross-Platform**: Windows, macOS, and Linux
- **⚙️ Customizable**: Configure hotkeys, languages, and AI providers via GUI
- **🔒 Privacy First**: API keys stored locally, not uploaded anywhere

## Supported AI Providers

| Provider | Type | API Key Required |
|----------|------|------------------|
| **DeepSeek** | OpenAI-compatible | Yes |
| **Moonshot AI (Kimi)** | OpenAI-compatible | Yes |
| **Zhipu AI (GLM)** | OpenAI-compatible | Yes |
| **Alibaba Qwen** | OpenAI-compatible | Yes |
| **Baidu ERNIE** | OpenAI-compatible | Yes |
| **Tencent Hunyuan** | OpenAI-compatible | Yes |
| **ByteDance Doubao** | OpenAI-compatible | Yes |
| **Minimax** | OpenAI-compatible | Yes |
| **SiliconFlow** | OpenAI-compatible | Yes |
| **OpenAI GPT-4/3.5** | OpenAI | Yes |
| **Anthropic Claude** | OpenAI-compatible | Yes |
| **Groq** | OpenAI-compatible | Yes |
| **Together AI** | OpenAI-compatible | Yes |
| **OpenRouter** | OpenAI-compatible | Yes |
| **Ollama** | Local | No |

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

**Platform-specific notes:**

- **Windows**: All dependencies install automatically
- **macOS/Linux**: `keyboard` and `pyautogui` are Windows-only and will be skipped automatically
- **All platforms**: `pynput` provides cross-platform keyboard/mouse support

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

- googletrans == 4.0.0rc1 (Google Translate)
- langdetect >= 1.0.9 (Language detection)
- pyautogui >= 0.9.54 (Clipboard simulation)
- pynput >= 1.7.6 (Input handling)
- pyperclip >= 1.8.0 (Clipboard access)
- requests >= 2.31.0 (HTTP requests)
- pywin32 >= 305 (Windows API, Windows only)
- Pillow >= 9.0.0 (Image handling)

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

### v1.4.0 (2026)
- **Removed PySide6 dependency**: Now uses tkinter for GUI - lighter weight, faster installation
- **Added 16 AI providers**: DeepSeek, Moonshot, Zhipu, Alibaba Qwen, Baidu ERNIE, Tencent Hunyuan, ByteDance Doubao, Minimax, SiliconFlow, OpenAI, Anthropic Claude, Groq, Together AI, OpenRouter, and Ollama
- **Fixed proxy issues**: API calls now bypass proxy settings for reliable connections
- **Improved key simulation**: Using pyautogui for reliable Ctrl+C/Ctrl+V operations
- **Fixed 'c' character bug**: No more stray 'c' characters appearing before translations
- **Window tracking**: Translations now paste to the correct source window
- **Better formatting preservation**: Translations maintain original line breaks and structure
- **Fixed infinite translation loop**: Added safeguards to prevent repeated auto-translations
- **Improved clipboard handling**: More reliable clipboard operations with retries
- **Better error handling**: Clearer error messages and fallback mechanisms

### v1.3.6 (2026)
- **Suppressed OpenMP warnings**: Added warning filter to hide OpenMP error messages
- **Improved user experience**: No more scary error messages on Windows
- **App works normally**: OpenMP warnings are cosmetic, not functional

### v1.3.5 (2026)
- **Fixed OpenMP conflict properly**: Created wrapper script to set environment variable before imports
- **Improved entry point**: Changed from direct import to wrapper script
- **No more OpenMP warnings**: Environment variable set before any library imports

### v1.3.4 (2026)
- **Fixed OpenMP conflict on Windows**: Resolved libiomp5md.dll initialization error
- **Added environment variable fix**: Automatically sets KMP_DUPLICATE_LIB_OK=TRUE
- **Improved startup stability**: No more OpenMP warnings or crashes

### v1.3.3 (2026)
- **Fixed model selection bug**: Now correctly saves model name instead of display text
- **Fixed "model not found" error**: Resolved issue where selected model couldn't be found
- **Improved model handling**: Properly extracts model name from dropdown data

### v1.3.2 (2026)
- **Fixed TypeError**: Resolved "setEnabled called with wrong argument types" error
- **Fixed button enable logic**: Changed from string to boolean check for URL field
- **Improved stability**: Better handling of empty URL strings

### v1.3.1 (2026)
- **Fixed bug**: Resolved "NoneType has no attribute strip" error when saving provider without model
- **Improved error handling**: Better handling of None values in model selection

### v1.3.0 (2026)
- **Auto-fetch Ollama models**: Added "Fetch Models" button to automatically retrieve available models from any Ollama URL
- **Improved model selection**: Changed model field to dropdown combo box for easier selection
- **Better Ollama integration**: Automatically enables "Fetch Models" button when Ollama URL is entered
- **Enhanced UI**: Better feedback when fetching models and connecting to Ollama servers
- **Cross-platform Ollama support**: Easily connect to Ollama running on any device (Windows, Mac, Linux) over WiFi

### v1.2.9 (2026)
- **Improved hotkey detection**: Fixed hotkey combination detection to properly track modifier keys
- **Added cooldown mechanism**: Prevents multiple rapid triggers of the same hotkey
- **Better key tracking**: Properly tracks pressed/released keys for reliable hotkey detection
- **Enhanced logging**: Added detailed debug logging for key press/release events

### v1.2.8 (2026)
- **Fixed macOS tray icon visibility**: Added macOS-specific fixes to ensure tray icon appears in menu bar
- **Prevented garbage collection**: Keep reference to tray app to prevent icon from disappearing
- **Added visibility logging**: Better debugging for tray icon display issues

### v1.2.7 (2026)
- **Fixed hotkey support for macOS/Linux**: Replaced Windows-only `keyboard` library with cross-platform `pynput`
- **Added pyperclip dependency**: For reliable clipboard access across all platforms
- **macOS hotkey improvements**: Uses Cmd key instead of Ctrl for better macOS UX
- **Hotkey now works on all platforms**: Windows, macOS, and Linux

### v1.2.6 (2026)
- **Fixed cross-platform config directory**: Now uses platform-specific paths
  - Windows: `%APPDATA%/TranslateContextMenu`
  - macOS: `~/Library/Application Support/PyShineTranslator`
  - Linux: `~/.config/pyshine-translator`
- App now works on macOS and Linux!

### v1.2.5 (2026)
- **Added upper bounds** to all dependencies to speed up pip dependency resolution
- This significantly reduces installation time on macOS/Linux

### v1.2.4 (2026)
- **Fixed dependency resolution**: Made `keyboard` and `pyautogui` Windows-only to speed up macOS/Linux installation
- Added OS-specific classifiers (Windows, Linux, macOS) for better PyPI filtering
- Relaxed `googletrans` version constraint from `==4.0.0rc1` to `>=4.0.0rc1` for better compatibility

### v1.2.3 (2026)
- Added prominent **PyShine.com branding** links in README

### v1.2.2 (2026)
- **Fixed notification message** to show actual configured hotkey instead of hardcoded value

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

---

<p align="center">
  <a href="https://pyshine.com">
    <strong>🏠 PyShine.com</strong>
  </a>
  <br>
  <sub>Python tutorials, AI projects, and more</sub>
</p>
