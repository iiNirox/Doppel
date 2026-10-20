# Doppel 🔁

Doppel is a lightweight, open-source Python application that records mouse movements and keyboard strokes, allowing you to play them back at custom speeds. Inspired by TinyTask, Doppel features a clean GUI, native `.rec` file saving, and a built-in macro editor.

## Features

- **Precision Macro Recording:** Seamlessly capture exact mouse movements, clicks, scrolls, and keyboard keystrokes down to the millisecond.
- **Custom Playback Speeds:** Scale your macro playback speed dynamically from `0.5x` (slow motion) up to `1000x` (instant execution).
- **Playlist Queue Manager:** Chain multiple `.rec` files together to run back-to-back. Easily reorder your queue using **drag-and-drop** or keyboard/on-screen arrow buttons (`▲`/`▼`).
- **Advanced Step Editor:** Open the built-in macro editor to view every individual step, delete unwanted actions/jitters, or artificially insert wait times.
- **Global Hotkeys:** Press `F8` to start/stop recording and `F9` to play/stop your macro or playlist without clicking the application window.
- **Smart EXE Builder:** A built-in PyInstaller wrapper that compiles your script into a portable standalone `.exe`. When run as an executable, the builder option automatically hides itself for a cleaner layout.
- **Always on Top & Menus:** Pin the window so it floats over your screen, with full File, View, and Help menus linking directly to the developer repository.
- **Dark UI:** A gorgeous, minimalist obsidian dark mode interface featuring smooth custom anti-aliased rounded buttons and real-time status indicators.

## Installation

**Prerequisites:** You must have Python installed on your system.

1. Clone this repository or download the source code.
2. Open your terminal or command prompt in the folder directory.
3. Install the required dependency:
   ```bash
   pip install -r requirements.txt
