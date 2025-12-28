"""
Window Detector Module
Detects and tracks Roblox game windows, specifically "The Forge" game.
"""

import re
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Callable
import threading
import time


@dataclass
class WindowHandle:
    """Represents a window handle with metadata"""
    window_id: str
    title: str
    process_name: str
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class Rectangle:
    """Represents a window rectangle"""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


class WindowDetector:
    """
    Detects and manages Roblox window references.
    Currently supports Linux/X11 using wmctrl and xdotool.
    """
    
    # Window title patterns to match Roblox and The Forge
    ROBLOX_PATTERNS = [
        r"Roblox",
        r"The Forge",
        r".*Roblox.*",
    ]
    
    def __init__(self):
        self._current_window: Optional[WindowHandle] = None
        self._state_callbacks: List[Callable[[bool], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitoring = False
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check if required system tools are available"""
        try:
            subprocess.run(["wmctrl", "-l"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: wmctrl not found. Install with: sudo apt install wmctrl")
        
        try:
            subprocess.run(["xdotool", "version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: xdotool not found. Install with: sudo apt install xdotool")
    
    def find_roblox_window(self) -> Optional[WindowHandle]:
        """
        Find the Roblox window, preferring "The Forge" game window.
        Returns the WindowHandle if found, None otherwise.
        """
        windows = self._enumerate_windows()
        
        # First, try to find "The Forge" specifically
        for window in windows:
            if "The Forge" in window.title or "forge" in window.title.lower():
                self._current_window = window
                self._update_window_geometry(window)
                return window
        
        # Fallback to any Roblox window
        for window in windows:
            for pattern in self.ROBLOX_PATTERNS:
                if re.search(pattern, window.title, re.IGNORECASE):
                    self._current_window = window
                    self._update_window_geometry(window)
                    return window
        
        self._current_window = None
        return None
    
    def _enumerate_windows(self) -> List[WindowHandle]:
        """Enumerate all windows using wmctrl"""
        windows = []
        try:
            result = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                # wmctrl output format: WINDOW_ID DESKTOP HOST TITLE
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    window_id, desktop, host, title = parts[0], parts[1], parts[2], parts[3]
                    windows.append(WindowHandle(
                        window_id=window_id,
                        title=title,
                        process_name=host
                    ))
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error enumerating windows: {e}")
        
        return windows
    
    def _update_window_geometry(self, window: WindowHandle) -> None:
        """Update window geometry using xdotool"""
        try:
            result = subprocess.run(
                ["xdotool", "getwindowgeometry", "--shell", window.window_id],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if line.startswith("X="):
                    window.x = int(line.split("=")[1])
                elif line.startswith("Y="):
                    window.y = int(line.split("=")[1])
                elif line.startswith("WIDTH="):
                    window.width = int(line.split("=")[1])
                elif line.startswith("HEIGHT="):
                    window.height = int(line.split("=")[1])
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
            print(f"Error getting window geometry: {e}")
    
    def is_window_valid(self, handle: Optional[WindowHandle] = None) -> bool:
        """Check if the window handle is still valid"""
        target = handle or self._current_window
        if not target:
            return False
        
        try:
            # Try to get window info - will fail if window doesn't exist
            result = subprocess.run(
                ["xdotool", "getwindowname", target.window_id],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_window_rect(self, handle: Optional[WindowHandle] = None) -> Optional[Rectangle]:
        """Get the current window rectangle"""
        target = handle or self._current_window
        if not target:
            return None
        
        self._update_window_geometry(target)
        return Rectangle(
            x=target.x,
            y=target.y,
            width=target.width,
            height=target.height
        )
    
    def get_click_position(self) -> Optional[tuple[int, int]]:
        """Get the center position of the target window for clicking"""
        rect = self.get_window_rect()
        if rect:
            return rect.center
        return None
    
    def on_window_state_changed(self, callback: Callable[[bool], None]) -> None:
        """Register a callback for window state changes"""
        self._state_callbacks.append(callback)
    
    def start_monitoring(self, interval_seconds: float = 1.0) -> None:
        """Start monitoring window state in background"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring window state"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None
    
    def _monitor_loop(self, interval: float) -> None:
        """Background thread that monitors window state"""
        was_valid = self.is_window_valid()
        
        while self._monitoring:
            is_valid = self.is_window_valid()
            
            if is_valid != was_valid:
                for callback in self._state_callbacks:
                    try:
                        callback(is_valid)
                    except Exception as e:
                        print(f"Error in window state callback: {e}")
                was_valid = is_valid
            
            # If window became invalid, try to find it again
            if not is_valid:
                self.find_roblox_window()
                is_valid = self.is_window_valid()
                if is_valid and not was_valid:
                    for callback in self._state_callbacks:
                        try:
                            callback(True)
                        except Exception as e:
                            print(f"Error in window state callback: {e}")
                    was_valid = True
            
            time.sleep(interval)
    
    @property
    def current_window(self) -> Optional[WindowHandle]:
        """Get the currently tracked window"""
        return self._current_window
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to a valid Roblox window"""
        return self._current_window is not None and self.is_window_valid()


# For testing
if __name__ == "__main__":
    detector = WindowDetector()
    window = detector.find_roblox_window()
    
    if window:
        print(f"Found window: {window.title}")
        print(f"Window ID: {window.window_id}")
        rect = detector.get_window_rect()
        if rect:
            print(f"Position: ({rect.x}, {rect.y})")
            print(f"Size: {rect.width}x{rect.height}")
            print(f"Center: {rect.center}")
    else:
        print("No Roblox window found")
        print("\nAll windows:")
        for w in detector._enumerate_windows():
            print(f"  - {w.title}")
