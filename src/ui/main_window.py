"""
Main Window UI
The primary application window with auto-clicker controls.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSpinBox, QRadioButton, QButtonGroup,
    QGroupBox, QFrame, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from window_detector import WindowDetector
from click_generator import ClickGenerator, ClickPattern
from config_manager import ConfigurationManager, Configuration
from hotkey_manager import HotkeyManager


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signal for thread-safe UI updates
    click_updated = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        # Initialize modules
        self._window_detector = WindowDetector()
        self._click_generator = ClickGenerator()
        self._config_manager = ConfigurationManager()
        self._hotkey_manager = HotkeyManager()
        
        # Load configuration
        self._config = self._config_manager.load_config()
        
        # State
        self._is_clicking = False
        self._start_time = None
        
        # Setup UI
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._apply_styles()
        self._connect_signals()
        self._setup_timers()
        self._setup_hotkeys()
        
        # Initial window detection
        self._detect_window()
    
    def _setup_window(self):
        """Configure main window properties"""
        self.setWindowTitle("The Forge Auto-Clicker")
        self.setFixedSize(420, 520)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Central widget
        self._central = QWidget()
        self.setCentralWidget(self._central)
        
        # ===== Target Window Section =====
        self._window_group = QGroupBox("Target Window Status")
        self._window_status_indicator = QLabel("●")
        self._window_status_indicator.setFont(QFont("Segoe UI", 16))
        self._window_status_label = QLabel("Searching for Roblox...")
        self._window_status_label.setFont(QFont("Segoe UI", 10))
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.setFixedWidth(80)
        
        # ===== Click Interval Section =====
        self._interval_group = QGroupBox("Click Interval (ms)")
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(50, 10000)
        self._interval_spin.setValue(self._config.click_interval_ms)
        self._interval_spin.setSingleStep(10)
        self._interval_spin.setFont(QFont("Segoe UI", 12))
        
        # Preset buttons
        self._slow_btn = QPushButton("Slow (500ms)")
        self._medium_btn = QPushButton("Medium (250ms)")
        self._fast_btn = QPushButton("Fast (100ms)")
        
        # ===== Intensity Pattern Section =====
        self._pattern_group = QGroupBox("Intensity Pattern")
        self._pattern_constant = QRadioButton("Constant")
        self._pattern_random = QRadioButton("Random (±20%)")
        self._pattern_burst = QRadioButton("Burst Mode")
        
        self._pattern_button_group = QButtonGroup()
        self._pattern_button_group.addButton(self._pattern_constant, 0)
        self._pattern_button_group.addButton(self._pattern_random, 1)
        self._pattern_button_group.addButton(self._pattern_burst, 2)
        
        # Set initial selection
        pattern_map = {"constant": 0, "random": 1, "burst": 2}
        initial_pattern = pattern_map.get(self._config.intensity_pattern, 0)
        self._pattern_button_group.button(initial_pattern).setChecked(True)
        
        # ===== Start/Stop Button =====
        self._toggle_btn = QPushButton("START CLICKING")
        self._toggle_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._toggle_btn.setMinimumHeight(60)
        
        # ===== Statistics Section =====
        self._stats_group = QGroupBox("Statistics")
        self._clicks_label = QLabel("Total Clicks: 0")
        self._runtime_label = QLabel("Active Time: 00:00:00")
        self._interval_display = QLabel(f"Current Interval: {self._config.click_interval_ms}ms")
        
        # ===== Bottom Buttons =====
        self._settings_btn = QPushButton("Settings")
        self._about_btn = QPushButton("About")
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready - Press Ctrl+Shift+S to toggle")
    
    def _setup_layout(self):
        """Arrange widgets in layouts"""
        main_layout = QVBoxLayout(self._central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Target Window Section
        window_layout = QHBoxLayout()
        window_layout.addWidget(self._window_status_indicator)
        window_layout.addWidget(self._window_status_label, 1)
        window_layout.addWidget(self._refresh_btn)
        self._window_group.setLayout(window_layout)
        main_layout.addWidget(self._window_group)
        
        # Click Interval Section
        interval_layout = QVBoxLayout()
        interval_layout.addWidget(self._interval_spin)
        
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(self._slow_btn)
        preset_layout.addWidget(self._medium_btn)
        preset_layout.addWidget(self._fast_btn)
        interval_layout.addLayout(preset_layout)
        self._interval_group.setLayout(interval_layout)
        main_layout.addWidget(self._interval_group)
        
        # Intensity Pattern Section
        pattern_layout = QHBoxLayout()
        pattern_layout.addWidget(self._pattern_constant)
        pattern_layout.addWidget(self._pattern_random)
        pattern_layout.addWidget(self._pattern_burst)
        self._pattern_group.setLayout(pattern_layout)
        main_layout.addWidget(self._pattern_group)
        
        # Start/Stop Button
        main_layout.addWidget(self._toggle_btn)
        
        # Statistics Section
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(self._clicks_label)
        stats_layout.addWidget(self._runtime_label)
        stats_layout.addWidget(self._interval_display)
        self._stats_group.setLayout(stats_layout)
        main_layout.addWidget(self._stats_group)
        
        # Bottom Buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(self._settings_btn)
        bottom_layout.addWidget(self._about_btn)
        main_layout.addLayout(bottom_layout)
    
    def _apply_styles(self):
        """Apply visual styling"""
        self.setStyleSheet("""
            QMainWindow {
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
            QPushButton {
                background-color: #3a3a5a;
                color: #fff;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4a4a7a;
            }
            QPushButton:pressed {
                background-color: #2a2a4a;
            }
            QPushButton#toggle_active {
                background-color: #e74c3c;
            }
            QPushButton#toggle_inactive {
                background-color: #27ae60;
            }
            QSpinBox {
                background-color: #2a2a4a;
                color: #fff;
                border: 2px solid #4a4a6a;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
            }
            QRadioButton {
                color: #ddd;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QStatusBar {
                background-color: #0f0f1a;
                color: #888;
            }
        """)
        
        # Set initial toggle button style
        self._update_toggle_button_style()
    
    def _update_toggle_button_style(self):
        """Update toggle button appearance based on state"""
        if self._is_clicking:
            self._toggle_btn.setText("STOP CLICKING")
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
        else:
            self._toggle_btn.setText("START CLICKING")
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #219a52;
                }
            """)
    
    def _update_window_status(self, connected: bool, title: str = ""):
        """Update window connection status display"""
        if connected:
            self._window_status_indicator.setText("●")
            self._window_status_indicator.setStyleSheet("color: #27ae60;")
            self._window_status_label.setText(f"Connected to: {title}")
        else:
            self._window_status_indicator.setText("○")
            self._window_status_indicator.setStyleSheet("color: #e74c3c;")
            self._window_status_label.setText("Window Not Found")
    
    def _connect_signals(self):
        """Connect widget signals to slots"""
        self._toggle_btn.clicked.connect(self._on_toggle_clicked)
        self._refresh_btn.clicked.connect(self._detect_window)
        
        # Preset buttons
        self._slow_btn.clicked.connect(lambda: self._set_interval(500))
        self._medium_btn.clicked.connect(lambda: self._set_interval(250))
        self._fast_btn.clicked.connect(lambda: self._set_interval(100))
        
        # Interval change
        self._interval_spin.valueChanged.connect(self._on_interval_changed)
        
        # Pattern change
        self._pattern_button_group.buttonClicked.connect(self._on_pattern_changed)
        
        # Settings and About
        self._settings_btn.clicked.connect(self._show_settings)
        self._about_btn.clicked.connect(self._show_about)
        
        # Click updates (thread-safe)
        self.click_updated.connect(self._on_click_updated)
        self._click_generator.on_click(lambda count: self.click_updated.emit(count))
    
    def _setup_timers(self):
        """Setup update timers"""
        # Statistics update timer
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._update_stats)
        self._stats_timer.start(100)  # Update every 100ms
        
        # Window detection timer
        self._window_timer = QTimer()
        self._window_timer.timeout.connect(self._detect_window)
        self._window_timer.start(5000)  # Check every 5 seconds
    
    def _setup_hotkeys(self):
        """Setup global hotkeys"""
        self._hotkey_manager.register_hotkey(
            self._config.hotkey_toggle,
            self._on_toggle_clicked
        )
        self._hotkey_manager.register_hotkey(
            self._config.hotkey_emergency_stop,
            self._emergency_stop
        )
        self._hotkey_manager.start()
    
    def _detect_window(self):
        """Detect Roblox window"""
        window = self._window_detector.find_roblox_window()
        if window:
            self._update_window_status(True, window.title)
        else:
            self._update_window_status(False)
    
    def _on_toggle_clicked(self):
        """Handle start/stop toggle"""
        if self._is_clicking:
            self._stop_clicking()
        else:
            self._start_clicking()
    
    def _start_clicking(self):
        """Start auto-clicking"""
        # Check for confirmation
        if self._config.confirm_before_start:
            reply = QMessageBox.question(
                self,
                "Start Auto-Clicking?",
                "Are you sure you want to start auto-clicking?\n\n"
                "⚠️ This may violate Roblox Terms of Service.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Get target position from Roblox window
        target_pos = self._window_detector.get_click_position()
        
        # Get current pattern
        pattern_map = {
            0: ClickPattern.CONSTANT,
            1: ClickPattern.RANDOM,
            2: ClickPattern.BURST
        }
        pattern = pattern_map.get(
            self._pattern_button_group.checkedId(),
            ClickPattern.CONSTANT
        )
        
        # Start clicking
        self._click_generator.start_clicking(
            interval_ms=self._interval_spin.value(),
            pattern=pattern,
            target_position=target_pos
        )
        
        self._is_clicking = True
        self._update_toggle_button_style()
        self._status_bar.showMessage("Auto-clicking active - Press ESC to stop")
    
    def _stop_clicking(self):
        """Stop auto-clicking"""
        self._click_generator.stop_clicking()
        self._is_clicking = False
        self._update_toggle_button_style()
        self._status_bar.showMessage("Stopped")
    
    def _emergency_stop(self):
        """Emergency stop - called by hotkey"""
        if self._is_clicking:
            self._stop_clicking()
            self._status_bar.showMessage("Emergency stop activated!")
    
    def _set_interval(self, value: int):
        """Set interval from preset button"""
        self._interval_spin.setValue(value)
    
    def _on_interval_changed(self, value: int):
        """Handle interval change"""
        self._click_generator.set_interval(value)
        self._config.click_interval_ms = value
        self._config_manager.save_config(self._config)
        self._interval_display.setText(f"Current Interval: {value}ms")
    
    def _on_pattern_changed(self, button):
        """Handle pattern change"""
        pattern_map = {
            0: (ClickPattern.CONSTANT, "constant"),
            1: (ClickPattern.RANDOM, "random"),
            2: (ClickPattern.BURST, "burst")
        }
        button_id = self._pattern_button_group.id(button)
        if button_id in pattern_map:
            pattern, name = pattern_map[button_id]
            self._click_generator.set_pattern(pattern)
            self._config.intensity_pattern = name
            self._config_manager.save_config(self._config)
    
    def _on_click_updated(self, count: int):
        """Update click count (called from signal)"""
        self._clicks_label.setText(f"Total Clicks: {count:,}")
    
    def _update_stats(self):
        """Update statistics display"""
        if self._is_clicking:
            runtime = self._click_generator.get_runtime_seconds()
            hours = int(runtime // 3600)
            minutes = int((runtime % 3600) // 60)
            seconds = int(runtime % 60)
            self._runtime_label.setText(f"Active Time: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def _show_settings(self):
        """Show settings dialog"""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self._config, self)
        if dialog.exec():
            # Reload config
            self._config = self._config_manager.load_config()
            self._setup_hotkeys()
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About The Forge Auto-Clicker",
            "<h3>The Forge Auto-Clicker v1.0</h3>"
            "<p>A cross-platform automated clicking utility for "
            "\"The Forge\" Roblox game.</p>"
            "<p><b>⚠️ Disclaimer:</b> This tool may violate Roblox's "
            "Terms of Service. Use at your own risk.</p>"
            "<p><b>Hotkeys:</b></p>"
            "<ul>"
            "<li>Ctrl+Shift+S: Toggle clicking</li>"
            "<li>Escape: Emergency stop</li>"
            "</ul>"
        )
    
    def closeEvent(self, event):
        """Handle window close"""
        # Stop clicking
        if self._is_clicking:
            self._stop_clicking()
        
        # Stop hotkey listener
        self._hotkey_manager.stop()
        
        # Stop timers
        self._stats_timer.stop()
        self._window_timer.stop()
        
        event.accept()
