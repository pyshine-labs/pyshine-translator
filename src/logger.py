"""
Logging configuration for the translator application.
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path

def setup_logging(config_manager=None):
    """
    Set up logging to file and console.
    
    Args:
        config_manager: Optional ConfigManager instance to get log level.
    """
    # Determine log level
    log_level = logging.INFO
    if config_manager is not None:
        level_str = config_manager.get("log_level", "INFO").upper()
        log_level = getattr(logging, level_str, logging.INFO)
    
    # Determine log directory
    appdata = os.getenv("APPDATA")
    if not appdata:
        appdata = os.path.expanduser("~")
    log_dir = Path(appdata) / "TranslateContextMenu"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "translation.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler with rotation (max 5 MB, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    logging.info("Logging initialized. Log file: %s", log_file)


if __name__ == "__main__":
    # Test logging
    setup_logging()
    logging.debug("Debug message")
    logging.info("Info message")
    logging.warning("Warning message")
    logging.error("Error message")