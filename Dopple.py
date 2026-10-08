import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pynput import mouse, keyboard
import time
import threading
import json
import os
import subprocess

class DoppelApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Doppel")
        self.root.geometry("450x100")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.events = []
        self.is_recording = False
        self.is_playing = False
        self.start_time = 0

        self.mouse_listener = None
        self.keyboard_listener = None
        
        self.mouse_ctrl = mouse.Controller()
        self.keyboard_ctrl = keyboard.Controller()

        self.setup_gui()
        self.setup_hotkeys()

    def setup_gui(self):
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill=tk.BOTH, expand=True)

        # Buttons
        self.btn_open = ttk.Button(toolbar, text="📂 Open", width=8, command=self.load_rec)
        self.btn_open.grid(row=0, column=0, padx=2, pady=5)

        self.btn_save = ttk.Button(toolbar, text="💾 Save", width=8, command=self.save_rec)
        self.btn_save.grid(row=0, column=1, padx=2, pady=5)

        self.btn_record = ttk.Button(toolbar, text="🔴 Rec (F8)", width=10, command=self.toggle_record)
        self.btn_record.grid(row=0, column=2, padx=2, pady=5)

        self.btn_play = ttk.Button(toolbar, text="▶ Play (F9)", width=10, command=self.toggle_play)
        self.btn_play.grid(row=0, column=3, padx=2, pady=5)

        self.btn_edit = ttk.Button(toolbar, text="✏️ Edit", width=8, command=self.open_editor)
        self.btn_edit.grid(row=0, column=4, padx=2, pady=5)

        # Speed Control
        ttk.Label(toolbar, text="Speed:").grid(row=1, column=0, columnspan=2, sticky='e')
        self.speed_var = tk.StringVar(value="1.0")
        self.speed_entry = ttk.Entry(toolbar, textvariable=self.speed_var, width=10)
        self.speed_entry.grid(row=1, column=2, columnspan=2, sticky='w', padx=5)
        
        self.btn_exe = ttk.Button(toolbar, text="Make .exe", width=10, command=self.make_exe)
        self.btn_exe.grid(row=1, column=4, padx=2)

    def setup_hotkeys(self):
        # Global hotkey listener to start/stop without clicking the app
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
            self.btn_record.config(text="⏹ Stop (F8)")
            self.start_time = time.time()
            
            self.mouse_listener = mouse.Listener(
                on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_press, on_release=self.on_release)
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
        else:
            self.is_recording = False
            self.btn_record.config(text="🔴 Rec (F8)")
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
        # Ignore F8 and F9 so they don't get recorded in the macro
        if key in [keyboard.Key.f8, keyboard.Key.f9]: return
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self.record_event({'action': 'press', 'key': k})

    def on_release(self, key):
        if key in [keyboard.Key.f8, keyboard.Key.f9]: return
        try:
            k = key.char
        except AttributeError:
            k = str(key)
        self.record_event({'action': 'release', 'key': k})

    # --- PLAYBACK LOGIC ---
    def toggle_play(self):
        if self.is_recording or not self.events: return
        
        if not self.is_playing:
            self.is_playing = True
            self.btn_play.config(text="⏹ Stop (F9)")
            threading.Thread(target=self.play_macro, daemon=True).start()
        else:
            self.is_playing = False # Play thread checks this flag

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
        
        for i, event in enumerate(self.events):
            if not self.is_playing: break # Interrupted by user
            
            # Calculate when this event should happen
            target_time = start_time + (event['time'] / speed)
            sleep_duration = target_time - time.time()
            
            if sleep_duration > 0:
                time.sleep(sleep_duration)

            action = event['action']
            if action == 'move':
                self.mouse_ctrl.position = (event['x'], event['y'])
            elif action == 'click':
                btn = mouse.Button.left if 'left' in event['button'] else mouse.Button.right if 'right' in event['button'] else mouse.Button.middle
                if event['pressed']:
                    self.mouse_ctrl.press(btn)
                else:
                    self.mouse_ctrl.release(btn)
            elif action == 'scroll':
                self.mouse_ctrl.scroll(event['dx'], event['dy'])
            elif action == 'press':
                self.keyboard_ctrl.press(self.get_key_from_string(event['key']))
            elif action == 'release':
                self.keyboard_ctrl.release(self.get_key_from_string(event['key']))

        self.is_playing = False
        self.root.after(0, lambda: self.btn_play.config(text="▶ Play (F9)"))

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
            messagebox.showinfo("Loaded", f"Loaded {len(self.events)} steps.")

    # --- EXE COMPILATION ---
    def make_exe(self):
        msg = ("To compile this script into an executable, ensure you have pyinstaller installed:\n\n"
               "pip install pyinstaller\n\n"
               "Then run this in your terminal where this script is saved:\n"
               "pyinstaller --noconsole --onefile doppel.py\n\n"
               "Do you want Doppel to attempt to run this command for you now?")
        
        if messagebox.askyesno("Make EXE", msg):
            try:
                subprocess.Popen(["pyinstaller", "--noconsole", "--onefile", "doppel.py"])
                messagebox.showinfo("Compiling", "Pyinstaller started! Check your 'dist' folder in a minute.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to run pyinstaller automatically. Do it via command line.\nError: {e}")

    # --- EDITOR LOGIC ---
    def open_editor(self):
        if self.is_recording or self.is_playing: return
        
        editor = tk.Toplevel(self.root)
        editor.title("Doppel Editor")
        editor.geometry("400x400")
        editor.attributes("-topmost", True)

        listbox = tk.Listbox(editor, selectmode=tk.EXTENDED)
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def refresh_list():
            listbox.delete(0, tk.END)
            for i, e in enumerate(self.events):
                desc = f"[{e['time']:.2f}s] {e['action'].upper()}"
                if e['action'] == 'move': desc += f" to ({e['x']}, {e['y']})"
                elif e['action'] == 'click': desc += f" {e['button']} {'down' if e['pressed'] else 'up'}"
                elif e['action'] in ['press', 'release']: desc += f" '{e['key']}'"
                listbox.insert(tk.END, f"{i}: {desc}")

        refresh_list()

        def delete_selected():
            selected = listbox.curselection()
            for index in reversed(selected):
                del self.events[index]
            refresh_list()

        def add_wait():
            wait_time = simpledialog.askfloat("Add Wait", "Time to wait (seconds):", parent=editor)
            if wait_time and len(self.events) > 0:
                selected = listbox.curselection()
                insert_idx = selected[0] + 1 if selected else len(self.events)
                
                # Shift subsequent event times by the wait time to artificially add a pause
                for i in range(insert_idx, len(self.events)):
                    self.events[i]['time'] += wait_time
                refresh_list()

        btn_frame = ttk.Frame(editor)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Delete Selected", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Add Wait (Shift Times)", command=add_wait).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", command=lambda: [self.events.clear(), refresh_list()]).pack(side=tk.RIGHT, padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = DoppelApp(root)
    root.mainloop()