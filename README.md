# DisplayMode

A simple Python application designed to manage display modes, likely for automation or quick switching of display settings.

## Files

- `main.py`: The core Python script that contains the application's logic.
- `hotkeys.json`: Configuration file for defining hotkeys used by the application.
- `icon.png`: The application icon.
- `run.bat`: A batch script to run the `main.py` in the background without opening a new command prompt window.
- `run_debug.bat`: A batch script to run the `main.py` directly, useful for debugging.
- `run_venv.bat`: A batch script to run the application using a Python virtual environment.
- `setup_venv.bat`: A batch script to set up a Python virtual environment with all required dependencies.
- `requirements.txt`: Lists all Python dependencies required by the application.
- `.gitignore`: Specifies intentionally untracked files that Git should ignore.

## Installation (Recommended)

1. **Set up the virtual environment** (only needs to be done once):
   ```bash
   setup_venv.bat
   ```

2. **Run the application**:
   ```bash
   run.bat
   ```

## How to Run

### Standard Usage (Headless)
To run the application in the background (no console window):
```bash
run.bat
```

### Debug Mode
To run the application with console output for debugging:
```bash
run_debug.bat
```

### Alternative: System Python
If you prefer to use system Python instead of virtual environment:
```bash
pip install -r requirements.txt
pythonw main.py  # headless
# or
python main.py   # with console
```

## Dependencies

- `keyboard`: For global hotkey functionality
- `pystray`: For system tray icon
- `Pillow`: For image handling
- `pywin32`: For Windows registry access
