"""
Configuration manager for the desktop translator application.
Handles loading and saving settings to a JSON file in %APPDATA%/TranslateContextMenu/.
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manage application configuration."""
    
    DEFAULT_CONFIG = {
        "api_key": "",  # empty for googletrans
        "target_language": "zh-CN",  # Chinese Simplified
        "source_language": "en",  # source language for bidirectional translation
        "bidirectional": True,  # enable automatic direction swapping
        "hotkey": "ctrl+shift+t",
        "enabled": True,
        "log_level": "INFO",
        "use_official_api": False,  # if True, use google-cloud-translate with api_key
        "translation_backend": "google",  # google, openai, ollama, custom
        "ai_providers": [],  # list of custom AI providers
        "current_ai_provider": None,  # currently selected AI provider index
    }
    
    def __init__(self, config_dir: str = None, config_filename: str = "config.json"):
        """
        Initialize config manager.
        
        Args:
            config_dir: Directory where config file resides. If None, uses 
                        %APPDATA%/TranslateContextMenu.
            config_filename: Name of config file.
        """
        if config_dir is None:
            appdata = os.getenv("APPDATA")
            if not appdata:
                raise RuntimeError("APPDATA environment variable not found")
            config_dir = os.path.join(appdata, "TranslateContextMenu")
        self.config_dir = Path(config_dir)
        self.config_path = self.config_dir / config_filename
        self._config = None
        self._ensure_config_dir()
        
    def _ensure_config_dir(self) -> None:
        """Create config directory if it doesn't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file. If file doesn't exist, create with defaults.
        
        Returns:
            Configuration dictionary.
        """
        if self._config is not None:
            return self._config.copy()
        
        if not self.config_path.exists():
            logger.info("Config file not found, creating with defaults")
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()
            return self._config.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.debug("Configuration loaded from %s", self.config_path)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load config: %s. Using defaults.", e)
            self._config = self.DEFAULT_CONFIG.copy()
        
        # Ensure all default keys exist
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value
        
        return self._config.copy()
    
    def save(self, config: Dict[str, Any] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            config: Configuration dictionary to save. If None, saves current internal config.
        """
        if config is not None:
            self._config = config.copy()
        
        if self._config is None:
            self._config = self.load()
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            logger.debug("Configuration saved to %s", self.config_path)
        except OSError as e:
            logger.error("Failed to save config: %s", e)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if self._config is None:
            self.load()
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save immediately."""
        if self._config is None:
            self.load()
        self._config[key] = value
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        if self._config is None:
            self.load()
        return self._config.copy()


if __name__ == "__main__":
    # Quick test
    import sys
    logging.basicConfig(level=logging.DEBUG)
    cm = ConfigManager()
    config = cm.load()
    print("Current config:", json.dumps(config, indent=2))
    cm.set("target_language", "zh-CN")
    print("Updated config saved.")