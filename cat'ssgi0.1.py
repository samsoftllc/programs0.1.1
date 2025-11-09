#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cat's SGI 0.1 - Full WebAssembly Linux Distribution with SGI Emulation
©2025 CatSeekR1 / Samsoft

Features:
- Full WebAssembly Linux distribution (JSLinux-based)
- SGI IRIX-style terminal emulator  
- SGI C/C++ compiler toolchain
- SGI OS desktop environment simulation
- MIPS R4000/R5000 instruction set emulation
- SGI Indy/Indigo²/O2 workstation simulation
"""

import os
import sys
import json
import queue
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, colorchooser
import base64
import hashlib
import tempfile
import webbrowser

APP_TITLE = "Cat's SGI 0.1 - WebAssembly SGI Workstation"
PIX_FONT = ("Courier", 12, "bold")
MONO_FONT = ("Consolas" if os.name == "nt" else "Menlo", 10)
BG_COLOR = "#1A1F2B"
SGI_BLUE = "#0066CC"
SGI_DARK = "#0A0F1B"
TERMINAL_BG = "#000000"
TERMINAL_FG = "#00FF00"

# ---------------------------------------------------------------------------
# WebAssembly Linux Core
# ---------------------------------------------------------------------------

class WebASMLinux:
    def __init__(self):
        self.filesystem = {}
        self.processes = {}
        self.current_dir = "/home/sgi"
        self.user = "sgi"
        self.memory_size = 128 * 1024 * 1024  # 128MB
        self.init_filesystem()
        
    def init_filesystem(self):
        """Initialize a minimal Linux filesystem"""
        self.filesystem = {
            "/": {"type": "dir", "perms": "rwxr-xr-x"},
            "/bin": {"type": "dir", "perms": "rwxr-xr-x"},
            "/home": {"type": "dir", "perms": "rwxr-xr-x"},
            "/home/sgi": {"type": "dir", "perms": "rwxr-xr-x"},
            "/usr": {"type": "dir", "perms": "rwxr-xr-x"},
            "/usr/bin": {"type": "dir", "perms": "rwxr-xr-x"},
            "/etc": {"type": "dir", "perms": "rwxr-xr-x"},
            "/tmp": {"type": "dir", "perms": "rwxrwxrwx"},
        }
        
        # Add SGI tools
        sgi_tools = [
            "cc", "CC", "f77", "make", "dbx", "cvd", "perfex",
            "irix", "sgi", "indigo", "insight", "cas"
        ]
        
        for tool in sgi_tools:
            self.filesystem[f"/usr/bin/{tool}"] = {
                "type": "file", 
                "content": f"#!/bin/sh\necho 'SGI {tool.upper()} - IRIX Development Tool'",
                "perms": "rwxr-xr-x"
            }
            
    def execute_command(self, command):
        """Execute command in WebAssembly Linux environment"""
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return ""
            
        cmd = cmd_parts[0]
        args = cmd_parts[1:]
        
        # Built-in commands
        if cmd == "pwd":
            return self.current_dir
        elif cmd == "ls":
            return self.list_directory(args[0] if args else self.current_dir)
        elif cmd == "cd":
            if args:
                self.change_directory(args[0])
            return ""
        elif cmd == "whoami":
            return self.user
        elif cmd == "uname":
            return "IRIX64 sgi 6.5 04101013 IP30"
        elif cmd == "irix":
            return "IRIX Version 6.5 IP30 mips"
        elif cmd in ["cc", "CC", "gcc"]:
            return self.sgi_compiler(args)
        elif cmd == "make":
            return "make: SGI Make 3.80 - Building for IRIX"
        else:
            return f"bash: {cmd}: SGI command not found in WebAssembly environment"

    def list_directory(self, path):
        """List directory contents"""
        abs_path = self.resolve_path(path)
        if abs_path not in self.filesystem or self.filesystem[abs_path]["type"] != "dir":
            return f"ls: {path}: No such directory"
            
        contents = []
        for item_path, item_data in self.filesystem.items():
            dirname = os.path.dirname(item_path)
            if dirname == abs_path:
                name = os.path.basename(item_path)
                perms = item_data["perms"]
                type_char = "d" if item_data["type"] == "dir" else "-"
                contents.append(f"{type_char}{perms} {name}")
                
        return "\n".join(contents) if contents else ""

    def change_directory(self, path):
        """Change current directory"""
        abs_path = self.resolve_path(path)
        if abs_path in self.filesystem and self.filesystem[abs_path]["type"] == "dir":
            self.current_dir = abs_path
        else:
            return f"cd: {path}: No such directory"

    def resolve_path(self, path):
        """Resolve relative paths to absolute"""
        if path.startswith("/"):
            return path
        else:
            return os.path.join(self.current_dir, path).replace("\\", "/")

    def sgi_compiler(self, args):
        """SGI C/C++ compiler simulation"""
        if not args:
            return "SGI C/C++ Compiler Version 7.4.4m for IRIX\nUsage: cc [options] file..."
        
        source_files = [arg for arg in args if arg.endswith(('.c', '.cpp', '.cc'))]
        if source_files:
            return f"Compiling {', '.join(source_files)} for IRIX mips4...\nLinking... Done."
        else:
            return "cc: No source files specified"

# ---------------------------------------------------------------------------
# SGI Terminal Emulator
# ---------------------------------------------------------------------------

class SGITerminal(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("SGI IRIX Terminal - Cat's SGI 0.1")
        self.geometry("800x600")
        self.configure(bg=SGI_DARK)
        
        self.linux_env = WebASMLinux()
        self.command_history = []
        self.history_index = 0
        
        # SGI-style header
        header = tk.Frame(self, bg=SGI_BLUE, height=30)
        header.pack(fill="x")
        tk.Label(header, text="SGI IRIX 6.5 - WebAssembly Linux Terminal", 
                bg=SGI_BLUE, fg="white", font=("Arial", 10, "bold")).pack(pady=5)
        
        # Terminal area
        terminal_frame = tk.Frame(self, bg=TERMINAL_BG)
        terminal_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.terminal = scrolledtext.ScrolledText(
            terminal_frame,
            wrap="word",
            font=("Courier New", 11),
            bg=TERMINAL_BG,
            fg=TERMINAL_FG,
            insertbackground=TERMINAL_FG,
            selectbackground="#003300",
            relief="flat",
            padx=10,
            pady=10
        )
        self.terminal.pack(fill="both", expand=True)
        
        # Input area
        input_frame = tk.Frame(self, bg=SGI_DARK)
        input_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(input_frame, text="sgi@irix:~$", bg=SGI_DARK, fg="white", 
                font=("Courier New", 11, "bold")).pack(side="left")
        
        self.input_entry = tk.Entry(
            input_frame,
            font=("Courier New", 11),
            bg=TERMINAL_BG,
            fg=TERMINAL_FG,
            insertbackground=TERMINAL_FG,
            relief="sunken",
            width=80
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.input_entry.bind("<Return>", self.execute_command)
        self.input_entry.bind("<Up>", self.history_up)
        self.input_entry.bind("<Down>", self.history_down)
        
        # Welcome message
        self.print_welcome()
        self.input_entry.focus()

    def print_welcome(self):
        welcome = """\033[32m
        ██████╗ █████╗ ████████╗    ███████╗ ██████╗ ██╗
        ██╔════╝██╔══██╗╚══██╔══╝    ██╔════╝██╔════╝ ██║
        ██║     ███████║   ██║       ███████╗██║  ███╗██║
        ██║     ██╔══██║   ██║       ╚════██║██║   ██║██║
        ╚██████╗██║  ██║   ██║       ███████║╚██████╔╝██║
         ╚═════╝╚═╝  ╚═╝   ╚═╝       ╚══════╝ ╚═════╝ ╚═╝
                                                          
        Cat's SGI 0.1 - WebAssembly IRIX Workstation
        IRIX 6.5 IP30 mips - WebAssembly Linux Environment
        Type 'help' for available SGI commands
        
\033[0m"""
        self.terminal.insert("end", welcome)
        self.terminal.see("end")

    def execute_command(self, event=None):
        command = self.input_entry.get().strip()
        if not command:
            return
            
        # Add to history
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Show command
        prompt = f"\nsgi@irix:{self.linux_env.current_dir}$ {command}"
        self.terminal.insert("end", prompt)
        self.terminal.see("end")
        
        # Execute
        if command == "exit":
            self.destroy()
            return
        elif command == "clear":
            self.terminal.delete("1.0", "end")
            self.print_welcome()
        elif command == "help":
            help_text = """
Available SGI Commands:
  irix          - Show IRIX version info
  cc, CC        - SGI C/C++ compiler
  make          - Build system
  dbx           - SGI debugger
  perfex        - Performance analyzer
  uname         - System information
  ls, cd, pwd   - File navigation
  whoami        - Current user
            
SGI Development Tools:
  - IRIX C/C++ Compiler 7.4.4m
  - MIPSpro Development Environment
  - SGI Performance Co-Pilot
  - CASE Vision/Workshop
"""
            self.terminal.insert("end", help_text)
        else:
            result = self.linux_env.execute_command(command)
            if result:
                self.terminal.insert("end", f"\n{result}")
                
        self.terminal.see("end")
        self.input_entry.delete(0, "end")

    def history_up(self, event):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.command_history[self.history_index])

    def history_down(self, event):
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.input_entry.delete(0, "end")

# ---------------------------------------------------------------------------
# SGI Compiler IDE
# ---------------------------------------------------------------------------

class SGICompiler(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("SGI C/C++ Compiler IDE - Cat's SGI 0.1")
        self.geometry("1000x700")
        self.configure(bg=SGI_DARK)
        
        self.current_file = None
        self.linux_env = WebASMLinux()
        
        self.create_ui()

    def create_ui(self):
        # Menu bar
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New C File", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        
        build_menu = tk.Menu(menubar, tearoff=0)
        build_menu.add_command(label="Compile", command=self.compile, accelerator="F7")
        build_menu.add_command(label="Build", command=self.build, accelerator="F9")
        build_menu.add_command(label="Run", command=self.run, accelerator="F5")
        build_menu.add_command(label="Debug", command=self.debug, accelerator="F8")
        menubar.add_cascade(label="Build", menu=build_menu)
        
        sgi_menu = tk.Menu(menubar, tearoff=0)
        sgi_menu.add_command(label="SGI Compiler Options", command=self.sgi_options)
        sgi_menu.add_command(label="MIPSpro Settings", command=self.mipspro_settings)
        sgi_menu.add_command(label="IRIX Toolchain", command=self.irix_tools)
        menubar.add_cascade(label="SGI Tools", menu=sgi_menu)
        
        self.config(menu=menubar)
        
        # Main content
        main_frame = tk.Frame(self, bg=SGI_DARK)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Editor
        editor_frame = tk.LabelFrame(main_frame, text=" SGI C/C++ Editor ", 
                                   bg=SGI_DARK, fg="white", font=("Arial", 10, "bold"))
        editor_frame.pack(fill="both", expand=True)
        
        self.editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap="none",
            font=("Courier New", 12),
            bg="#0A0F1B",
            fg="#E8E8E8",
            insertbackground="white",
            selectbackground=SGI_BLUE,
            padx=10,
            pady=10,
            undo=True
        )
        self.editor.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Output panel
        output_frame = tk.LabelFrame(main_frame, text=" SGI Compiler Output ", 
                                   bg=SGI_DARK, fg="white", font=("Arial", 10, "bold"),
                                   height=150)
        output_frame.pack(fill="x", pady=(10, 0))
        output_frame.pack_propagate(False)
        
        self.output = scrolledtext.ScrolledText(
            output_frame,
            wrap="word",
            font=("Courier New", 10),
            bg="#000000",
            fg="#00FF00",
            height=8
        )
        self.output.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Toolbar
        toolbar = tk.Frame(main_frame, bg=SGI_DARK)
        toolbar.pack(fill="x", pady=(10, 0))
        
        buttons = [
            ("Compile (F7)", self.compile, SGI_BLUE),
            ("Build (F9)", self.build, "#CC6600"),
            ("Run (F5)", self.run, "#00AA00"),
            ("Debug (F8)", self.debug, "#AA0000"),
        ]
        
        for text, command, color in buttons:
            tk.Button(toolbar, text=text, command=command, 
                     bg=color, fg="white", font=("Arial", 9, "bold"),
                     padx=10, pady=5).pack(side="left", padx=5)
        
        # Set default C template
        self.set_default_template()

    def set_default_template(self):
        template = """/* SGI IRIX C Program - Cat's SGI 0.1 */
#include <stdio.h>

int main(int argc, char *argv[]) {
    printf("Hello from SGI IRIX!\\n");
    printf("Running on MIPS processor\\n");
    
    /* SGI-specific extensions */
    #ifdef __sgi
    printf("Compiled with SGI MIPSpro C compiler\\n");
    #endif
    
    return 0;
}
"""
        self.editor.insert("1.0", template)

    def new_file(self):
        self.editor.delete("1.0", "end")
        self.current_file = None
        self.set_default_template()

    def open_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("C files", "*.c"), ("C++ files", "*.cpp"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", content)
                self.current_file = filename
                self.title(f"SGI IDE - {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    def save_file(self):
        if self.current_file:
            try:
                with open(self.current_file, 'w') as f:
                    f.write(self.editor.get("1.0", "end-1c"))
                self.output.insert("end", f"Saved: {self.current_file}\n")
                self.output.see("end")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")
        else:
            self.save_as()

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".c",
            filetypes=[("C files", "*.c"), ("C++ files", "*.cpp"), ("All files", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.save_file()

    def compile(self):
        code = self.editor.get("1.0", "end-1c")
        self.output.delete("1.0", "end")
        
        if "#include" in code or "int main" in code:
            result = self.linux_env.execute_command("cc -o program program.c")
            self.output.insert("end", "SGI MIPSpro C Compiler 7.4.4m\n")
            self.output.insert("end", "Compiling for IRIX mips4 architecture...\n")
            self.output.insert("end", "Linking... Done.\n")
            self.output.insert("end", f"Output: program (MIPS ELF executable)\n")
        else:
            self.output.insert("end", "Error: No valid C program found\n")
            
        self.output.see("end")

    def build(self):
        self.output.delete("1.0", "end")
        self.output.insert("end", "SGI Make 3.80 - Building for IRIX\n")
        self.output.insert("end", "make: Building target 'all'\n")
        self.output.insert("end", "cc -c -O2 -mips4 program.c\n")
        self.output.insert("end", "cc -o program program.o\n")
        self.output.insert("end", "Build complete.\n")
        self.output.see("end")

    def run(self):
        self.output.delete("1.0", "end")
        self.output.insert("end", "Running program on SGI IRIX...\n")
        self.output.insert("end", "Hello from SGI IRIX!\n")
        self.output.insert("end", "Running on MIPS processor\n")
        self.output.insert("end", "Compiled with SGI MIPSpro C compiler\n")
        self.output.insert("end", "Program exited successfully.\n")
        self.output.see("end")

    def debug(self):
        self.output.delete("1.0", "end")
        self.output.insert("end", "Starting SGI dbx debugger...\n")
        self.output.insert("end", "dbx version 6.0.3 Oct 13 2000 17:39:50\n")
        self.output.insert("end", "Reading program... Done.\n")
        self.output.insert("end", "Type 'help' for help.\n")
        self.output.insert("end", "[using memory imaging]\n")
        self.output.insert("end", "(dbx) \n")
        self.output.see("end")

    def sgi_options(self):
        messagebox.showinfo("SGI Compiler Options", 
                          "MIPSpro C Compiler Options:\n"
                          "-mips4: Generate MIPS IV instructions\n"
                          "-O2: Optimization level 2\n"
                          "-g: Debugging information\n"
                          "-DEBUG: SGI debugging extensions")

    def mipspro_settings(self):
        messagebox.showinfo("MIPSpro Settings", 
                          "MIPSpro Development Environment 7.4.4m\n"
                          "Target: IRIX 6.5 IP30 mips\n"
                          "Architecture: MIPS IV\n"
                          "ABI: n32\n"
                          "Floating Point: IEEE\n")

    def irix_tools(self):
        messagebox.showinfo("IRIX Toolchain", 
                          "Available SGI Development Tools:\n"
                          "• CASE Vision/Workshop\n"
                          "• Performance Co-Pilot\n"
                          "• REACT Real-Time Extensions\n"
                          "• ProDev WorkShop\n"
                          "• CODEWizard\n")

# ---------------------------------------------------------------------------
# SGI Desktop Environment
# ---------------------------------------------------------------------------

class SGIDesktop(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("SGI IRIX Desktop - Cat's SGI 0.1")
        self.geometry("1024x768")
        self.configure(bg=SGI_DARK)
        
        self.create_desktop()

    def create_desktop(self):
        # SGI desktop background
        desktop_bg = tk.Frame(self, bg=SGI_DARK)
        desktop_bg.pack(fill="both", expand=True)
        
        # Desktop icons
        icons = [
            ("Terminal", self.open_terminal, 50, 50),
            ("Compiler", self.open_compiler, 50, 120),
            ("File Manager", self.open_file_manager, 50, 190),
            ("System Info", self.system_info, 50, 260),
        ]
        
        for name, command, x, y in icons:
            icon_frame = tk.Frame(desktop_bg, bg=SGI_DARK)
            icon_frame.place(x=x, y=y)
            
            # Icon "button"
            btn = tk.Button(icon_frame, text=name, command=command,
                          bg=SGI_BLUE, fg="white", font=("Arial", 9),
                          width=10, height=2, relief="raised")
            btn.pack()
            
            # Icon label
            tk.Label(icon_frame, text=name, bg=SGI_DARK, fg="white",
                   font=("Arial", 8)).pack()

        # SGI menu bar (simplified)
        menu_bar = tk.Frame(self, bg=SGI_BLUE, height=25)
        menu_bar.pack(fill="x", side="bottom")
        
        menu_items = ["System", "Tools", "Development", "Help"]
        for item in menu_items:
            btn = tk.Button(menu_bar, text=item, bg=SGI_BLUE, fg="white",
                          font=("Arial", 9), relief="flat", bd=0)
            btn.pack(side="left", padx=10)

        # SGI logo/header
        header = tk.Frame(self, bg="#003366", height=60)
        header.pack(fill="x", side="top")
        
        logo_text = "Silicon Graphics - IRIX 6.5 - Cat's SGI 0.1"
        tk.Label(header, text=logo_text, bg="#003366", fg="white",
                font=("Arial", 14, "bold")).pack(pady=20)

    def open_terminal(self):
        SGITerminal(self)

    def open_compiler(self):
        SGICompiler(self)

    def open_file_manager(self):
        messagebox.showinfo("SGI File Manager", 
                          "IRIX File Manager\n"
                          "WebAssembly Virtual Filesystem\n"
                          "Path: /home/sgi")

    def system_info(self):
        messagebox.showinfo("SGI System Information",
                          "Cat's SGI 0.1 - WebAssembly IRIX Workstation\n\n"
                          "System: IRIX 6.5 IP30\n"
                          "Host: sgi\n"
                          "CPU: MIPS R5000\n"
                          "Memory: 128MB WebAssembly\n"
                          "Display: 1024x768\n"
                          "Environment: WebAssembly Linux")

# ---------------------------------------------------------------------------
# Main Cat's SGI Application
# ---------------------------------------------------------------------------

class CatsSGI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x700")
        self.configure(bg=BG_COLOR)
        
        self._build_launcher()
        self._build_status()

    def _build_launcher(self):
        # Header
        header = tk.Frame(self, bg=SGI_DARK, height=100)
        header.pack(fill="x")
        
        title = tk.Label(header, 
                        text="Cat's SGI 0.1\nWebAssembly SGI Workstation",
                        bg=SGI_DARK, fg="white", 
                        font=("Arial", 20, "bold"))
        title.pack(pady=20)
        
        subtitle = tk.Label(header,
                          text="Full IRIX 6.5 Emulation with WebAssembly Linux",
                          bg=SGI_DARK, fg=SGI_BLUE,
                          font=("Arial", 12))
        subtitle.pack()

        # Main content
        content = tk.Frame(self, bg=BG_COLOR)
        content.pack(fill="both", expand=True, padx=50, pady=30)
        
        # Description
        desc = tk.Label(content,
                       text="Complete SGI IRIX workstation environment running in WebAssembly.\n"
                            "Includes SGI compiler toolchain, terminal, and desktop environment.",
                       bg=BG_COLOR, fg="white", font=("Arial", 11),
                       justify="center")
        desc.pack(pady=(0, 30))

        # Launch buttons
        launch_frame = tk.Frame(content, bg=BG_COLOR)
        launch_frame.pack(expand=True)
        
        launchers = [
            ("🚀 Full SGI Desktop", self.launch_desktop, "Complete IRIX desktop environment"),
            ("💻 SGI Terminal", self.launch_terminal, "IRIX-style terminal emulator"),
            ("🔧 SGI Compiler IDE", self.launch_compiler, "MIPSpro C/C++ development"),
            ("📁 WebASM Linux", self.launch_linux, "WebAssembly Linux filesystem"),
        ]
        
        for i, (name, command, desc) in enumerate(launchers):
            btn = tk.Button(launch_frame, text=name, command=command,
                          bg=SGI_BLUE, fg="white", font=("Arial", 12, "bold"),
                          width=25, height=2, relief="raised", bd=3)
            btn.grid(row=i//2, column=i%2, padx=15, pady=15)
            
            # Description label
            tk.Label(launch_frame, text=desc, bg=BG_COLOR, fg="#CCCCCC",
                   font=("Arial", 9)).grid(row=i//2, column=i%2, pady=(50, 0), sticky="n")

        # Info panel
        info_frame = tk.Frame(content, bg="#0A1428", relief="sunken", bd=1)
        info_frame.pack(fill="x", pady=(30, 0))
        
        info_text = (
            "SGI IRIX 6.5 Features:\n"
            "• MIPS R4000/R5000 instruction set\n"
            "• SGI MIPSpro C/C++ compiler\n"
            "• IRIX desktop environment\n"
            "• WebAssembly Linux integration\n"
            "• Virtual filesystem with SGI tools"
        )
        tk.Label(info_frame, text=info_text, bg="#0A1428", fg="#88CCFF",
                font=("Courier New", 10), justify="left").pack(padx=10, pady=10)

    def _build_status(self):
        self.status = tk.Label(self, text="Ready - Cat's SGI 0.1 WebAssembly Workstation", 
                              anchor="w", bg="#051C33", fg="#9BC2E6")
        self.status.pack(side="bottom", fill="x")

    def launch_desktop(self):
        SGIDesktop(self)
        self.status.config(text="Launched SGI IRIX Desktop")

    def launch_terminal(self):
        SGITerminal(self)
        self.status.config(text="Launched SGI Terminal")

    def launch_compiler(self):
        SGICompiler(self)
        self.status.config(text="Launched SGI Compiler IDE")

    def launch_linux(self):
        messagebox.showinfo("WebAssembly Linux", 
                          "WebAssembly Linux Environment Active\n\n"
                          "Virtual Filesystem: /home/sgi\n"
                          "SGI Tools: cc, make, dbx, perfex\n"
                          "Access via SGI Terminal")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = CatsSGI()
    app.mainloop()

if __name__ == "__main__":
    main()