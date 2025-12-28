"""
Settings Dialog UI
Configuration dialog for advanced settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config_manager import ConfigurationManager, Configuration


class SettingsDialog(QDialog):
    """Settings configuration dialog"""
    
    def __init__(self, config: Configuration, parent=None):
        super().__init__(parent)
        self._config = config
        self._config_manager = ConfigurationManager()
        
        self._setup_ui()
        self._load_values()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 450)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # ===== Hotkeys Section =====
        hotkey_group = QGroupBox("Hotkeys")
        hotkey_layout = QGridLayout()
        
        hotkey_layout.addWidget(QLabel("Start/Stop:"), 0, 0)
        self._toggle_hotkey = QLineEdit()
        self._toggle_hotkey.setPlaceholderText("e.g., ctrl+shift+s")
        hotkey_layout.addWidget(self._toggle_hotkey, 0, 1)
        
        hotkey_layout.addWidget(QLabel("Emergency Stop:"), 1, 0)
        self._stop_hotkey = QLineEdit()
        self._stop_hotkey.setPlaceholderText("e.g., escape")
        hotkey_layout.addWidget(self._stop_hotkey, 1, 1)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # ===== Safety Section =====
        safety_group = QGroupBox("Safety")
        safety_layout = QVBoxLayout()
        
        self._pause_minimize = QCheckBox("Pause when window minimized")
        self._confirm_start = QCheckBox("Confirm before starting")
        
        safety_layout.addWidget(self._pause_minimize)
        safety_layout.addWidget(self._confirm_start)
        
        safety_group.setLayout(safety_layout)
        layout.addWidget(safety_group)
        
        # ===== Behavior Section =====
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QGridLayout()
        
        self._start_minimized = QCheckBox("Start minimized to tray")
        self._auto_start = QCheckBox("Auto-start clicking on launch")
        
        behavior_layout.addWidget(self._start_minimized, 0, 0, 1, 2)
        behavior_layout.addWidget(self._auto_start, 1, 0, 1, 2)
        
        behavior_layout.addWidget(QLabel("Mouse Button:"), 2, 0)
        self._mouse_button = QComboBox()
        self._mouse_button.addItems(["Left Click", "Right Click", "Middle Click"])
        behavior_layout.addWidget(self._mouse_button, 2, 1)
        
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)
        
        # ===== Advanced Section =====
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QGridLayout()
        
        advanced_layout.addWidget(QLabel("Max Runtime (minutes):"), 0, 0)
        self._max_runtime = QSpinBox()
        self._max_runtime.setRange(0, 1440)  # Up to 24 hours
        self._max_runtime.setSpecialValueText("Unlimited")
        advanced_layout.addWidget(self._max_runtime, 0, 1)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # ===== Buttons =====
        button_layout = QHBoxLayout()
        
        self._save_btn = QPushButton("Save")
        self._cancel_btn = QPushButton("Cancel")
        self._defaults_btn = QPushButton("Defaults")
        
        button_layout.addStretch()
        button_layout.addWidget(self._save_btn)
        button_layout.addWidget(self._cancel_btn)
        button_layout.addWidget(self._defaults_btn)
        
        layout.addLayout(button_layout)
        
        # Apply dark theme
        self._apply_styles()
    
    def _apply_styles(self):
        """Apply visual styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
            }
            QGroupBox {
                font-weight: bold;
                color: #eee;
                border: 2px solid #4a4a6a;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #ddd;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #2a2a4a;
                color: #fff;
                border: 2px solid #4a4a6a;
                border-radius: 5px;
                padding: 6px;
            }
            QCheckBox {
                color: #ddd;
                spacing: 8px;
            }
            QPushButton {
                background-color: #3a3a5a;
                color: #fff;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4a4a7a;
            }
        """)
    
    def _load_values(self):
        """Load current config values into widgets"""
        self._toggle_hotkey.setText(self._config.hotkey_toggle)
        self._stop_hotkey.setText(self._config.hotkey_emergency_stop)
        self._pause_minimize.setChecked(self._config.pause_on_minimize)
        self._confirm_start.setChecked(self._config.confirm_before_start)
        self._start_minimized.setChecked(self._config.start_minimized)
        self._auto_start.setChecked(self._config.auto_start)
        self._max_runtime.setValue(self._config.max_runtime_minutes)
        
        # Mouse button
        button_map = {"left": 0, "right": 1, "middle": 2}
        self._mouse_button.setCurrentIndex(
            button_map.get(self._config.mouse_button, 0)
        )
    
    def _connect_signals(self):
        """Connect signals"""
        self._save_btn.clicked.connect(self._save)
        self._cancel_btn.clicked.connect(self.reject)
        self._defaults_btn.clicked.connect(self._reset_defaults)
    
    def _save(self):
        """Save settings"""
        # Update config
        self._config.hotkey_toggle = self._toggle_hotkey.text().strip() or "ctrl+shift+s"
        self._config.hotkey_emergency_stop = self._stop_hotkey.text().strip() or "escape"
        self._config.pause_on_minimize = self._pause_minimize.isChecked()
        self._config.confirm_before_start = self._confirm_start.isChecked()
        self._config.start_minimized = self._start_minimized.isChecked()
        self._config.auto_start = self._auto_start.isChecked()
        self._config.max_runtime_minutes = self._max_runtime.value()
        
        button_map = {0: "left", 1: "right", 2: "middle"}
        self._config.mouse_button = button_map.get(
            self._mouse_button.currentIndex(), "left"
        )
        
        # Save to file
        if self._config_manager.save_config(self._config):
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Failed to save settings."
            )
    
    def _reset_defaults(self):
        """Reset to default values"""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults?",
            "Reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            default = self._config_manager.get_default_config()
            self._config = default
            self._load_values()
