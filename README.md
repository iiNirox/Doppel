# Doppel 🔁

Doppel is a lightweight, open-source Python application that records mouse movements and keyboard strokes, allowing you to play them back at custom speeds. Inspired by TinyTask, Doppel features a clean GUI, native `.rec` file saving, and a built-in macro editor.

## Features

- **Record & Playback:** Capture precise mouse clicks, movements, scrolls, and keystrokes.
- **Custom Playback Speed:** Speed up or slow down your macros from `0.5x` (half speed) to `1000x` (instant execution).
- **Macro Editor:** View every recorded step down to the millisecond. Delete unwanted actions or artificially insert wait times.
- **Save/Load:** Save your complex macros as `.rec` files to use later.
- **Hotkeys:** Press `F8` to start/stop recording and `F9` to play/stop the macro without needing to click the GUI.
- **Executable Builder:** Built-in button to automatically compile the script into a standalone `.exe` using PyInstaller.

## Installation

**Prerequisites:** You must have Python installed on your system.

1. Clone this repository or download the source code.
2. Open your terminal or command prompt in the folder directory.
3. Install the required dependency:
   ```bash
   pip install -r requirements.txt