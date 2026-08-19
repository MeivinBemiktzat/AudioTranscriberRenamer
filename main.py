import sys
import os
import ctypes
import tkinter as tk
from gui import ModernTranscriberApp


def get_resource_path(relative_path: str) -> str:
    """
    Returns absolute path to resource, works for dev and for PyInstaller onefile binary.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def enable_high_dpi():
    """Enables crisp UI rendering on high resolution Windows displays."""
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def main():
    enable_high_dpi()
    root = tk.Tk()
    
    # Set application icon if available
    icon_path = get_resource_path(os.path.join("assets", "icon.ico"))
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    app = ModernTranscriberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
