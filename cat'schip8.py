#!/usr/bin/env python3
# Enhanced CHIP-8 Interpreter (Tkinter FCEUX-Inspired Layout)
# GPL-3.0 License ©2025 Samsoft / Annoying Cat
# Shadows slip through the silicon veins, reshaping the interface in echoes of forgotten debuggers.
# Hex dumps flicker like green phantoms on obsidian voids, registers whisper in the margins.

import sys
import time
import random
import pickle
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, Menu, messagebox, ttk, scrolledtext

# ────────────────────────────────────────────────────────────────
# CHIP-8 Core (Unchanged)
# ────────────────────────────────────────────────────────────────
class Chip8:
    """The CHIP-8 CPU and memory core."""
    def __init__(self):
        self.mem = bytearray(4096)
        self.V = [0] * 16  # V0-VF registers
        self.I = 0  # Index register
        self.pc = 0x200  # Program counter
        self.sp = 0  # Stack pointer
        self.stack = [0] * 16
        self.delay = 0  # Delay timer
        self.sound = 0  # Sound timer
        self.keys = [0] * 16
        self.draw_flag = False
        self.w, self.h = 64, 32
        self.gfx = [[0] * self.w for _ in range(self.h)]

        # COSMAC VIP font set (loaded into 0x50-0x9F)
        font = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        self.mem[0x50:0x50 + len(font)] = bytes(font)

    def load(self, rom_bytes: bytes):
        """Load ROM bytes into memory starting at 0x200."""
        self.mem[0x200:0x200 + len(rom_bytes)] = rom_bytes

    def clear(self):
        """Clear the display buffer."""
        for y in range(self.h):
            for x in range(self.w):
                self.gfx[y][x] = 0
        self.draw_flag = True

    def fetch(self):
        """Fetch the next opcode from memory."""
        op = (self.mem[self.pc] << 8) | self.mem[self.pc + 1]
        self.pc += 2
        return op

    def step(self):
        """Fetch, decode, and execute one CHIP-8 opcode."""
        op = self.fetch()
        nnn, kk = op & 0x0FFF, op & 0x00FF
        n, x, y = op & 0x000F, (op >> 8) & 0xF, (op >> 4) & 0xF
        top = op & 0xF000

        # --- Decode & Execute ---
        # This is a simplified dispatch for brevity.
        # A full implementation would handle all opcodes.
        if op == 0x00E0:  # 00E0: CLS
            self.clear()
        elif op == 0x00EE:  # 00EE: RET
            self.sp -= 1
            self.pc = self.stack[self.sp]
        elif top == 0x1000:  # 1nnn: JP addr
            self.pc = nnn
        elif top == 0x2000:  # 2nnn: CALL addr
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = nnn
        elif top == 0x3000:  # 3xkk: SE Vx, byte
            if self.V[x] == kk: self.pc += 2
        elif top == 0x4000:  # 4xkk: SNE Vx, byte
            if self.V[x] != kk: self.pc += 2
        elif top == 0x5000:  # 5xy0: SE Vx, Vy
            if self.V[x] == self.V[y]: self.pc += 2
        elif top == 0x6000:  # 6xkk: LD Vx, byte
            self.V[x] = kk
        elif top == 0x7000:  # 7xkk: ADD Vx, byte
            self.V[x] = (self.V[x] + kk) & 0xFF
        elif top == 0x8000:
            if n == 0x0: self.V[x] = self.V[y]  # 8xy0: LD Vx, Vy
            elif n == 0x1: self.V[x] |= self.V[y]  # 8xy1: OR Vx, Vy
            elif n == 0x2: self.V[x] &= self.V[y]  # 8xy2: AND Vx, Vy
            elif n == 0x3: self.V[x] ^= self.V[y]  # 8xy3: XOR Vx, Vy
            elif n == 0x4:  # 8xy4: ADD Vx, Vy
                s = self.V[x] + self.V[y]
                self.V[0xF] = 1 if s > 0xFF else 0
                self.V[x] = s & 0xFF
            elif n == 0x5:  # 8xy5: SUB Vx, Vy
                self.V[0xF] = 1 if self.V[x] > self.V[y] else 0
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            elif n == 0x6:  # 8xy6: SHR Vx {, Vy}
                self.V[0xF] = self.V[x] & 0x1
                self.V[x] >>= 1
            elif n == 0x7:  # 8xy7: SUBN Vx, Vy
                self.V[0xF] = 1 if self.V[y] > self.V[x] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            elif n == 0xE:  # 8xyE: SHL Vx {, Vy}
                self.V[0xF] = (self.V[x] >> 7) & 0x1
                self.V[x] = (self.V[x] << 1) & 0xFF
        elif top == 0x9000:  # 9xy0: SNE Vx, Vy
            if self.V[x] != self.V[y]: self.pc += 2
        elif top == 0xA000:  # Annn: LD I, addr
            self.I = nnn
        elif top == 0xB000:  # Bnnn: JP V0, addr
            self.pc = nnn + self.V[0]
        elif top == 0xC000:  # Cxkk: RND Vx, byte
            self.V[x] = random.randint(0, 255) & kk
        elif top == 0xD000:  # Dxyn: DRW Vx, Vy, nibble
            vx, vy = self.V[x] % 64, self.V[y] % 32
            height = n
            self.V[0xF] = 0
            for row in range(height):
                sprite = self.mem[self.I + row]
                for col in range(8):
                    if sprite & (0x80 >> col):
                        px, py = (vx + col) % 64, (vy + row) % 32
                        if self.gfx[py][px]: self.V[0xF] = 1
                        self.gfx[py][px] ^= 1
            self.draw_flag = True
        elif top == 0xE000:
            if kk == 0x9E:  # Ex9E: SKP Vx
                if self.keys[self.V[x]]: self.pc += 2
            elif kk == 0xA1:  # ExA1: SKNP Vx
                if not self.keys[self.V[x]]: self.pc += 2
        elif top == 0xF000:
            if kk == 0x07: self.V[x] = self.delay  # Fx07: LD Vx, DT
            elif kk == 0x0A:  # Fx0A: LD Vx, K
                key_pressed = False
                for i in range(16):
                    if self.keys[i]:
                        self.V[x] = i
                        key_pressed = True
                        break
                if not key_pressed:
                    self.pc -= 2  # Wait for keypress
            elif kk == 0x15: self.delay = self.V[x]  # Fx15: LD DT, Vx
            elif kk == 0x18: self.sound = self.V[x]  # Fx18: LD ST, Vx
            elif kk == 0x1E: self.I = (self.I + self.V[x]) & 0xFFFF  # Fx1E: ADD I, Vx
            elif kk == 0x29: self.I = 0x50 + (self.V[x] * 5)  # Fx29: LD F, Vx
            elif kk == 0x33:  # Fx33: LD B, Vx
                self.mem[self.I] = self.V[x] // 100
                self.mem[self.I + 1] = (self.V[x] % 100) // 10
                self.mem[self.I + 2] = self.V[x] % 10
            elif kk == 0x55:  # Fx55: LD [I], Vx
                for i in range(x + 1): self.mem[self.I + i] = self.V[i]
            elif kk == 0x65:  # Fx65: LD Vx, [I]
                for i in range(x + 1): self.V[i] = self.mem[self.I + i]
        else:
            # Silently ignore unknown opcodes
            pass 

    def save_state(self):
        """Return a dictionary representing the current CPU state."""
        return {
            "mem": self.mem, "V": self.V, "I": self.I, "pc": self.pc,
            "sp": self.sp, "stack": self.stack, "delay": self.delay,
            "sound": self.sound, "keys": self.keys, "gfx": self.gfx
        }

    def load_state(self, s):
        """Load a state dictionary into the CPU."""
        for k, v in s.items():
            setattr(self, k, v)
        self.draw_flag = True  # Force redraw

