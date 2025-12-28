"""
Click Generator Module
Generates automated mouse clicks with configurable intervals and patterns.
"""

import threading
import time
import random
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
from pynput.mouse import Button, Controller as MouseController


class ClickPattern(Enum):
    """Click intensity patterns"""
    CONSTANT = "constant"      # Fixed interval between clicks
    RANDOM = "random"          # ±20% variance from base interval
    BURST = "burst"            # Groups of rapid clicks with pauses


@dataclass
class ClickConfig:
    """Configuration for click generation"""
    interval_ms: int = 200           # Base interval in milliseconds
    pattern: ClickPattern = ClickPattern.CONSTANT
    mouse_button: str = "left"       # left, right, or middle
    variation_percent: float = 20.0  # For RANDOM pattern
    burst_clicks: int = 5            # Clicks per burst
    burst_pause_ms: int = 1000       # Pause between bursts


class ClickGenerator:
    """
    Generates automated mouse clicks at configurable intervals.
    Uses pynput for cross-platform mouse control.
    """
    
    # Interval limits from PRD
    MIN_INTERVAL_MS = 50
    MAX_INTERVAL_MS = 10000
    DEFAULT_INTERVAL_MS = 200
    
    def __init__(self):
        self._mouse = MouseController()
        self._config = ClickConfig()
        self._clicking = False
        self._click_thread: Optional[threading.Thread] = None
        self._click_count = 0
        self._start_time: Optional[float] = None
        self._target_position: Optional[tuple[int, int]] = None
        self._on_click_callback: Optional[Callable[[int], None]] = None
        self._lock = threading.Lock()
    
    def start_clicking(
        self,
        interval_ms: Optional[int] = None,
        pattern: Optional[ClickPattern] = None,
        target_position: Optional[tuple[int, int]] = None
    ) -> bool:
        """
        Start automated clicking.
        
        Args:
            interval_ms: Click interval in milliseconds (50-10000)
            pattern: Click pattern (CONSTANT, RANDOM, or BURST)
            target_position: Optional (x, y) position to click at
            
        Returns:
            True if clicking started successfully
        """
        if self._clicking:
            return False
        
        # Update config if provided
        if interval_ms is not None:
            self.set_interval(interval_ms)
        if pattern is not None:
            self._config.pattern = pattern
        
        self._target_position = target_position
        self._clicking = True
        self._click_count = 0
        self._start_time = time.time()
        
        self._click_thread = threading.Thread(
            target=self._click_loop,
            daemon=True
        )
        self._click_thread.start()
        
        return True
    
    def stop_clicking(self) -> None:
        """Stop automated clicking immediately"""
        self._clicking = False
        if self._click_thread:
            self._click_thread.join(timeout=1.0)
            self._click_thread = None
    
    def set_interval(self, interval_ms: int) -> None:
        """Set the click interval, enforcing min/max limits"""
        with self._lock:
            self._config.interval_ms = max(
                self.MIN_INTERVAL_MS,
                min(self.MAX_INTERVAL_MS, interval_ms)
            )
    
    def set_pattern(self, pattern: ClickPattern) -> None:
        """Set the click pattern"""
        with self._lock:
            self._config.pattern = pattern
    
    def set_mouse_button(self, button: str) -> None:
        """Set the mouse button to click (left, right, middle)"""
        with self._lock:
            self._config.mouse_button = button.lower()
    
    def set_target_position(self, position: Optional[tuple[int, int]]) -> None:
        """Set the target click position"""
        self._target_position = position
    
    def on_click(self, callback: Callable[[int], None]) -> None:
        """Register callback for click events"""
        self._on_click_callback = callback
    
    def get_click_count(self) -> int:
        """Get total clicks since start"""
        return self._click_count
    
    def get_runtime_seconds(self) -> float:
        """Get runtime in seconds since clicking started"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time
    
    def get_current_interval(self) -> int:
        """Get the current effective interval (including any variation)"""
        return self._config.interval_ms
    
    @property
    def is_clicking(self) -> bool:
        """Check if currently clicking"""
        return self._clicking
    
    def _get_mouse_button(self) -> Button:
        """Get the pynput Button for the configured mouse button"""
        button_map = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
        }
        return button_map.get(self._config.mouse_button, Button.left)
    
    def _calculate_interval(self) -> float:
        """Calculate the next interval based on pattern"""
        base_interval = self._config.interval_ms / 1000.0  # Convert to seconds
        
        if self._config.pattern == ClickPattern.CONSTANT:
            return base_interval
        
        elif self._config.pattern == ClickPattern.RANDOM:
            # Add ±variation_percent variance
            variance = base_interval * (self._config.variation_percent / 100.0)
            return base_interval + random.uniform(-variance, variance)
        
        elif self._config.pattern == ClickPattern.BURST:
            # Burst mode handled in click loop
            return base_interval
        
        return base_interval
    
    def _perform_click(self) -> None:
        """Perform a single mouse click"""
        button = self._get_mouse_button()
        
        # Move to target position if specified
        if self._target_position:
            self._mouse.position = self._target_position
        
        # Click
        self._mouse.click(button)
        
        with self._lock:
            self._click_count += 1
        
        # Notify callback
        if self._on_click_callback:
            try:
                self._on_click_callback(self._click_count)
            except Exception as e:
                print(f"Error in click callback: {e}")
    
    def _click_loop(self) -> None:
        """Main clicking loop running in background thread"""
        while self._clicking:
            if self._config.pattern == ClickPattern.BURST:
                # Burst mode: rapid clicks followed by pause
                for _ in range(self._config.burst_clicks):
                    if not self._clicking:
                        break
                    self._perform_click()
                    time.sleep(0.05)  # Rapid 50ms between burst clicks
                
                if self._clicking:
                    time.sleep(self._config.burst_pause_ms / 1000.0)
            else:
                # Normal click
                self._perform_click()
                interval = self._calculate_interval()
                
                # Sleep in small increments to allow quick stopping
                sleep_remaining = interval
                while sleep_remaining > 0 and self._clicking:
                    sleep_time = min(0.05, sleep_remaining)
                    time.sleep(sleep_time)
                    sleep_remaining -= sleep_time
    
    def reset_stats(self) -> None:
        """Reset click count and runtime"""
        with self._lock:
            self._click_count = 0
            self._start_time = time.time() if self._clicking else None


# Preset configurations
PRESET_SLOW = ClickConfig(interval_ms=500, pattern=ClickPattern.CONSTANT)
PRESET_MEDIUM = ClickConfig(interval_ms=250, pattern=ClickPattern.CONSTANT)
PRESET_FAST = ClickConfig(interval_ms=100, pattern=ClickPattern.CONSTANT)


# For testing
if __name__ == "__main__":
    print("Click Generator Test")
    print("Will click 10 times at 500ms interval at current mouse position")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    generator = ClickGenerator()
    generator.on_click(lambda count: print(f"Click #{count}"))
    
    generator.start_clicking(interval_ms=500, pattern=ClickPattern.RANDOM)
    
    # Let it run for 5 seconds
    time.sleep(5)
    
    generator.stop_clicking()
    print(f"\nTotal clicks: {generator.get_click_count()}")
    print(f"Runtime: {generator.get_runtime_seconds():.2f} seconds")
