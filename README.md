# Context Menu Manager

A lightweight, native GUI utility for Windows to view, toggle, clean up, and customize Windows Explorer context menu entries without manually navigating the Windows Registry.

## Features

- **Categorized Discovery:** Inspect context menu entries for **Files (`*`)**, **Folders & Directories**, **Desktop & Background**, and **Drives**.
- **Safe Enable & Disable:** Toggle cluttering entries on and off instantly without deleting registry keys (using Windows' native `LegacyDisable` and `Shell Extensions\Blocked`).
- **Windows 11 Classic Menu Toggle:** Switch between the Windows 11 modern context menu and the classic Windows 10 style menu in one click.
- **Custom Context Menu Actions:** Easily add custom right-click actions with customizable command arguments, working directory tokens (`%V`, `%1`), custom icons, and menu positions (`Top` / `Bottom`).
- **Explorer Restarter:** 1-click restart helper that flushes the shell cache (`SHChangeNotify`) and revives the Windows Explorer process cleanly.
- **Jump to RegEdit:** Open the exact key path directly in `regedit.exe` with a single click.
- **Automated JSON Backups:** Export full key hierarchies to `./backups/` before deleting any entries.

## Requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.10+ (Standard library with `tkinter` and `ctypes`; no external `pip` dependencies required)

## Usage

Run the launcher or execute `main.py` directly:

```bat
run.bat
```

Or via Python:

```sh
python main.py
```

## Keyboard Shortcuts

- `Space`: Toggle selected item status (Enable / Disable)
- `F5`: Refresh all items and registry scan
- `Delete`: Delete selected item (prompts to create a JSON backup)
- `Ctrl` + `N`: Open "Add Custom Action" dialog
- `Ctrl` + `R`: Restart Windows Explorer and flush shell cache
- `Ctrl` + `F`: Focus search bar
