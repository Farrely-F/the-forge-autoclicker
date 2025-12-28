"""
Hotkey Manager Module
Handles global keyboard shortcuts for controlling the auto-clicker.
"""

import threading
from typing import Dict, Callable, Optional, Set
from pynput import keyboard


class HotkeyManager:
    """
    Manages global hotkeys for the application.
    Uses pynput for cross-platform keyboard monitoring.
    """
    
    def __init__(self):
        self._hotkeys: Dict[frozenset, Callable] = {}  # key_set -> callback
        self._pressed_keys: Set[keyboard.Key | keyboard.KeyCode] = set()
        self._listener: Optional[keyboard.Listener] = None
        self._running = False
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """Start listening for hotkeys"""
        if self._running:
            return
        
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._listener.start()
    
    def stop(self) -> None:
        """Stop listening for hotkeys"""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._pressed_keys.clear()
    
    def register_hotkey(self, key_combination: str, callback: Callable) -> bool:
        """
        Register a hotkey combination.
        
        Args:
            key_combination: Key combo like "ctrl+shift+s" or "escape"
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if registered successfully
        """
        try:
            key_set = self._parse_key_combination(key_combination)
            with self._lock:
                self._hotkeys[key_set] = callback
            return True
        except ValueError as e:
            print(f"Error registering hotkey '{key_combination}': {e}")
            return False
    
    def unregister_hotkey(self, key_combination: str) -> bool:
        """
        Unregister a hotkey combination.
        
        Args:
            key_combination: Key combo to unregister
            
        Returns:
            True if unregistered successfully
        """
        try:
            key_set = self._parse_key_combination(key_combination)
            with self._lock:
                if key_set in self._hotkeys:
                    del self._hotkeys[key_set]
                    return True
            return False
        except ValueError:
            return False
    
    def is_hotkey_available(self, key_combination: str) -> bool:
        """
        Check if a hotkey combination is available.
        
        Args:
            key_combination: Key combo to check
            
        Returns:
            True if the hotkey is not already registered
        """
        try:
            key_set = self._parse_key_combination(key_combination)
            with self._lock:
                return key_set not in self._hotkeys
        except ValueError:
            return False
    
    def _parse_key_combination(self, combo: str) -> frozenset:
        """
        Parse a key combination string into a set of keys.
        
        Args:
            combo: Key combo like "ctrl+shift+s"
            
        Returns:
            Frozenset of pynput Key/KeyCode objects
        """
        keys = set()
        parts = combo.lower().replace(" ", "").split("+")
        
        key_mapping = {
            # Modifiers
            "ctrl": keyboard.Key.ctrl_l,
            "control": keyboard.Key.ctrl_l,
            "shift": keyboard.Key.shift,
            "alt": keyboard.Key.alt_l,
            "cmd": keyboard.Key.cmd,
            "command": keyboard.Key.cmd,
            # Special keys
            "escape": keyboard.Key.esc,
            "esc": keyboard.Key.esc,
            "space": keyboard.Key.space,
            "enter": keyboard.Key.enter,
            "return": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "backspace": keyboard.Key.backspace,
            "delete": keyboard.Key.delete,
            "home": keyboard.Key.home,
            "end": keyboard.Key.end,
            "pageup": keyboard.Key.page_up,
            "pagedown": keyboard.Key.page_down,
            "up": keyboard.Key.up,
            "down": keyboard.Key.down,
            "left": keyboard.Key.left,
            "right": keyboard.Key.right,
            # Function keys
            "f1": keyboard.Key.f1,
            "f2": keyboard.Key.f2,
            "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4,
            "f5": keyboard.Key.f5,
            "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7,
            "f8": keyboard.Key.f8,
            "f9": keyboard.Key.f9,
            "f10": keyboard.Key.f10,
            "f11": keyboard.Key.f11,
            "f12": keyboard.Key.f12,
        }
        
        for part in parts:
            if part in key_mapping:
                keys.add(key_mapping[part])
            elif len(part) == 1:
                keys.add(keyboard.KeyCode.from_char(part))
            else:
                raise ValueError(f"Unknown key: {part}")
        
        return frozenset(keys)
    
    def _normalize_key(self, key) -> keyboard.Key | keyboard.KeyCode:
        """Normalize key to handle left/right variants"""
        # Map right-side modifiers to left-side
        key_mapping = {
            keyboard.Key.ctrl_r: keyboard.Key.ctrl_l,
            keyboard.Key.shift_r: keyboard.Key.shift,
            keyboard.Key.alt_r: keyboard.Key.alt_l,
            keyboard.Key.cmd_r: keyboard.Key.cmd,
        }
        
        if hasattr(key, 'name'):
            return key_mapping.get(key, key)
        return key
    
    def _on_key_press(self, key) -> None:
        """Handle key press events"""
        normalized = self._normalize_key(key)
        self._pressed_keys.add(normalized)
        
        # Check if any registered hotkey matches
        current_keys = frozenset(self._pressed_keys)
        with self._lock:
            for hotkey_set, callback in self._hotkeys.items():
                if hotkey_set == current_keys:
                    try:
                        callback()
                    except Exception as e:
                        print(f"Error in hotkey callback: {e}")
                    break
    
    def _on_key_release(self, key) -> None:
        """Handle key release events"""
        normalized = self._normalize_key(key)
        self._pressed_keys.discard(normalized)


# For testing
if __name__ == "__main__":
    print("Hotkey Manager Test")
    print("Press Ctrl+Shift+S to toggle, Escape to stop")
    print("Running for 30 seconds...")
    
    manager = HotkeyManager()
    
    def on_toggle():
        print("Toggle hotkey pressed!")
    
    def on_emergency():
        print("Emergency stop pressed!")
        manager.stop()
    
    manager.register_hotkey("ctrl+shift+s", on_toggle)
    manager.register_hotkey("escape", on_emergency)
    manager.start()
    
    import time
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    
    manager.stop()
    print("Done.")
