"""
Global hotkey manager for translation.
Registers a hotkey (default Ctrl+Shift+T) that copies selected text, translates it,
and pastes the translation back.
"""
import logging
import threading
import time
import sys

logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    logger.warning("keyboard library not installed. Install with: pip install keyboard")

try:
    import pyautogui
    PY_AUTOGUI_AVAILABLE = True
except ImportError:
    PY_AUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not installed. Install with: pip install pyautogui")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    logger.warning("pyperclip not installed. Install with: pip install pyperclip")

class HotkeyManager:
    """
    Manages global hotkey registration and translation triggered by hotkey.
    """
    def __init__(self, config_manager, translation_service, notification_callback=None):
        self.config = config_manager
        self.translation_service = translation_service
        self.notification_callback = notification_callback
        self._hotkey = None
        self._registered = False
        self._stop_event = threading.Event()
        self._listener_thread = None
        self._hotkey_str = self.config.get("hotkey", "ctrl+shift+t")
        
    def start(self):
        """Start listening for hotkey."""
        if not KEYBOARD_AVAILABLE:
            logger.error("keyboard library unavailable, cannot register hotkey")
            return False
        
        if self._registered:
            logger.warning("Hotkey already registered")
            return True
        
        # Register the hotkey
        try:
            keyboard.add_hotkey(self._hotkey_str, self._on_hotkey_triggered)
            logger.info("Hotkey registered: %s", self._hotkey_str)
            self._registered = True
        except Exception as e:
            logger.exception("Failed to register hotkey: %s", e)
            return False
        
        # Start a background thread to keep the hotkey active
        self._stop_event.clear()
        self._listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._listener_thread.start()
        logger.debug("Hotkey listener started")
        return True
    
    def stop(self):
        """Stop listening for hotkey."""
        if not self._registered:
            return
        self._stop_event.set()
        if self._listener_thread:
            self._listener_thread.join(timeout=1)
        try:
            keyboard.remove_hotkey(self._hotkey_str)
        except Exception:
            pass
        self._registered = False
        logger.info("Hotkey unregistered")
    
    def _listener_loop(self):
        """Background loop to keep the hotkey listener alive."""
        while not self._stop_event.is_set():
            time.sleep(0.5)
        logger.debug("Hotkey listener loop exiting")
    
    def _on_hotkey_triggered(self):
        """Callback when hotkey is pressed."""
        logger.info("Hotkey triggered (thread %s)", threading.current_thread().name)
        if not self.config.get("enabled", True):
            logger.debug("Translation disabled, ignoring hotkey")
            return
        
        # Step 1: Copy selected text (simulate Ctrl+C)
        original_clipboard = None
        try:
            # Backup clipboard content
            if PYPERCLIP_AVAILABLE:
                original_clipboard = pyperclip.paste()
            else:
                # Fallback to using pyautogui hotkey
                pass
            
            # Simulate Ctrl+C with retries and improved reliability
            selected_text = None
            max_attempts = 5
            base_delay = 0.4
            for attempt in range(max_attempts):
                logger.debug("Copy attempt %d of %d (thread %s)", attempt + 1, max_attempts, threading.current_thread().name)
                
                # On first attempt, try to release any stuck modifier keys that might interfere
                if attempt == 0 and KEYBOARD_AVAILABLE:
                    try:
                        keyboard.release('ctrl')
                        keyboard.release('shift')
                        keyboard.release('alt')
                        time.sleep(0.05)
                    except Exception:
                        pass
                
                if PY_AUTOGUI_AVAILABLE:
                    pyautogui.hotkey('ctrl', 'c')
                else:
                    keyboard.send('ctrl+c')
                
                # Wait for clipboard to update, increasing delay with each attempt
                delay = base_delay + (attempt * 0.1)
                time.sleep(delay)
                
                # Get clipboard text
                if PYPERCLIP_AVAILABLE:
                    selected_text = pyperclip.paste()
                else:
                    selected_text = self._get_clipboard_text_fallback()
                
                logger.debug("Clipboard after attempt %d: %r", attempt + 1, selected_text[:200] if selected_text else '')
                
                if selected_text and not selected_text.isspace():
                    logger.debug("Copy succeeded on attempt %d", attempt + 1)
                    break
                else:
                    logger.debug("Clipboard empty after attempt %d, retrying...", attempt + 1)
                    # Additional small delay before next attempt
                    time.sleep(0.2)
            
            if not selected_text or selected_text.isspace():
                logger.warning("No text selected or clipboard empty after %d attempts", max_attempts)
                # Restore clipboard
                if original_clipboard is not None and PYPERCLIP_AVAILABLE:
                    pyperclip.copy(original_clipboard)
                return
            
            logger.info("Selected text: %s", selected_text[:100])
            
            # Step 2: Translate
            result = self.translation_service.translate(selected_text)
            if not result.success():
                logger.error("Translation failed: %s", result.error)
                # Show notification
                if self.notification_callback:
                    self.notification_callback("Translation Failed", f"Translation failed: {result.error}", is_error=True)
                return
            
            translated_text = result.text
            logger.info("Translated text: %s", translated_text[:100])
            
            # Step 3: Replace clipboard with translation
            if PYPERCLIP_AVAILABLE:
                pyperclip.copy(translated_text)
            else:
                self._set_clipboard_text_fallback(translated_text)
            
            # Small delay to ensure clipboard updated
            time.sleep(0.1)
            
            # Step 4: Paste (simulate Ctrl+V)
            if PY_AUTOGUI_AVAILABLE:
                pyautogui.hotkey('ctrl', 'v')
            else:
                keyboard.send('ctrl+v')
            
            logger.info("Translation pasted successfully")
            if self.notification_callback:
                backend_info = f" via {result.backend}" if result.backend else ""
                self.notification_callback("Translation Completed", f"Translated {len(selected_text)} characters{backend_info}", is_error=False)
            
            # Restore original clipboard after a short delay (optional)
            # For now, we keep translation in clipboard.
            # If we want to restore, we could copy original_clipboard back after a delay.
            
        except Exception as e:
            logger.exception("Error during hotkey translation: %s", e)
            if self.notification_callback:
                self.notification_callback("Translation Error", f"An error occurred: {e}", is_error=True)
        finally:
            # If we backed up clipboard and want to restore, we could do it here
            pass
    
    def _get_clipboard_text_fallback(self):
        """Fallback method to get clipboard text using tkinter."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text
        except Exception as e:
            logger.error("Failed to get clipboard text: %s", e)
            return ""
    
    def _set_clipboard_text_fallback(self, text):
        """Fallback method to set clipboard text using tkinter."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()  # needed for clipboard to persist
            root.destroy()
        except Exception as e:
            logger.error("Failed to set clipboard text: %s", e)
    
    def update_hotkey(self, new_hotkey: str):
        """Update the hotkey combination."""
        if self._registered:
            self.stop()
        self._hotkey_str = new_hotkey
        self.config.set("hotkey", new_hotkey)
        self.start()


if __name__ == "__main__":
    # Quick test
    import sys
    sys.path.insert(0, '.')
    from config_manager import ConfigManager
    from translator import TranslationService
    
    logging.basicConfig(level=logging.DEBUG)
    cm = ConfigManager()
    ts = TranslationService(cm)
    hm = HotkeyManager(cm, ts)
    print("Starting hotkey manager. Press Ctrl+Shift+T to test. Press Ctrl+C to exit.")
    try:
        hm.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        hm.stop()
        print("Exiting.")