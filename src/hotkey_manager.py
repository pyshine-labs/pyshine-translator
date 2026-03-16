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

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not installed. Install with: pip install pyautogui")

# Windows API for window management and key simulation
if platform.system() == 'Windows':
    try:
        import ctypes
        import ctypes.wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        # Windows SendInput structures for reliable key simulation
        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        KEYEVENTF_EXTENDEDKEY = 0x0001
        
        VK_CONTROL = 0x11
        VK_SHIFT = 0x10
        VK_MENU = 0x12  # Alt
        VK_C = 0x43
        VK_V = 0x56
        VK_A = 0x41
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", ctypes.wintypes.WORD),
                ("wScan", ctypes.wintypes.WORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG)),
            ]
        
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.wintypes.LONG),
                ("dy", ctypes.wintypes.LONG),
                ("mouseData", ctypes.wintypes.DWORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG)),
            ]
        
        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", ctypes.wintypes.DWORD),
                ("wParamL", ctypes.wintypes.WORD),
                ("wParamH", ctypes.wintypes.WORD),
            ]
        
        class INPUT_UNION(ctypes.Union):
            _fields_ = [
                ("ki", KEYBDINPUT),
                ("mi", MOUSEINPUT),
                ("hi", HARDWAREINPUT),
            ]
        
        class INPUT(ctypes.Structure):
            _anonymous_ = ("_input",)
            _fields_ = [
                ("type", ctypes.wintypes.DWORD),
                ("_input", INPUT_UNION),
            ]
        
        WINDOWS_API_AVAILABLE = True
    except Exception as e:
        WINDOWS_API_AVAILABLE = False
        logger.warning("Windows API not available: %s", e)
