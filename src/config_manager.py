"""
Configuration Manager Module
Handles loading, saving, and validating user configuration.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


@dataclass
class Configuration:
    """Application configuration settings"""
    click_interval_ms: int = 200
    intensity_pattern: str = "constant"  # constant, random, burst
    mouse_button: str = "left"           # left, right, middle
    hotkey_toggle: str = "ctrl+shift+s"
    hotkey_emergency_stop: str = "escape"
    pause_on_minimize: bool = True
    confirm_before_start: bool = True
    start_minimized: bool = False
    auto_start: bool = False
    max_runtime_minutes: int = 0         # 0 = unlimited


class ConfigurationManager:
    """
    Manages application configuration with JSON persistence.
    Stores config in ~/.config/forge-autoclicker/config.json
    """
    
    # Validation limits
    MIN_INTERVAL_MS = 50
    MAX_INTERVAL_MS = 10000
    VALID_PATTERNS = ["constant", "random", "burst"]
    VALID_BUTTONS = ["left", "right", "middle"]
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Optional custom config directory path
        """
        if config_dir:
            self._config_dir = Path(config_dir)
        else:
            self._config_dir = Path.home() / ".config" / "forge-autoclicker"
        
        self._config_file = self._config_dir / "config.json"
        self._config: Configuration = self.get_default_config()
    
    def load_config(self) -> Configuration:
        """
        Load configuration from file.
        Creates default config if file doesn't exist.
        
        Returns:
            Loaded Configuration object
        """
        if not self._config_file.exists():
            # Load from default config bundled with app
            default_path = Path(__file__).parent.parent / "config" / "default_config.json"
            if default_path.exists():
                try:
                    with open(default_path, 'r') as f:
                        data = json.load(f)
                        self._config = Configuration(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Error loading default config: {e}")
                    self._config = self.get_default_config()
            else:
                self._config = self.get_default_config()
            
            # Save to user config location
            self.save_config(self._config)
            return self._config
        
        try:
            with open(self._config_file, 'r') as f:
                data = json.load(f)
                self._config = Configuration(**data)
                
                # Validate and fix if needed
                if not self.validate_config(self._config):
                    self._config = self._fix_invalid_config(self._config)
                    self.save_config(self._config)
                
                return self._config
        except (json.JSONDecodeError, TypeError, FileNotFoundError) as e:
            print(f"Error loading config: {e}")
            self._config = self.get_default_config()
            return self._config
    
    def save_config(self, config: Configuration) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: Configuration to save
            
        Returns:
            True if saved successfully
        """
        try:
            # Ensure directory exists
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self._config_file, 'w') as f:
                json.dump(asdict(config), f, indent=4)
            
            self._config = config
            return True
        except (OSError, IOError) as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_default_config(self) -> Configuration:
        """Get default configuration"""
        return Configuration()
    
    def validate_config(self, config: Configuration) -> bool:
        """
        Validate configuration values.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if all values are valid
        """
        # Check interval limits
        if not (self.MIN_INTERVAL_MS <= config.click_interval_ms <= self.MAX_INTERVAL_MS):
            return False
        
        # Check pattern
        if config.intensity_pattern not in self.VALID_PATTERNS:
            return False
        
        # Check mouse button
        if config.mouse_button not in self.VALID_BUTTONS:
            return False
        
        # Check max runtime
        if config.max_runtime_minutes < 0:
            return False
        
        return True
    
    def _fix_invalid_config(self, config: Configuration) -> Configuration:
        """Fix invalid configuration values"""
        # Fix interval
        config.click_interval_ms = max(
            self.MIN_INTERVAL_MS,
            min(self.MAX_INTERVAL_MS, config.click_interval_ms)
        )
        
        # Fix pattern
        if config.intensity_pattern not in self.VALID_PATTERNS:
            config.intensity_pattern = "constant"
        
        # Fix mouse button
        if config.mouse_button not in self.VALID_BUTTONS:
            config.mouse_button = "left"
        
        # Fix max runtime
        if config.max_runtime_minutes < 0:
            config.max_runtime_minutes = 0
        
        return config
    
    @property
    def current_config(self) -> Configuration:
        """Get the current configuration"""
        return self._config
    
    def update_interval(self, interval_ms: int) -> None:
        """Update and save click interval"""
        self._config.click_interval_ms = max(
            self.MIN_INTERVAL_MS,
            min(self.MAX_INTERVAL_MS, interval_ms)
        )
        self.save_config(self._config)
    
    def update_pattern(self, pattern: str) -> None:
        """Update and save intensity pattern"""
        if pattern in self.VALID_PATTERNS:
            self._config.intensity_pattern = pattern
            self.save_config(self._config)
    
    def update_mouse_button(self, button: str) -> None:
        """Update and save mouse button"""
        if button in self.VALID_BUTTONS:
            self._config.mouse_button = button
            self.save_config(self._config)


# For testing
if __name__ == "__main__":
    manager = ConfigurationManager()
    config = manager.load_config()
    
    print("Current configuration:")
    print(f"  Interval: {config.click_interval_ms}ms")
    print(f"  Pattern: {config.intensity_pattern}")
    print(f"  Button: {config.mouse_button}")
    print(f"  Toggle hotkey: {config.hotkey_toggle}")
    print(f"  Emergency stop: {config.hotkey_emergency_stop}")
    print(f"  Pause on minimize: {config.pause_on_minimize}")
    print(f"  Confirm before start: {config.confirm_before_start}")
    
    # Test save
    config.click_interval_ms = 300
    manager.save_config(config)
    print("\nUpdated interval to 300ms and saved.")
