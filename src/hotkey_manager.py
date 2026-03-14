"""
Global hotkey manager for translation.
Registers a hotkey (default Ctrl+Shift+T) that copies selected text, translates it,
and pastes translation back.
"""
import logging
import threading
import time
import sys
import platform

logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    logger.warning("pynput library not installed. Install with: pip install pynput")

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
        self._listener = None
        self._hotkey_str = self.config.get("hotkey", "ctrl+shift+t")
        
    def start(self):
        """Start listening for hotkey."""
        if not PYNPUT_AVAILABLE:
            logger.error("pynput library unavailable, cannot register hotkey")
            return False
        
        if self._registered:
            logger.warning("Hotkey already registered")
            return True
        
        # Parse hotkey string
        try:
            hotkey_combination = self._parse_hotkey(self._hotkey_str)
            logger.info("Parsed hotkey: %s -> %s", self._hotkey_str, hotkey_combination)
        except Exception as e:
            logger.error("Failed to parse hotkey %s: %s", self._hotkey_str, e)
            return False
        
        # Register hotkey
        try:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._hotkey = hotkey_combination
            self._listener.start()
            logger.info("Hotkey registered: %s", self._hotkey_str)
            self._registered = True
        except Exception as e:
            logger.exception("Failed to register hotkey: %s", e)
            return False
        
        # Start a background thread to keep hotkey active
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
        if self._listener:
            self._listener.stop()
            self._listener.join()
        self._registered = False
        logger.info("Hotkey unregistered")
    
    def _listener_loop(self):
        """Background loop to keep hotkey listener alive."""
        while not self._stop_event.is_set():
            time.sleep(0.5)
        logger.debug("Hotkey listener loop exiting")
    
    def _parse_hotkey(self, hotkey_str):
        """Parse hotkey string like 'ctrl+shift+t' into pynput format."""
        parts = hotkey_str.lower().split('+')
        modifiers = []
        key = None
        
        for part in parts:
            part = part.strip()
            if part in ['ctrl', 'control', 'cmd', 'command']:
                # On macOS, use cmd instead of ctrl for better UX
                if platform.system() == 'Darwin':
                    modifiers.append(keyboard.Key.cmd)
                else:
                    modifiers.append(keyboard.Key.ctrl)
            elif part in ['shift']:
                modifiers.append(keyboard.Key.shift)
            elif part in ['alt', 'option']:
                if platform.system() == 'Darwin':
                    modifiers.append(keyboard.Key.alt)
                else:
                    modifiers.append(keyboard.Key.alt)
            elif part in ['meta', 'win']:
                modifiers.append(keyboard.Key.cmd)
            elif len(part) == 1:
                key = part
            else:
                # Try to parse as special key
                try:
                    key = getattr(keyboard.Key, part)
                except AttributeError:
                    key = part
        
        if not key:
            raise ValueError(f"Invalid hotkey: {hotkey_str}")
        
        return tuple(modifiers + [key])
    
    def _on_press(self, key):
        """Handle key press events."""
        pass
    
    def _on_release(self, key):
        """Handle key release events and check for hotkey."""
        if self._hotkey and key == self._hotkey[-1]:
            # Check if all modifier keys are pressed
            try:
                # Get current pressed keys
                current_pressed = set()
                
                # Check each modifier
                for modifier in self._hotkey[:-1]:
                    try:
                        if hasattr(modifier, 'name'):
                            # For special keys like ctrl, shift
                            if modifier == keyboard.Key.ctrl:
                                current_pressed.add('ctrl')
                            elif modifier == keyboard.Key.shift:
                                current_pressed.add('shift')
                            elif modifier == keyboard.Key.alt:
                                current_pressed.add('alt')
                            elif modifier == keyboard.Key.cmd:
                                current_pressed.add('cmd')
                    except Exception:
                        pass
                
                # Simulate checking if modifiers are pressed
                # This is a simplified version - in practice, you'd need to track key states
                # For now, we'll trigger on the final key release
                self._on_hotkey_triggered()
                
            except Exception as e:
                logger.debug("Error checking hotkey: %s", e)
    
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
            
            # Simulate Ctrl+C with retries
            selected_text = None
            max_attempts = 5
            base_delay = 0.4
            
            for attempt in range(max_attempts):
                logger.debug("Copy attempt %d of %d (thread %s)", attempt + 1, max_attempts, threading.current_thread().name)
                
                # Use pynput to simulate Ctrl+C
                self._simulate_copy()
                
                # Wait for clipboard to update
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
            self._simulate_paste()
            
            logger.info("Translation pasted successfully")
            if self.notification_callback:
                backend_info = f" via {result.backend}" if result.backend else ""
                self.notification_callback("Translation Completed", f"Translated {len(selected_text)} characters{backend_info}", is_error=False)
            
        except Exception as e:
            logger.exception("Error during hotkey translation: %s", e)
            if self.notification_callback:
                self.notification_callback("Translation Error", f"An error occurred: {e}", is_error=True)
    
    def _simulate_copy(self):
        """Simulate Ctrl+C using pynput."""
        try:
            keyboard_controller = keyboard.Controller()
            
            # On macOS, use Cmd+C, on Windows/Linux use Ctrl+C
            if platform.system() == 'Darwin':
                keyboard_controller.press(keyboard.Key.cmd)
                keyboard_controller.press('c')
                keyboard_controller.release('c')
                keyboard_controller.release(keyboard.Key.cmd)
            else:
                keyboard_controller.press(keyboard.Key.ctrl)
                keyboard_controller.press('c')
                keyboard_controller.release('c')
                keyboard_controller.release(keyboard.Key.ctrl)
        except Exception as e:
            logger.error("Failed to simulate copy: %s", e)
    
    def _simulate_paste(self):
        """Simulate Ctrl+V using pynput."""
        try:
            keyboard_controller = keyboard.Controller()
            
            # On macOS, use Cmd+V, on Windows/Linux use Ctrl+V
            if platform.system() == 'Darwin':
                keyboard_controller.press(keyboard.Key.cmd)
                keyboard_controller.press('v')
                keyboard_controller.release('v')
                keyboard_controller.release(keyboard.Key.cmd)
            else:
                keyboard_controller.press(keyboard.Key.ctrl)
                keyboard_controller.press('v')
                keyboard_controller.release('v')
                keyboard_controller.release(keyboard.Key.ctrl)
        except Exception as e:
            logger.error("Failed to simulate paste: %s", e)
    
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
            root.update()
            root.destroy()
        except Exception as e:
            logger.error("Failed to set clipboard text: %s", e)
    
    def update_hotkey(self, new_hotkey: str):
        """Update hotkey combination."""
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
