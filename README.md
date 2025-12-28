# The Forge Auto-Clicker

A cross-platform automated clicking utility for "The Forge" Roblox game.

## ⚠️ Disclaimer

This tool automates mouse clicks which may violate Roblox's Terms of Service. Use at your own risk.

## Features

- 🎯 Automatic Roblox window detection
- ⏱️ Configurable click intervals (50ms - 10,000ms)
- 🎲 Click patterns: Constant, Random (±20% variance), Burst mode
- ⌨️ Global hotkeys for start/stop control
- 🛡️ Safety features: emergency stop, pause on minimize
- 📊 Real-time statistics display

## Requirements

- Python 3.10+

### Platform-Specific

| Platform                  | Additional Requirements           |
| ------------------------- | --------------------------------- |
| **Linux (Ubuntu 22.04+)** | `wmctrl`, `xdotool`               |
| **Windows 11**            | None (uses Win32 API via pywin32) |

---

## Installation & Usage

### 🐧 Linux (Ubuntu)

```bash
# Install system dependencies
sudo apt install wmctrl xdotool

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run
python run.py
```

### 🪟 Windows 11

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Run
python run.py
```

#### Building Windows Executable (.exe)

```powershell
# Install PyInstaller
pip install pyinstaller

# Build single-file executable
pyinstaller --onefile --windowed --name "ForgeAutoClicker" --icon=icon.ico run.py

# Output: dist/ForgeAutoClicker.exe
```

> **Note**: For Windows, you may need to add `pywin32` to requirements.txt for native window detection:
>
> ```
> pip install pywin32
> ```

---

## Hotkeys

| Key            | Action               |
| -------------- | -------------------- |
| `Ctrl+Shift+S` | Toggle auto-clicking |
| `Escape`       | Emergency stop       |

## Configuration

Settings are saved to:

- **Linux**: `~/.config/forge-autoclicker/config.json`
- **Windows**: `%APPDATA%\forge-autoclicker\config.json`

## License

For personal use only.