else:
    WINDOWS_API_AVAILABLE = False

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
        self._pressed_keys = set()
        self._last_trigger_time = 0
        self._trigger_cooldown = 0.5
        self._translation_lock = threading.Lock()
        self._is_translating = False
        self._simulating_keys = False
        self._source_window_handle = None
        self._source_window_title = None
    
    def _win_send_key(self, vk_code, key_down=True):
        """Send a key event using Windows SendInput API."""
        if not WINDOWS_API_AVAILABLE:
            return False
        
        flags = 0 if key_down else KEYEVENTF_KEYUP
        
        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp._input.ki.wVk = vk_code
        inp._input.ki.wScan = 0
        inp._input.ki.dwFlags = flags
        inp._input.ki.time = 0
        inp._input.ki.dwExtraInfo = None
        
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        return True
    
    def _win_send_hotkey(self, vk_modifier, vk_key):
        """Send a hotkey combination using Windows SendInput API."""
        if not WINDOWS_API_AVAILABLE:
            return False
        
        self._simulating_keys = True
        try:
            self._win_send_key(vk_modifier, key_down=True)
            time.sleep(0.05)
            self._win_send_key(vk_key, key_down=True)
            time.sleep(0.05)
            self._win_send_key(vk_key, key_down=False)
            time.sleep(0.05)
            self._win_send_key(vk_modifier, key_down=False)
            time.sleep(0.1)
            return True
        finally:
            self._simulating_keys = False
            self._pressed_keys.clear()
    
    def _get_foreground_window(self):
        """Get the current foreground window handle and title."""
        if not WINDOWS_API_AVAILABLE:
            return None, None
        
        try:
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value if buff.value else ""
            return hwnd, title
        except Exception as e:
            logger.error("Failed to get foreground window: %s", e)
            return None, None
    
    def _set_foreground_window(self, hwnd):
        """Set the foreground window by handle."""
        if not WINDOWS_API_AVAILABLE or not hwnd:
            return False
        
        try:
            # Windows has restrictions on SetForegroundWindow
            # We need to use a workaround to force focus
            # First, try to attach to the foreground window's thread
            foreground_thread = user32.GetWindowThreadProcessId(hwnd, None)
            current_thread = kernel32.GetCurrentThreadId()
            current_foreground = user32.GetForegroundWindow()
            current_foreground_thread = user32.GetWindowThreadProcessId(current_foreground, None)
            
            # Attach threads to allow focus change
            user32.AttachThreadInput(current_foreground_thread, current_thread, True)
            user32.AttachThreadInput(current_thread, foreground_thread, True)
            
            # Show the window first
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            
            # Now set foreground
            result = user32.SetForegroundWindow(hwnd)
            
            # Detach threads
            user32.AttachThreadInput(current_thread, foreground_thread, False)
            user32.AttachThreadInput(current_foreground_thread, current_thread, False)
            
            if result:
                logger.debug("Successfully set foreground window using thread attach")
                return True
            else:
                # Fallback: just show the window
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.BringWindowToTop(hwnd)
                logger.debug("Used fallback method to bring window to top")
                return True
        except Exception as e:
            logger.error("Failed to set foreground window: %s", e)
            # Last resort fallback
            try:
                user32.ShowWindow(hwnd, 9)
                user32.BringWindowToTop(hwnd)
            except:
                pass
            return False
    
    def _is_window_valid(self, hwnd):
        """Check if a window handle is still valid."""
        if not WINDOWS_API_AVAILABLE or not hwnd:
            return False
        
        try:
            return user32.IsWindow(hwnd) != 0
        except Exception:
            return False
        
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
        if self._simulating_keys:
            return
        try:
            key_name = self._get_key_name(key)
            if key_name:
                self._pressed_keys.add(key_name)
                logger.debug("Key pressed: %s, currently pressed: %s", key_name, self._pressed_keys)
        except Exception as e:
            logger.debug("Error tracking key press: %s", e)
    
    def _on_release(self, key):
        """Handle key release events and check for hotkey."""
        if self._simulating_keys:
            return
        try:
            key_name = self._get_key_name(key)
            if key_name:
                # Check for hotkey BEFORE removing the key from pressed set
                if self._check_hotkey():
                    current_time = time.time()
                    if current_time - self._last_trigger_time >= self._trigger_cooldown:
                        self._last_trigger_time = current_time
                        self._on_hotkey_triggered()
                    else:
                        logger.debug("Hotkey triggered too recently, ignoring (cooldown: %.2fs)", self._trigger_cooldown)
                self._pressed_keys.discard(key_name)
                logger.debug("Key released: %s, currently pressed: %s", key_name, self._pressed_keys)
        except Exception as e:
            logger.debug("Error tracking key release: %s", e)
    
    def _get_key_name(self, key):
        """Get a normalized key name for comparison."""
        try:
            if hasattr(key, 'name'):
                name = key.name
            elif hasattr(key, 'char'):
                name = key.char
            else:
                name = str(key)
            
            # Normalize modifier key names
            name_lower = name.lower() if name else ''
            if name_lower in ('ctrl_l', 'ctrl_r', 'control_l', 'control_r'):
                name = 'ctrl'
            elif name_lower in ('shift_l', 'shift_r'):
                name = 'shift'
            elif name_lower in ('alt_l', 'alt_r'):
                name = 'alt'
            elif name_lower in ('cmd_l', 'cmd_r'):
                name = 'cmd'
            
            return name
        except Exception:
            return None
    
    def _check_hotkey(self):
        """Check if the current pressed keys match the hotkey."""
        if not self._hotkey:
            return False
        
        try:
            required_keys = set()
            for key in self._hotkey:
                key_name = self._get_key_name(key)
                if key_name:
                    required_keys.add(key_name)
            
            logger.debug("Hotkey check: pressed=%s, required=%s, match=%s", 
                        self._pressed_keys, required_keys, self._pressed_keys == required_keys)
            
            if self._pressed_keys == required_keys:
                logger.info("Hotkey combination detected: %s", self._hotkey_str)
                return True
        except Exception as e:
            logger.debug("Error checking hotkey: %s", e)
        
        return False
    
    def _on_hotkey_triggered(self):
        """Callback when hotkey is pressed."""
        logger.info("Hotkey triggered (thread %s)", threading.current_thread().name)
        
        if self._is_translating:
            logger.debug("Translation already in progress, skipping")
            return
        
        if not self.config.get("enabled", True):
            logger.debug("Translation disabled, ignoring hotkey")
            return
        
        with self._translation_lock:
            if self._is_translating:
                logger.debug("Translation already in progress, skipping")
                return
            self._is_translating = True
        
        try:
            self._do_translation()
        finally:
            with self._translation_lock:
                self._is_translating = False
    
    def _do_translation(self):
        """Perform the actual translation."""
        # Step 0: Capture source window
        self._source_window_handle, self._source_window_title = self._get_foreground_window()
        logger.info("Source window: handle=%s, title='%s'", self._source_window_handle, self._source_window_title)
        
        # Step 1: Copy selected text (simulate Ctrl+C)
        original_clipboard = None
        try:
            # Backup clipboard content
            if PYPERCLIP_AVAILABLE:
                original_clipboard = pyperclip.paste()
                logger.debug("Original clipboard: %r", original_clipboard[:100] if original_clipboard else '')
            
            # Simulate Ctrl+C with retries
            selected_text = None
            max_attempts = 5
            base_delay = 0.6
            
            for attempt in range(max_attempts):
                logger.debug("Copy attempt %d of %d (thread %s)", attempt + 1, max_attempts, threading.current_thread().name)
                
                # Use pyautogui to simulate Ctrl+C
                self._simulate_copy()
                
                # Wait for clipboard to update
                delay = base_delay + (attempt * 0.2)
                time.sleep(delay)
                
                # Get clipboard text
                if PYPERCLIP_AVAILABLE:
                    selected_text = pyperclip.paste()
                else:
                    selected_text = self._get_clipboard_text_fallback()
                
                logger.debug("Clipboard after attempt %d: %r", attempt + 1, selected_text[:200] if selected_text else '')
                
                # Check if clipboard has content
                if selected_text and not selected_text.isspace() and len(selected_text) > 0:
                    logger.debug("Copy succeeded on attempt %d", attempt + 1)
                    break
                else:
                    logger.debug("Clipboard empty after attempt %d, retrying...", attempt + 1)
                    time.sleep(0.3)
            
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
            
            # Step 4: Restore focus to source window and paste
            if self._is_window_valid(self._source_window_handle):
                logger.info("Restoring focus to source window: %s", self._source_window_title)
                self._set_foreground_window(self._source_window_handle)
                time.sleep(0.3)  # Wait for window to be focused
            
            # Step 5: Paste (simulate Ctrl+V)
            self._simulate_paste()
            
            logger.info("Translation pasted successfully to %s", self._source_window_title)
            if self.notification_callback:
                backend_info = f" via {result.backend}" if result.backend else ""
                window_info = f" to {self._source_window_title}" if self._source_window_title else ""
                self.notification_callback("Translation Completed", f"Translated {len(selected_text)} characters{backend_info}{window_info}", is_error=False)
            
        except Exception as e:
            logger.exception("Error during hotkey translation: %s", e)
            if self.notification_callback:
                self.notification_callback("Translation Error", f"An error occurred: {e}", is_error=True)
    
    def _simulate_copy(self):
        """Simulate Ctrl+C using Windows SendInput API for reliability."""
        try:
            if WINDOWS_API_AVAILABLE:
                self._win_send_hotkey(VK_CONTROL, VK_C)
                logger.debug("Used Windows SendInput for Ctrl+C simulation")
            elif PYAUTOGUI_AVAILABLE:
                self._simulating_keys = True
                pyautogui.keyDown('ctrl')
                time.sleep(0.1)
                pyautogui.keyDown('c')
                time.sleep(0.05)
                pyautogui.keyUp('c')
                time.sleep(0.1)
                pyautogui.keyUp('ctrl')
                self._simulating_keys = False
                self._pressed_keys.clear()
                logger.debug("Used pyautogui for Ctrl+C simulation")
            else:
                self._simulating_keys = True
                keyboard_controller = keyboard.Controller()
                if platform.system() == 'Darwin':
                    keyboard_controller.press(keyboard.Key.cmd)
                    time.sleep(0.1)
                    keyboard_controller.press('c')
                    time.sleep(0.05)
                    keyboard_controller.release('c')
                    time.sleep(0.1)
                    keyboard_controller.release(keyboard.Key.cmd)
                else:
                    keyboard_controller.press(keyboard.Key.ctrl)
                    time.sleep(0.1)
                    keyboard_controller.press('c')
                    time.sleep(0.05)
                    keyboard_controller.release('c')
                    time.sleep(0.1)
                    keyboard_controller.release(keyboard.Key.ctrl)
                self._simulating_keys = False
                self._pressed_keys.clear()
                logger.debug("Used pynput for Ctrl+C simulation")
            time.sleep(0.3)
        except Exception as e:
            logger.error("Failed to simulate copy: %s", e)
            self._simulating_keys = False
            self._pressed_keys.clear()
    
    def _simulate_paste(self):
        """Simulate Ctrl+V using the most reliable method available."""
        try:
            if PYAUTOGUI_AVAILABLE:
                self._simulating_keys = True
                pyautogui.keyDown('ctrl')
                time.sleep(0.15)
                pyautogui.keyDown('v')
                time.sleep(0.1)
                pyautogui.keyUp('v')
                time.sleep(0.15)
                pyautogui.keyUp('ctrl')
                time.sleep(0.2)
                self._simulating_keys = False
                self._pressed_keys.clear()
                logger.debug("Used pyautogui for Ctrl+V simulation")
            elif WINDOWS_API_AVAILABLE:
                self._win_send_hotkey(VK_CONTROL, VK_V)
                logger.debug("Used Windows SendInput for Ctrl+V simulation")
            else:
                self._simulating_keys = True
                keyboard_controller = keyboard.Controller()
                if platform.system() == 'Darwin':
                    keyboard_controller.press(keyboard.Key.cmd)
                    time.sleep(0.1)
                    keyboard_controller.press('v')
                    time.sleep(0.05)
                    keyboard_controller.release('v')
                    time.sleep(0.1)
                    keyboard_controller.release(keyboard.Key.cmd)
                else:
                    keyboard_controller.press(keyboard.Key.ctrl)
                    time.sleep(0.1)
                    keyboard_controller.press('v')
                    time.sleep(0.05)
                    keyboard_controller.release('v')
                    time.sleep(0.1)
                    keyboard_controller.release(keyboard.Key.ctrl)
                self._simulating_keys = False
                self._pressed_keys.clear()
                logger.debug("Used pynput for Ctrl+V simulation")
            time.sleep(0.3)
        except Exception as e:
            logger.error("Failed to simulate paste: %s", e)
            self._simulating_keys = False
            self._pressed_keys.clear()
    
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
