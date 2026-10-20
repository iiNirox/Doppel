import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pynput import mouse, keyboard
import time
import threading
import json
import os
import sys
import subprocess

# Colors for Modern Dark Aesthetics
BG_COLOR = "#0F0F12"          # Dark Obsidian
CARD_BG = "#1A1A22"           # Slightly lighter dark grey
TEXT_COLOR = "#E2E8F0"        # Off-white/slate
ACCENT_PURPLE = "#A855F7"     # Neon Purple
ACCENT_GREEN = "#10B981"      # Cyber Green
ACCENT_RED = "#EF4444"        # Record Red
BUTTON_BG = "#272732"         # Button default dark
BUTTON_HOVER = "#3B3B4F"      # Hover glow bg
TEXT_MUTED = "#94A3B8"        # Gray for secondary info

class DoppelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Doppel")
        self.root.geometry("460x140")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.events = []
        self.is_recording = False
        self.is_playing = False
        self.is_compiling = False
        self.start_time = 0

        self.mouse_listener = None
        self.keyboard_listener = None
        
        self.mouse_ctrl = mouse.Controller()
        self.keyboard_ctrl = keyboard.Controller()

        self.setup_gui()
        self.setup_hotkeys()

    def setup_gui(self):
        # Custom Title / Header Bar
        header = tk.Frame(self.root, bg=BG_COLOR, height=35)
        header.pack(fill=tk.X, padx=12, pady=(8, 0))
        
        title_lbl = tk.Label(header, text="Doppel 🔁", font=("Segoe UI", 12, "bold"), fg=ACCENT_PURPLE, bg=BG_COLOR)
        title_lbl.pack(side=tk.LEFT)
        
        self.status_dot = tk.Label(header, text="●", font=("Segoe UI", 11), fg=ACCENT_GREEN, bg=BG_COLOR)
        self.status_dot.pack(side=tk.RIGHT, padx=(0, 2))
        self.status_lbl = tk.Label(header, text="IDLE", font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=BG_COLOR)
        self.status_lbl.pack(side=tk.RIGHT, padx=5)

        # Toolbar Frame for Controls
        toolbar = tk.Frame(self.root, bg=BG_COLOR)
        toolbar.pack(fill=tk.X, padx=12, pady=5)

        # Flat styling with hover interactions
        self.btn_open = self.create_btn(toolbar, "📂\nOpen", self.load_rec)
        self.btn_open.grid(row=0, column=0, padx=2)

        self.btn_save = self.create_btn(toolbar, "💾\nSave", self.save_rec)
        self.btn_save.grid(row=0, column=1, padx=2)

        self.btn_record = self.create_btn(toolbar, "🔴\nRec (F8)", self.toggle_record, highlight=ACCENT_RED)
        self.btn_record.grid(row=0, column=2, padx=2)

        self.btn_play = self.create_btn(toolbar, "▶\nPlay (F9)", self.toggle_play, highlight=ACCENT_GREEN)
        self.btn_play.grid(row=0, column=3, padx=2)

        self.btn_edit = self.create_btn(toolbar, "✏️\nEdit", self.open_editor)
        self.btn_edit.grid(row=0, column=4, padx=2)

        self.btn_exe = self.create_btn(toolbar, "📦\nMake .exe", self.make_exe, highlight=ACCENT_PURPLE)
        self.btn_exe.grid(row=0, column=5, padx=2)

        # Speed Settings Bar (Compact Footer)
        footer = tk.Frame(self.root, bg=CARD_BG, height=35)
        footer.pack(fill=tk.X, padx=12, pady=(5, 10))
        
        speed_lbl = tk.Label(footer, text="⚡ SPEED:", font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=CARD_BG)
        speed_lbl.pack(side=tk.LEFT, padx=(10, 5), pady=6)
        
        self.speed_var = tk.StringVar(value="1.0")
        self.speed_entry = tk.Entry(footer, textvariable=self.speed_var, font=("Segoe UI", 9, "bold"), 
                                    fg=TEXT_COLOR, bg=BG_COLOR, insertbackground=TEXT_COLOR, 
                                    bd=0, justify="center", width=6)
        self.speed_entry.pack(side=tk.LEFT, padx=2, pady=5)
        
        speed_unit = tk.Label(footer, text="x  (0.5 - 1000)", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=CARD_BG)
        speed_unit.pack(side=tk.LEFT, padx=2)

        self.credits_lbl = tk.Label(footer, text="v1.1", font=("Segoe UI", 8, "italic"), fg=TEXT_MUTED, bg=CARD_BG)
        self.credits_lbl.pack(side=tk.RIGHT, padx=10, pady=6)

    def create_btn(self, parent, text, command, highlight=None):
        """Helper to construct sleek flat buttons with modern dark UI hovers."""
        btn = tk.Button(
            parent, text=text, command=command, font=("Segoe UI", 8, "bold"),
            bg=BUTTON_BG, fg=TEXT_COLOR, activebackground=BUTTON_HOVER, activeforeground=TEXT_COLOR,
            relief="flat", bd=0, width=8, height=2, cursor="hand2"
        )
        if highlight:
            btn.config(fg=highlight)
            
        def on_enter(e):
            btn.config(bg=BUTTON_HOVER)
        def on_leave(e):
            btn.config(bg=BUTTON_BG)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def update_status(self, text, color):
        self.status_lbl.config(text=text, fg=color)
        self.status_dot.config(fg=color)

    def setup_hotkeys(self):
        def on_press(key):
            if key == keyboard.Key.f8:
                self.root.after(0, self.toggle_record)
            elif key == keyboard.Key.f9:
                self.root.after(0, self.toggle_play)
        
        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.start()

    # --- RECORDING LOGIC ---
    def toggle_record(self):
        if self.is_playing: return
        
        if not self.is_recording:
            self.events.clear()
            self.is_recording = True
            self.btn_record.config(text="⏹\nStop (F8)", fg=ACCENT_RED)
            self.update_status("RECORDING", ACCENT_RED)
            self.start_time = time.time()
            
            self.mouse_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
            self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
        else:
            self.is_recording = False
            self.btn_record.config(text="🔴\nRec (F8)", fg=ACCENT_RED)
            self.update_status("IDLE", TEXT_MUTED)
            if self.mouse_listener: self.mouse_listener.stop()
            if self.keyboard_listener: self.keyboard_listener.stop()

    def record_event(self, event_data):
        if self.is_recording:
            event_data['time'] = time.time() - self.start_time
            self.events.append(event_data)

    def on_move(self, x, y):
        self.record_event({'action': 'move', 'x': x, 'y': y})

    def on_click(self, x, y, button, pressed):
        self.record_event({'action': 'click', 'x': x, 'y': y, 'button': str(button), 'pressed': pressed})

    def on_scroll(self, x, y, dx, dy):
        self.record_event({'action': 'scroll', 'x': x, 'y': y, 'dx': dx, 'dy': dy})

    def on_press(self, key):
        if key in [keyboard.Key.f8, keyboard.Key.f9]: return
        try: k = key.char
        except AttributeError: k = str(key)
        self.record_event({'action': 'press', 'key': k})

    def on_release(self, key):
        if key in [keyboard.Key.f8, keyboard.Key.f9]: return
        try: k = key.char
        except AttributeError: k = str(key)
        self.record_event({'action': 'release', 'key': k})

    # --- PLAYBACK LOGIC ---
    def toggle_play(self):
        if self.is_recording or not self.events: return
        
        if not self.is_playing:
            self.is_playing = True
            self.btn_play.config(text="⏹\nStop (F9)", fg=ACCENT_RED)
            self.update_status("PLAYING", ACCENT_GREEN)
            threading.Thread(target=self.play_macro, daemon=True).start()
        else:
            self.is_playing = False

    def get_key_from_string(self, key_str):
        if key_str.startswith('Key.'):
            return getattr(keyboard.Key, key_str.split('.')[1])
        return key_str

    def play_macro(self):
        try:
            speed = float(self.speed_var.get())
            if speed < 0.5 or speed > 1000:
                speed = max(0.5, min(speed, 1000.0))
        except ValueError:
            speed = 1.0

        start_time = time.time()
        
        for event in self.events:
            if not self.is_playing: break
            
            target_time = start_time + (event['time'] / speed)
            sleep_duration = target_time - time.time()
            
            if sleep_duration > 0:
                time.sleep(sleep_duration)

            action = event['action']
            try:
                if action == 'move':
                    self.mouse_ctrl.position = (event['x'], event['y'])
                elif action == 'click':
                    btn = mouse.Button.left if 'left' in event['button'] else mouse.Button.right if 'right' in event['button'] else mouse.Button.middle
                    if event['pressed']: self.mouse_ctrl.press(btn)
                    else: self.mouse_ctrl.release(btn)
                elif action == 'scroll':
                    self.mouse_ctrl.scroll(event['dx'], event['dy'])
                elif action == 'press':
                    self.keyboard_ctrl.press(self.get_key_from_string(event['key']))
                elif action == 'release':
                    self.keyboard_ctrl.release(self.get_key_from_string(event['key']))
            except Exception:
                pass # Avoid app lockups if some virtual modifier releases fail.

        self.is_playing = False
        self.root.after(0, lambda: [
            self.btn_play.config(text="▶\nPlay (F9)", fg=ACCENT_GREEN),
            self.update_status("IDLE", TEXT_MUTED)
        ])

    # --- FILE OPERATIONS ---
    def save_rec(self):
        if not self.events:
            messagebox.showinfo("Empty", "Nothing to save!")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".rec", filetypes=[("Doppel Record", "*.rec")])
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(self.events, f)

    def load_rec(self):
        filepath = filedialog.askopenfilename(filetypes=[("Doppel Record", "*.rec")])
        if filepath:
            with open(filepath, 'r') as f:
                self.events = json.load(f)
            messagebox.showinfo("Loaded", f"Successfully loaded {len(self.events)} steps.")

    # --- SAFE/FIXED EXE COMPILATION ---
    def make_exe(self):
        if self.is_compiling:
            return
        
        msg = ("Do you want to compile this script to a standalone Executable?\n\n"
               "Ensure you have 'pyinstaller' installed first (pip install pyinstaller).\n\n"
               "Compile times may take up to a minute.")
        if not messagebox.askyesno("Confirm Compilation", msg):
            return

        self.is_compiling = True
        self.update_status("BUILDING...", ACCENT_PURPLE)
        self.btn_exe.config(text="⏳\nWait...", state="disabled", fg=TEXT_MUTED)

        # Multithread compile processing to guarantee UI stability
        threading.Thread(target=self.run_pyinstaller, daemon=True).start()

    def run_pyinstaller(self):
        current_script = sys.argv[0] if sys.argv[0].endswith(".py") else "doppel.py"
        
        # Self-Check for doppel.py safety
        if not os.path.exists(current_script):
            # Safe Fallback to standard save if run under temp names
            with open("doppel.py", "w") as f:
                f.write(open(__file__).read())
            current_script = "doppel.py"

        # Correctly call inside active Python Env back to command terminal
        try:
            cmd = [sys.executable, "-m", "PyInstaller", "--noconsole", "--onefile", current_script]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if result.returncode == 0:
                messagebox.showinfo("Compilation Complete", "Doppel successfully built!\n\nCheck your newly created 'dist' folder.")
            else:
                messagebox.showerror("Build Error", f"Something went wrong during compilation:\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to execute compilation tool: {e}")
        finally:
            self.is_compiling = False
            self.root.after(0, lambda: [
                self.btn_exe.config(text="📦\nMake .exe", state="normal", fg=ACCENT_PURPLE),
                self.update_status("IDLE", TEXT_MUTED)
            ])

    # --- COMPACT EDITOR ---
    def open_editor(self):
        if self.is_recording or self.is_playing: return
        
        editor = tk.Toplevel(self.root)
        editor.title("Doppel - Macro Editor")
        editor.geometry("420x420")
        editor.configure(bg=BG_COLOR)
        editor.attributes("-topmost", True)

        title = tk.Label(editor, text="Macro Steps Editor", font=("Segoe UI", 11, "bold"), fg=ACCENT_PURPLE, bg=BG_COLOR)
        title.pack(anchor="w", px=15, py=10)

        # Style Listbox
        list_frame = tk.Frame(editor, bg=BG_COLOR)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        scroll = tk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, font=("Courier New", 9),
                             bg=CARD_BG, fg=TEXT_COLOR, borderwidth=0, highlightthickness=0,
                             selectbackground=ACCENT_PURPLE, yscrollcommand=scroll.set)
        listbox.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=listbox.yview)

        def refresh_list():
            listbox.delete(0, tk.END)
            for i, e in enumerate(self.events):
                desc = f"[{e['time']:.2f}s] {e['action'].upper()}"
                if e['action'] == 'move': desc += f" to ({e['x']}, {e['y']})"
                elif e['action'] == 'click': desc += f" {e['button']} {'↓' if e['pressed'] else '↑'}"
                elif e['action'] in ['press', 'release']: desc += f" '{e['key']}'"
                listbox.insert(tk.END, f"{i:03d}: {desc}")

        refresh_list()

        def delete_selected():
            selected = listbox.curselection()
            if not selected: return
            for index in reversed(selected):
                del self.events[index]
            refresh_list()

        def add_wait():
            wait_time = simpledialog.askfloat("Insert Wait", "Wait duration (seconds):", parent=editor)
            if wait_time and len(self.events) > 0:
                selected = listbox.curselection()
                insert_idx = selected[0] + 1 if selected else len(self.events)
                
                # Shift all subsequence actions forward
                for i in range(insert_idx, len(self.events)):
                    self.events[i]['time'] += wait_time
                refresh_list()

        # Modern controls for step updates
        btn_frame = tk.Frame(editor, bg=BG_COLOR)
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        del_btn = tk.Button(btn_frame, text="🗑 Delete", command=delete_selected, font=("Segoe UI", 9, "bold"),
                            bg=BUTTON_BG, fg=ACCENT_RED, activebackground=BUTTON_HOVER, relief="flat", bd=0, padx=10, pady=5)
        del_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        wait_btn = tk.Button(btn_frame, text="⏳ Add Wait", command=add_wait, font=("Segoe UI", 9, "bold"),
                             bg=BUTTON_BG, fg=ACCENT_GREEN, activebackground=BUTTON_HOVER, relief="flat", bd=0, padx=10, pady=5)
        wait_btn.pack(side=tk.LEFT)

        clear_btn = tk.Button(btn_frame, text="❌ Clear All", command=lambda: [self.events.clear(), refresh_list()], 
                              font=("Segoe UI", 9, "bold"), bg=BUTTON_BG, fg=TEXT_MUTED, activebackground=BUTTON_HOVER, relief="flat", bd=0, padx=10, pady=5)
        clear_btn.pack(side=tk.RIGHT)

if __name__ == "__main__":
    root = tk.Tk()
    app = DoppelApp(root)
    root.mainloop()
