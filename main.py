
import tkinter as tk
from tkinter import ttk
import subprocess
import keyboard
import json
import os
import winreg
from pystray import MenuItem as item
import pystray
from PIL import Image, ImageDraw, ImageTk
import threading
import win32event
import win32api
import sys

APP_NAME = "DisplayMode"
# Get the absolute path of the script
APP_PATH = os.path.abspath(os.path.dirname(__file__))
# Construct the full path to the batch file
BAT_PATH = os.path.join(APP_PATH, "run.bat")
ICON_PATH = os.path.join(APP_PATH, "icon.png")


class DisplayModeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DisplayMode Settings")
        self.geometry("400x350")
        self.hotkeys = {}
        self.listening_entry = None # To keep track of which entry is listening
        self.current_hook = None # Initialize current_hook
        self.create_widgets()
        self.load_hotkeys()
        self.register_hotkeys()
        self.check_startup()
        # Hide the window when the close button is pressed
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        # Set the taskbar icon
        print("Attempting to set taskbar icon...")
        try:
            # Use the same image object created for the pystray icon
            # Ensure the image is kept as an instance variable to prevent garbage collection
            self.taskbar_icon_image = Image.open(ICON_PATH) if os.path.exists(ICON_PATH) else create_image()
            print(f"Taskbar icon image loaded: {self.taskbar_icon_image}")
            self.taskbar_icon_photo = ImageTk.PhotoImage(self.taskbar_icon_image)
            print(f"Taskbar icon PhotoImage created: {self.taskbar_icon_photo}")
            self.iconphoto(True, self.taskbar_icon_photo)
            print("Taskbar icon set successfully using iconphoto.")
        except Exception as e:
            print(f"Error setting taskbar icon with iconphoto: {e}")
            # Fallback to a default Tkinter icon if custom icon fails
            try:
                self.iconbitmap('wm.ico') # A common default Tkinter icon
                print("Taskbar icon set successfully using iconbitmap fallback.")
            except Exception as e_fallback:
                print(f"Error setting taskbar icon with iconbitmap fallback: {e_fallback}")
            pass

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1) # Add column for Listen button

        ttk.Label(self, text="Display Modes:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10)

        self.create_mode_entry("PC Screen Only", "ctrl+shift+1", 1)
        self.create_mode_entry("Second Screen Only", "ctrl+shift+2", 2)
        self.create_mode_entry("Duplicate", "ctrl+shift+3", 3)
        self.create_mode_entry("Extend", "ctrl+shift+4", 4)

        self.startup_var = tk.BooleanVar()
        ttk.Checkbutton(self, text="Run on Startup", variable=self.startup_var).grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=10)

        ttk.Button(self, text="Save", command=self.save_settings).grid(row=6, column=0, padx=10, pady=10, sticky="e")
        # The "Cancel" button will now just hide the window
        ttk.Button(self, text="Cancel", command=self.withdraw).grid(row=6, column=1, padx=10, pady=10, sticky="w")

    def create_mode_entry(self, label_text, default_hotkey, row):
        ttk.Label(self, text=label_text).grid(row=row, column=0, sticky="w", padx=20)
        hotkey_entry = ttk.Entry(self, state="readonly") # Make it read-only
        hotkey_entry.insert(0, default_hotkey)
        hotkey_entry.grid(row=row, column=1, sticky="ew", padx=20, pady=5)
        self.hotkeys[label_text] = hotkey_entry

        listen_button = ttk.Button(self, text="Listen", command=lambda: self.start_listening_for_hotkey(hotkey_entry))
        listen_button.grid(row=row, column=2, sticky="w", padx=5, pady=5)

    def switch_display_mode(self, mode):
        if mode == "PC Screen Only":
            subprocess.run(["displayswitch.exe", "/internal"])
        elif mode == "Second Screen Only":
            subprocess.run(["displayswitch.exe", "/external"])
        elif mode == "Duplicate":
            subprocess.run(["displayswitch.exe", "/clone"])
        elif mode == "Extend":
            subprocess.run(["displayswitch.exe", "/extend"])

    def start_listening_for_hotkey(self, entry):
        print("Starting to listen for hotkey...")
        if self.listening_entry and self.current_hook:
            # Stop listening for the previous entry if any
            keyboard.unhook(self.current_hook)
            self.listening_entry.config(state="readonly")
            self.listening_entry = None

        self.listening_entry = entry
        self.listening_entry.config(state="normal") # Make it writable for input
        self.listening_entry.delete(0, tk.END)
        self.listening_entry.insert(0, "Press a key combination...")
        self.listening_entry.focus_set()

        # Unhook all existing hotkeys to avoid conflicts
        keyboard.unhook_all()
        # Start listening for all key events
        self.current_hook = keyboard.hook(self.on_key_event)
        print("Hooked keyboard for listening.")

    def on_key_event(self, event):
        print(f"Key event detected: {event.event_type}, name: {event.name}, is_modifier: {keyboard.is_modifier(event.name)}")
        if self.listening_entry and event.event_type == keyboard.KEY_DOWN:
            # If the pressed key is not a modifier, it's likely the final key in the combination
            if not keyboard.is_modifier(event.name):
                hotkey_string = keyboard.get_hotkey_name()
                print(f"Captured hotkey string: '{hotkey_string}'")

                # Ensure a valid hotkey string is captured (e.g., not just a modifier key by itself)
                if not hotkey_string or hotkey_string in ['ctrl', 'alt', 'shift', 'windows']:
                    print("Invalid hotkey string or modifier key only. Ignoring.")
                    return

                self.listening_entry.config(state="normal") # Make it writable temporarily
                self.listening_entry.delete(0, tk.END)
                self.listening_entry.insert(0, hotkey_string)
                self.listening_entry.config(state="readonly")

                # Stop listening for key events
                if self.current_hook:
                    keyboard.unhook(self.current_hook)
                    self.current_hook = None
                # Re-register application hotkeys
                self.register_hotkeys()
                self.listening_entry = None
                print("Hotkey captured and registered.")

    def save_hotkeys(self):
        hotkey_config = {mode: entry.get() for mode, entry in self.hotkeys.items()}
        with open("hotkeys.json", "w") as f:
            json.dump(hotkey_config, f)

    def load_hotkeys(self):
        print("Attempting to load hotkeys...")
        try:
            with open("hotkeys.json", "r") as f:
                hotkey_config = json.load(f)
                print(f"Loaded hotkey config: {hotkey_config}")
                for mode, hotkey in hotkey_config.items():
                    if mode in self.hotkeys: # Ensure the mode exists in our UI
                        self.hotkeys[mode].config(state="normal") # Temporarily enable writing
                        self.hotkeys[mode].delete(0, tk.END)
                        self.hotkeys[mode].insert(0, hotkey)
                        self.hotkeys[mode].config(state="readonly") # Revert to read-only
                        print(f"Updated {mode} with hotkey: {hotkey}")
                    else:
                        print(f"Warning: Mode '{mode}' from hotkeys.json not found in UI.")
        except FileNotFoundError:
            print("hotkeys.json not found. Using default hotkeys.")
            pass # No hotkeys saved yet
        except json.JSONDecodeError:
            print("Error decoding hotkeys.json. File might be corrupted. Using default hotkeys.")
        except Exception as e:
            print(f"An unexpected error occurred while loading hotkeys: {e}")

    def register_hotkeys(self):
        # Only register hotkeys if not in listening mode
        if not self.listening_entry:
            # Unregister all previous hotkeys
            keyboard.unhook_all()
            for mode, entry in self.hotkeys.items():
                hotkey = entry.get()
                if hotkey and hotkey != "Press a key combination...": # Ensure hotkey is not empty or placeholder
                    # Use a lambda to capture the current mode
                    keyboard.add_hotkey(hotkey, lambda m=mode: self.switch_display_mode(m))

    def set_startup(self, enable):
        key = winreg.HKEY_CURRENT_USER
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(key, path, 0, winreg.KEY_ALL_ACCESS) as registry_key:
                if enable:
                    winreg.SetValueEx(registry_key, APP_NAME, 0, winreg.REG_SZ, f'"{BAT_PATH}"')
                else:
                    winreg.DeleteValue(registry_key, APP_NAME)
        except FileNotFoundError:
            # This can happen if the value doesn't exist when trying to delete
            pass
        except Exception as e:
            print(f"Error setting startup: {e}")

    def check_startup(self):
        key = winreg.HKEY_CURRENT_USER
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(key, path, 0, winreg.KEY_READ) as registry_key:
                winreg.QueryValueEx(registry_key, APP_NAME)
                self.startup_var.set(True)
        except FileNotFoundError:
            self.startup_var.set(False)
        except Exception as e:
            print(f"Error checking startup: {e}")
            self.startup_var.set(False)


    def save_settings(self):
        self.save_hotkeys()
        self.register_hotkeys()
        self.set_startup(self.startup_var.get())
        print("Settings saved!")
        self.withdraw()

    def show_window(self):
        print("Showing window...")
        self.deiconify()
        self.lift()
        self.focus_force()

    def exit_app(self, icon):
        keyboard.unhook_all()
        icon.stop()
        self.quit()
        # Release the mutex when the application exits
        global mutex_handle
        if mutex_handle:
            win32event.ReleaseMutex(mutex_handle)
            win32api.CloseHandle(mutex_handle)
            mutex_handle = None

