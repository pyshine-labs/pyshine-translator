# PyShine Translator v1.0.0

A cross-platform desktop translator application that translates selected text using a global hotkey. Supports Google Translate and AI providers (OpenAI, Ollama, and custom APIs).

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/pyshine-labs/pyshine-translator)

## Features

- **System Tray Application**: Runs in the background with a system tray icon
- **Global Hotkey**: Press `Ctrl+Shift+T` (default) to translate selected text
- **Multiple Translation Backends**:
  - Google Translate (free via googletrans)
  - AI Providers: OpenAI, Ollama, and custom OpenAI-compatible APIs
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

### Using pip with GitHub

```bash
pip install git+https://github.com/pyshine-labs/pyshine-translator.git
```

## Quick Start

### Command Line

After installation, run the application:

```bash
pyshine-translator
```

Or alternatively:

```bash
python -m src.tray_app
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
| Backend | Google Translate or AI Provider | Google Translate |
| Source Language | Source language for bidirectional translation | English |
| Target Language | Target language for translation | Chinese Simplified |
| Bidirectional | Auto-detect and swap translation direction | Enabled |
| Hotkey | Global hotkey combination | Ctrl+Shift+T |

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
├── MANIFEST.in              # Package manifest
├── LICENSE                  # MIT License
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

## Building from Source

### Development Setup

```bash
git clone https://github.com/pyshine-labs/pyshine-translator.git
cd pyshine-translator
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

pip install -e ".[dev]"
```

### Build Distribution

```bash
pip install build
python -m build
```

This creates:
- `dist/pyshine_translator-1.0.0.tar.gz` (source distribution)
- `dist/pyshine_translator-1.0.0-py3-none-any.whl` (wheel)

### Upload to PyPI

```bash
pip install twine
twine upload dist/*
```

## Troubleshooting

### Hotkey Not Working
- Make sure no other application is using the same hotkey
- Try running as administrator (Windows)
- Check if the application is enabled in the tray menu

### Ollama Models Not Showing
- Ensure Ollama is running: `ollama serve`
- Check if models are installed: `ollama list`
- Pull a model if needed: `ollama pull llama2`

### Translation Fails
- Check your internet connection (for Google Translate)
- Verify API key for OpenAI providers
- Check logs in the configuration directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [googletrans](https://pypi.org/project/googletrans/) - Free Google Translate API
- [PySide6](https://pypi.org/project/PySide6/) - Qt for Python GUI
- [keyboard](https://pypi.org/project/keyboard/) - Global hotkey support
- [pyautogui](https://pypi.org/project/PyAutoGUI/) - GUI automation
- [Ollama](https://ollama.ai/) - Local LLM runtime

## Changelog

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