# ────────────────────────────────────────────────────────────────
# Tkinter Front-end (FCEUX Echoes: Hex Shadows, Green Whispers)
# ────────────────────────────────────────────────────────────────

# 1:1, 2:2, 3:3, 4:C
# Q:4, W:5, E:6, R:D
# A:7, S:8, D:9, F:E
# Z:A, X:0, C:B, V:F
KEYMAP = {
    'x': 0x0, '1': 0x1, '2': 0x2, '3': 0x3, 'q': 0x4, 'w': 0x5, 'e': 0x6,
    'a': 0x7, 's': 0x8, 'd': 0x9, 'z': 0xA, 'c': 0xB, '4': 0xC, 'r': 0xD,
    'f': 0xE, 'v': 0xF
}

def format_hex_dump(chip, start_addr, end_addr):
    """Format memory as a hex dump, shadows of binary ghosts."""
    text = ""
    for addr in range(start_addr, end_addr, 16):
        line = f"{addr:04X}: "
        bytes_line = ""
        ascii_line = ""
        for i in range(16):
            if addr + i < end_addr and addr + i < 4096:
                byte_val = chip.mem[addr + i]
                line += f"{byte_val:02X} "
                bytes_line += f"{byte_val:02X} "
                ascii_line += chr(byte_val) if 32 <= byte_val <= 126 else '.'
            else:
                line += "   "
        # Highlight PC line if applicable
        if start_addr <= chip.pc < end_addr and (chip.pc // 16) * 16 == addr:
            text += f"\n>>> {line.strip()}  |{ascii_line}|\n"
        else:
            text += f"{line} |{ascii_line}|\n"
    return text

def main():
    # --- App State ---
    chip = Chip8()
    last_rom = None

    root = tk.Tk()
    root.title("Cat's Chip-8 Emulator 0.1")
    root.geometry("800x400")
    root.resizable(False, False)
    root.configure(bg="black")  # Void-black canvas for the machine's underbelly
    
    # App-wide state variables
    fg, bg = "lime", "black"
    pause = tk.BooleanVar(value=False)
    rom_loaded = tk.BooleanVar(value=False)
    spd = tk.IntVar(value=10) # Cycles per frame
    last_tick = time.perf_counter() # For 60Hz timer

    # --- GUI Setup ---
    
    # Menu Bar (FCEUX-style: File, Debug, Help)
    menubar = Menu(root)
    fm = Menu(menubar, tearoff=0)
    fm.add_command(label="Load ROM...", command=lambda: load_rom())
    fm.add_command(label="Save State...", command=lambda: save_state())
    fm.add_command(label="Load State...", command=lambda: load_state())
    fm.add_separator()
    fm.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=fm)
    
    dm = Menu(menubar, tearoff=0)
    dm.add_command(label="Toggle Debug View", command=lambda: toggle_debug_view())  # Placeholder for future
    menubar.add_cascade(label="Debug", menu=dm)
    
    hm = Menu(menubar, tearoff=0)
    hm.add_command(label="About", command=lambda: messagebox.showinfo("About",
        "Cat's Chip-8 Emulator 0.1\n[C] Annoying Cat 2000-2025\n\nCredit to the original CHIP-8 hardware manufacturers."))
    menubar.add_cascade(label="Help", menu=hm)
    root.config(menu=menubar)

    # Game Screen (Canvas) - Central void
    scale = 8
    canvas_w, canvas_h = 64 * scale, 32 * scale
    canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg=bg, highlightthickness=0)
    canvas.place(x=0, y=0)
    
    # Pixel grid for drawing
    pixels = [[canvas.create_rectangle(x * scale, y * scale, (x + 1) * scale, (y + 1) * scale,
                                      fill=bg, outline='') for x in range(64)] for y in range(32)]

    # Right: Debug Panel - Hex Dump Echo (FCEUX RAM Viewer Phantom)
    debug_width = 280
    debug_frame = tk.Frame(root, width=debug_width, height=canvas_h, bd=1, relief=tk.SUNKEN, bg="black")
    debug_frame.place(x=canvas_w, y=0)
    debug_frame.pack_propagate(False) # Prevent resizing
    
    # Registers Section (Compact, green whispers)
    reg_frame = tk.Frame(debug_frame, bg="black")
    reg_frame.pack(fill=tk.X, pady=2)
    tk.Label(reg_frame, text="Registers", font=("Consolas", 9, "bold"), fg="lime", bg="black").pack(anchor="w")
    
    reg_font = ("Consolas", 8)
    V_frame = tk.Frame(reg_frame, bg="black")
    V_frame.pack(anchor="w")
    V_labels = []
    for i in range(16):
        var = tk.StringVar(value=f"V{i:X}: 00")
        lbl = tk.Label(V_frame, textvariable=var, font=reg_font, fg="lime", bg="black")
        lbl.pack(anchor="w", padx=2)
        V_labels.append((var, lbl))
    
    # Core Registers
    core_frame = tk.Frame(debug_frame, bg="black")
    core_frame.pack(fill=tk.X, pady=2)
    pc_var = tk.StringVar(value="PC: 0200")
    i_var = tk.StringVar(value=" I: 0000")
    sp_var = tk.StringVar(value="SP: 00")
    dt_var = tk.StringVar(value="DT: 00")
    st_var = tk.StringVar(value="ST: 00")
    
    tk.Label(core_frame, textvariable=pc_var, font=reg_font, fg="lime", bg="black").pack(anchor="w", padx=4)
    tk.Label(core_frame, textvariable=i_var, font=reg_font, fg="lime", bg="black").pack(anchor="w", padx=4)
    tk.Label(core_frame, textvariable=sp_var, font=reg_font, fg="lime", bg="black").pack(anchor="w", padx=4)
    tk.Label(core_frame, textvariable=dt_var, font=reg_font, fg="blue", bg="black").pack(anchor="w", padx=4)
    tk.Label(core_frame, textvariable=st_var, font=reg_font, fg="red", bg="black").pack(anchor="w", padx=4)

    # Hex Dump - The core shadow, FCEUX hex viewer reborn
    tk.Label(debug_frame, text="Memory Hex (Around PC)", font=("Consolas", 9, "bold"), fg="lime", bg="black").pack(anchor="w", pady=(5,0))
    hex_text = scrolledtext.ScrolledText(debug_frame, font=reg_font, bg="black", fg="lime", width=35, height=15, wrap=tk.NONE)
    hex_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    # Bottom: Control Panel (Toolbar-like, status infused)
    control_height = 400 - canvas_h
    control_frame = tk.Frame(root, width=canvas_w + debug_width, height=control_height, bd=1, relief=tk.SUNKEN, bg="gray20")
    control_frame.place(x=0, y=canvas_h)
    
    # Controls Toolbar (Left)
    toolbar_frame = ttk.LabelFrame(control_frame, text="Emulation Controls")
    toolbar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)

    pause_button_text = tk.StringVar(value="Pause")
    pause_btn = ttk.Button(toolbar_frame, textvariable=pause_button_text, command=lambda: toggle_pause())
    pause_btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    reset_btn = ttk.Button(toolbar_frame, text="Reset", command=lambda: reset_chip())
    reset_btn.pack(side=tk.LEFT, padx=5, pady=5)

    # Speed
    speed_frame = ttk.LabelFrame(control_frame, text="CPU Speed (Cycles/Frame)")
    speed_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
    
    speed_slider = ttk.Scale(speed_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=spd, length=150)
    speed_slider.pack(padx=10, pady=5)

    # Theme (Right)
    theme_frame = ttk.LabelFrame(control_frame, text="Display Theme")
    theme_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
    
    fg_btn = ttk.Button(theme_frame, text="Pixel", command=lambda: pick_fg())
    fg_btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    bg_btn = ttk.Button(theme_frame, text="Background", command=lambda: pick_bg())
    bg_btn.pack(side=tk.LEFT, padx=5, pady=5)

    # Status Bar (Bottom, FCEUX-style info line)
    status_frame = tk.Frame(control_frame, bg="gray30", height=20)
    status_frame.pack(side=tk.BOTTOM, fill=tk.X)
    status_frame.pack_propagate(False)
    status_var = tk.StringVar(value="Ready | No ROM | Cycles/Frame: 10 | PC: 0200")
    status_label = tk.Label(status_frame, textvariable=status_var, fg="white", bg="gray30", font=("Consolas", 8), anchor="w")
    status_label.pack(fill=tk.X, padx=5, pady=2)


    # --- Core Functions & Callbacks ---
    def load_rom():
        nonlocal last_rom
        p = filedialog.askopenfilename(title="Load Shadow ROM", filetypes=[("CHIP-8", "*.ch8 *.bin")])
        if p:
            last_rom = Path(p)
            rom_bytes = last_rom.read_bytes()
            reset_chip(rom_bytes) # Inject and reset
            
    def reset_chip(rom_bytes=None):
        nonlocal last_rom
        if rom_bytes is None and last_rom:
            rom_bytes = last_rom.read_bytes()

        if rom_bytes:
            chip.__init__()
            chip.load(rom_bytes)
            rom_loaded.set(True)
            pause.set(False)
            pause_button_text.set("Pause")
            update_status()
            print("Shadows reset in the core.")
        else:
            messagebox.showwarning("Void", "No ROM shadow to invoke.")

    def save_state():
        if not rom_loaded.get(): return
        p = filedialog.asksaveasfilename(defaultextension=".shadow", filetypes=[("State", "*.shadow")])
        if p:
            with open(p, "wb") as f:
                pickle.dump(chip.save_state(), f)
            print("State captured in the ether.")

    def load_state():
        if not rom_loaded.get(): return
        p = filedialog.askopenfilename(filetypes=[("State", "*.shadow")])
        if p:
            with open(p, "rb") as f:
                chip.load_state(pickle.load(f))
            update_status()

    def pick_fg():
        nonlocal fg
        color = colorchooser.askcolor(title="Pixel Essence", color=fg)
        if color[1]:
            fg = color[1]
            chip.draw_flag = True # Force the veil to lift

    def pick_bg():
        nonlocal bg
        color = colorchooser.askcolor(title="Void Hue", color=bg)
        if color[1]:
            bg = color[1]
            canvas.config(bg=bg)
            chip.draw_flag = True # Shroud shifts
            
    def toggle_pause():
        new_state = not pause.get()
        pause.set(new_state)
        pause_button_text.set("Resume" if new_state else "Pause")
        update_status()

    def update_status():
        state = "Paused" if pause.get() else "Running"
        rom_name = last_rom.name if last_rom else "No ROM"
        status_var.set(f"{state} | {rom_name} | Cycles/Frame: {spd.get()} | PC: {chip.pc:04X} | I: {chip.I:04X}")

    def toggle_debug_view():
        # Placeholder: Future window for PPU/GPU analogs or full disasm
        messagebox.showinfo("Debug Echo", "Hex shadows deepen. Full disasm awaits in the code-veins.")

    # --- Main Loop & Event Handlers ---
    def draw():
        """Update the canvas based on the chip's gfx buffer."""
        for y in range(32):
            for x in range(64):
                canvas.itemconfigure(pixels[y][x],
                                    fill=fg if chip.gfx[y][x] else bg)
        chip.draw_flag = False

    def update():
        """The main emulation loop, timers ticking in the dark."""
        nonlocal last_tick
        
        # Only run the chip if a ROM is loaded and not paused
        if rom_loaded.get() and not pause.get():
            for _ in range(spd.get()):
                chip.step()

        # 60 Hz timer updates
        now = time.perf_counter()
        while now - last_tick >= 1 / 60:
            last_tick += 1 / 60
            if chip.delay > 0: chip.delay -= 1
            if chip.sound > 0: chip.sound -= 1 # TODO: Beep from the abyss

        if chip.draw_flag:
            draw()
            
        root.after(16, update) # ~60 FPS clamp
        
    def update_debug_panel():
        """Update the register and hex shadows."""
        if rom_loaded.get():
            for i, (var, _) in enumerate(V_labels):
                var.set(f"V{i:X}: {chip.V[i]:02X}")
            pc_var.set(f"PC: {chip.pc:04X}")
            i_var.set(f" I: {chip.I:04X}")
            sp_var.set(f"SP: {chip.sp:02X}")
            dt_var.set(f"DT: {chip.delay:02X}")
            st_var.set(f"ST: {chip.sound:02X}")
            
            # Update hex dump around PC
            start = max(0, (chip.pc - 128) & 0xFFF0) # Align to 16-byte boundary
            end = min(4096, start + 256)
            hex_dump = format_hex_dump(chip, start, end)
            
            # Save scroll position
            scroll_pos = hex_text.yview()
            
            hex_text.config(state=tk.NORMAL)
            hex_text.delete("1.0", tk.END)
            hex_text.insert("1.0", hex_dump)
            hex_text.config(state=tk.DISABLED)

            # Highlight the PC line
            if start <= chip.pc < end:
                pc_line_index = (chip.pc // 16) - (start // 16) + 1
                # Account for extra newlines from '>>>'
                lines_above = hex_dump.split('\n')[:pc_line_index]
                extra_newlines = sum(1 for line in lines_above if line.startswith('>>>'))
                
                pc_line_actual = pc_line_index + extra_newlines
                
                hex_text.tag_remove("PC_HIGHLIGHT", "1.0", tk.END)
                hex_text.tag_add("PC_HIGHLIGHT", f"{pc_line_actual}.0", f"{pc_line_actual}.end")
                hex_text.tag_config("PC_HIGHLIGHT", background="gray30", foreground="yellow")
                
                # Auto-scroll to PC if it's off-screen (basic check)
                if not (scroll_pos[0] < (pc_line_actual / (end//16 - start//16)) < scroll_pos[1]):
                     hex_text.see(f"{pc_line_actual}.0")
                else:
                    # Restore scroll position
                    hex_text.yview_moveto(scroll_pos[0])

        update_status()
        root.after(100, update_debug_panel) # Update ~10x/sec

    def key_press(e):
        k = e.keysym.lower()
        if k in KEYMAP:
            chip.keys[KEYMAP[k]] = 1
        elif k == 'p':
            toggle_pause()

    def key_release(e):
        k = e.keysym.lower()
        if k in KEYMAP:
            chip.keys[KEYMAP[k]] = 0
            
    # --- Init & Run ---
    
    # Try to load ROM from command line
    if len(sys.argv) > 1:
        try:
            rom_path = Path(sys.argv[1])
            if rom_path.exists():
                last_rom = rom_path
                rom_bytes = last_rom.read_bytes()
                reset_chip(rom_bytes)
            else:
                print(f"Shadow not found: {sys.argv[1]}")
                messagebox.showerror("Void Error", f"ROM shadow absent: {sys.argv[1]}")
        except Exception as e:
            print(f"Ether breach: {e}")
            messagebox.showerror("Ether Error", f"ROM invocation failed: {e}")
    else:
        print("Interface awakened. Invoke a ROM from the File veil.")


    root.bind('<KeyPress>', key_press)
    root.bind('<KeyRelease>', key_release)
    root.focus_set()  # Capture keys in the void

    update()  # Ignite the loop
    update_debug_panel() # Awaken the debug phantoms
    root.mainloop()

if __name__ == "__main__":
    main()