def create_image():
    # Create a placeholder image if icon.png is not found
    width = 64
    height = 64
    color1 = (100, 100, 100)
    color2 = (200, 200, 200)
    image = Image.new('RGB', (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2),
        fill=color2)
    dc.rectangle(
        (0, height // 2, width // 2, height),
        fill=color2)
    return image

def run_icon(app):
    # Try to load the user-provided icon, otherwise create a default one
    try:
        image = Image.open(ICON_PATH)
    except FileNotFoundError:
        image = create_image()

    def on_exit(icon, item):
        app.exit_app(icon)

    menu = (item('Show Settings', lambda icon, item: app.after(0, app.show_window)), item('Exit', on_exit))
    icon = pystray.Icon("DisplayMode", image, "DisplayMode", menu, on_activate=lambda icon, item: app.after(0, app.show_window))
    icon.run()

if __name__ == "__main__":
    # Mutex to ensure only one instance of the application runs
    # mutex_name = "DisplayModeAppMutex"
    # try:
    #     # Attempt to create a named mutex
    #     # If it already exists, CreateMutex returns a handle to the existing mutex
    #     # and GetLastError returns ERROR_ALREADY_EXISTS (0xB7)
    #     mutex_handle = win32event.CreateMutex(None, 1, mutex_name)
    #     if win32api.GetLastError() == 0xB7:  # ERROR_ALREADY_EXISTS
    #         print("Another instance of DisplayMode is already running. Exiting.")
    #         sys.exit(0)
    # except Exception as e:
    #     print(f"Error creating mutex: {e}")
    #     sys.exit(1)

    app = DisplayModeApp()
    app.withdraw() # Hide the main window on startup

    # Run the icon in a separate thread
    icon_thread = threading.Thread(target=run_icon, args=(app,))
    icon_thread.daemon = True
    icon_thread.start()

    try:
        app.mainloop()
    finally:
        pass # Placeholder for now, as mutex handling is commented out
