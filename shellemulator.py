import os
import zipfile
import json
import shutil
import tkinter as tk
from tkinter import filedialog, Text

class ShellEmulator:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.hostname = self.config['hostname']
        self.zip_path = self.config['filesystem']
        self.current_path = '/'
        self.temp_dir = 'temp_filesystem'

        self.setup_filesystem()

    def setup_filesystem(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)

        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def teardown_filesystem(self):
        shutil.rmtree(self.temp_dir)

    def get_real_path(self, virtual_path):
        return os.path.join(self.temp_dir, virtual_path.lstrip('/'))

    def list_dir(self):
        real_path = self.get_real_path(self.current_path)
        return os.listdir(real_path)

    def change_dir(self, path):
        real_path = self.get_real_path(os.path.join(self.current_path, path))
        if os.path.isdir(real_path):
            self.current_path = os.path.normpath(os.path.join(self.current_path, path))
        else:
            raise FileNotFoundError(f"Directory not found: {path}")

    def make_dir(self, name):
        real_path = self.get_real_path(os.path.join(self.current_path, name))
        os.makedirs(real_path, exist_ok=True)

    def create_file(self, name):
        real_path = self.get_real_path(os.path.join(self.current_path, name))
        with open(real_path, 'w') as f:
            pass

    def move(self, source, destination):
        real_source = self.get_real_path(os.path.join(self.current_path, source))
        real_destination = self.get_real_path(os.path.join(self.current_path, destination))
        shutil.move(real_source, real_destination)

class ShellGUI:
    def __init__(self, emulator):
        self.emulator = emulator
        self.root = tk.Tk()
        self.root.title("Shell Emulator")

        self.text_area = Text(self.root, height=20, width=80)
        self.text_area.pack()

        self.entry = tk.Entry(self.root, width=80)
        self.entry.pack()
        self.entry.bind("<Return>", self.execute_command)

        self.print_prompt()

    def print_prompt(self):
        prompt = f"{self.emulator.hostname}:{self.emulator.current_path}$ "
        self.text_area.insert(tk.END, prompt)
        self.text_area.see(tk.END)

    def execute_command(self, event):
        command = self.entry.get()
        self.text_area.insert(tk.END, command + '\n')
        self.entry.delete(0, tk.END)

        try:
            self.process_command(command)
        except Exception as e:
            self.text_area.insert(tk.END, f"Error: {str(e)}\n")

        self.print_prompt()

    def process_command(self, command):
        parts = command.split()
        if not parts:
            return

        cmd = parts[0]
        args = parts[1:]

        if cmd == "ls":
            items = self.emulator.list_dir()
            self.text_area.insert(tk.END, "\n".join(items) + '\n')
        elif cmd == "cd":
            if args:
                self.emulator.change_dir(args[0])
            else:
                raise ValueError("cd: missing argument")
        elif cmd == "mkdir":
            if args:
                self.emulator.make_dir(args[0])
            else:
                raise ValueError("mkdir: missing argument")
        elif cmd == "touch":
            if args:
                self.emulator.create_file(args[0])
            else:
                raise ValueError("touch: missing argument")
        elif cmd == "mv":
            if len(args) >= 2:
                self.emulator.move(args[0], args[1])
            else:
                raise ValueError("mv: missing arguments")
        elif cmd == "exit":
            self.emulator.teardown_filesystem()
            self.root.quit()
        else:
            self.text_area.insert(tk.END, f"Unknown command: {cmd}\n")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    config_path = filedialog.askopenfilename(title="Select Config File", filetypes=[("JSON files", "*.json")])
    if not config_path:
        print("No configuration file selected. Exiting.")
        exit()

    emulator = ShellEmulator(config_path)
    gui = ShellGUI(emulator)
    gui.run()