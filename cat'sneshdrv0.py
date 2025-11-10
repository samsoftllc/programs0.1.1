#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Cat's CHIP-8 Emu 0.1.0 — Tkinter-based CHIP‑8 emulator
# (C) 2025 Samsoft Studios and contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Nintendo is a trademark of Nintendo Co., Ltd. This project is not
# affiliated with or endorsed by Nintendo. CHIP‑8 is a virtual machine
# originally used on 1970s hobbyist computers (e.g., COSMAC VIP).
#
# Name:  Cat's CHIP‑8 Emu 0.1.0  [C] Samsoft — Tailored for Windows & macOS — [C] GPL‑3 — [C] Nintendo (trademark notice only)
# File:  cats_chip8_emu.py

import sys
import os
import struct
import random
import argparse
import time
from tkinter import (
    Tk, Canvas, Frame, BOTH, LEFT, RIGHT, X, Y, BOTTOM, TOP, StringVar,
    Label, Button, Scale, HORIZONTAL, filedialog, messagebox, Menu
)

VERSION = "Cat's CHIP‑8 Emu 0.1.0 (GPL‑3.0-or-later)"
WINDOW_TITLE_BASE = "Cat's CHIP-8 Emu 0.1.0 — [C] Samsoft — GPL‑3"

# -------------------------
# CHIP-8 Core
# -------------------------

class Chip8:
    """
    Minimal, correct CHIP‑8 interpreter core.

    Implements:
      - Memory 4 KiB
      - 16 general registers V0..VF (VF is carry/borrow/flag)
      - I register, PC, stack (16 levels)
      - Delay & sound timers at 60 Hz
      - 64x32 monochrome display
      - 16-key hex keypad
    """
    WIDTH = 64
    HEIGHT = 32
    MEM_SIZE = 4096
    ROM_LOAD_ADDR = 0x200
    FONT_ADDR = 0x050  # conventional location

    FONTSET = [
        0xF0,0x90,0x90,0x90,0xF0,  # 0
        0x20,0x60,0x20,0x20,0x70,  # 1
        0xF0,0x10,0xF0,0x80,0xF0,  # 2
        0xF0,0x10,0xF0,0x10,0xF0,  # 3
        0x90,0x90,0xF0,0x10,0x10,  # 4
        0xF0,0x80,0xF0,0x10,0xF0,  # 5
        0xF0,0x80,0xF0,0x90,0xF0,  # 6
        0xF0,0x10,0x20,0x40,0x40,  # 7
        0xF0,0x90,0xF0,0x90,0xF0,  # 8
        0xF0,0x90,0xF0,0x10,0xF0,  # 9
        0xF0,0x90,0xF0,0x90,0x90,  # A
        0xE0,0x90,0xE0,0x90,0xE0,  # B
        0xF0,0x80,0x80,0x80,0xF0,  # C
        0xE0,0x90,0x90,0x90,0xE0,  # D
        0xF0,0x80,0xF0,0x80,0xF0,  # E
        0xF0,0x80,0xF0,0x80,0x80   # F
    ]

    def __init__(self, shift_quirk=False, mem_quirk=False):
        # Quirks:
        # shift_quirk: 8XY6/8XYE use Vy as source (original) vs Vx (modern). False => modern.
        # mem_quirk: FX55/FX65 don't increment I (original) vs increment I (modern). False => modern (increments).
        self.shift_quirk = shift_quirk
        self.mem_quirk = mem_quirk
        self.reset(hard=True)

    def reset(self, hard=False):
        self.memory = [0] * self.MEM_SIZE
        self.V = [0] * 16
        self.I = 0
        self.pc = self.ROM_LOAD_ADDR
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.gfx = [0] * (self.WIDTH * self.HEIGHT)  # 1D framebuffer
        self.keypad = [0] * 16
        self.draw_flag = True
        self.wait_key_reg = None
        # Load font
        for i, b in enumerate(self.FONTSET):
            self.memory[self.FONT_ADDR + i] = b
        if not hard and getattr(self, "_rom_bytes", None):
            # Soft reset keeps last ROM resident
            self.load_rom_bytes(self._rom_bytes)

    def load_rom_bytes(self, rom_bytes: bytes):
        """Load ROM bytes into memory at 0x200 and reset registers/PC."""
        if len(rom_bytes) > (self.MEM_SIZE - self.ROM_LOAD_ADDR):
            raise ValueError("ROM too large for CHIP‑8 memory")
        # Clear program area
        for i in range(self.ROM_LOAD_ADDR, self.MEM_SIZE):
            self.memory[i] = 0
        for i, b in enumerate(rom_bytes):
            self.memory[self.ROM_LOAD_ADDR + i] = b
        self.pc = self.ROM_LOAD_ADDR
        self.V = [0] * 16
        self.I = 0
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.gfx = [0] * (self.WIDTH * self.HEIGHT)
        self.draw_flag = True
        self.wait_key_reg = None
        self._rom_bytes = bytes(rom_bytes)

    # --------- Helpers ---------

    def _rand_byte(self):
        return random.randint(0, 255)

    def _get_pixel(self, x, y):
        if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
            return self.gfx[y * self.WIDTH + x]
        return 0

    def _xor_pixel(self, x, y, val):
        """XOR a pixel at (x,y) with val (0/1), set VF if collision."""
        if not (0 <= x < self.WIDTH and 0 <= y < self.HEIGHT):
            return
        idx = y * self.WIDTH + x
        before = self.gfx[idx]
        after = before ^ val
        self.gfx[idx] = after
        if before == 1 and after == 0:
            self.V[0xF] = 1

    # --------- Execution ---------

    def cycle(self):
        """Fetch, decode, execute a single opcode."""
        # If waiting for key (Fx0A), stall by re-executing same opcode
        opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
        self.pc = (self.pc + 2) & 0xFFF

        nnn = opcode & 0x0FFF
        n = opcode & 0x000F
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        kk = opcode & 0x00FF

        if opcode == 0x00E0:
            # CLS
            self.gfx = [0] * (self.WIDTH * self.HEIGHT)
            self.draw_flag = True
            return
        elif opcode == 0x00EE:
            # RET
            if not self.stack:
                # Underflow protection; ignore
                return
            self.pc = self.stack.pop()
            return
        elif opcode & 0xF000 == 0x0000:
            # 0NNN - SYS (ignored)
            return
        elif opcode & 0xF000 == 0x1000:
            # 1NNN - JP addr
            self.pc = nnn
            return
        elif opcode & 0xF000 == 0x2000:
            # 2NNN - CALL addr
            if len(self.stack) >= 16:
                return  # overflow ignore
            self.stack.append(self.pc)
            self.pc = nnn
            return
        elif opcode & 0xF000 == 0x3000:
            # 3XKK - SE Vx, byte
            if self.V[x] == kk:
                self.pc += 2
            return
        elif opcode & 0xF000 == 0x4000:
            # 4XKK - SNE Vx, byte
            if self.V[x] != kk:
                self.pc += 2
            return
        elif opcode & 0xF00F == 0x5000:
            # 5XY0 - SE Vx, Vy
            if self.V[x] == self.V[y]:
                self.pc += 2
            return
        elif opcode & 0xF000 == 0x6000:
            # 6XKK - LD Vx, kk
            self.V[x] = kk
            return
        elif opcode & 0xF000 == 0x7000:
            # 7XKK - ADD Vx, kk
            self.V[x] = (self.V[x] + kk) & 0xFF
            return
        elif opcode & 0xF00F == 0x8000:
            # 8XY0 - LD Vx, Vy
            self.V[x] = self.V[y]
            return
        elif opcode & 0xF00F == 0x8001:
            # 8XY1 - OR Vx, Vy
            self.V[x] |= self.V[y]
            self.V[0xF] = 0
            return
        elif opcode & 0xF00F == 0x8002:
            # 8XY2 - AND Vx, Vy
            self.V[x] &= self.V[y]
            self.V[0xF] = 0
            return
        elif opcode & 0xF00F == 0x8003:
            # 8XY3 - XOR Vx, Vy
            self.V[x] ^= self.V[y]
            self.V[0xF] = 0
            return
        elif opcode & 0xF00F == 0x8004:
            # 8XY4 - ADD Vx, Vy with carry
            res = self.V[x] + self.V[y]
            self.V[0xF] = 1 if res > 0xFF else 0
            self.V[x] = res & 0xFF
            return
        elif opcode & 0xF00F == 0x8005:
            # 8XY5 - SUB Vx, Vy (Vx = Vx - Vy)
            self.V[0xF] = 1 if self.V[x] >= self.V[y] else 0
            self.V[x] = (self.V[x] - self.V[y]) & 0xFF
            return
        elif opcode & 0xF00F == 0x8007:
            # 8XY7 - SUBN Vx, Vy (Vx = Vy - Vx)
            self.V[0xF] = 1 if self.V[y] >= self.V[x] else 0
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            return
        elif opcode & 0xF00F == 0x8006:
            # 8XY6 - SHR (modern: Vx >>= 1; VF = old LSB)
            if self.shift_quirk:
                src = self.V[y]
                self.V[0xF] = src & 0x1
                self.V[x] = (src >> 1) & 0xFF
            else:
                self.V[0xF] = self.V[x] & 0x1
                self.V[x] >>= 1
            return
        elif opcode & 0xF00F == 0x800E:
            # 8XYE - SHL (modern: Vx <<= 1; VF = old MSB)
            if self.shift_quirk:
                src = self.V[y]
                self.V[0xF] = 1 if (src & 0x80) else 0
                self.V[x] = (src << 1) & 0xFF
            else:
                self.V[0xF] = 1 if (self.V[x] & 0x80) else 0
                self.V[x] = (self.V[x] << 1) & 0xFF
            return
        elif opcode & 0xF00F == 0x9000:
            # 9XY0 - SNE Vx, Vy
            if self.V[x] != self.V[y]:
                self.pc += 2
            return
        elif opcode & 0xF000 == 0xA000:
            # ANNN - LD I, addr
            self.I = nnn
            return
        elif opcode & 0xF000 == 0xB000:
            # BNNN - JP V0, addr
            self.pc = (nnn + self.V[0]) & 0xFFF
            return
        elif opcode & 0xF000 == 0xC000:
            # CXKK - RND Vx, byte
            self.V[x] = self._rand_byte() & kk
            return
        elif opcode & 0xF000 == 0xD000:
            # DXYN - DRW Vx, Vy, nibble
            vx = self.V[x] % self.WIDTH
            vy = self.V[y] % self.HEIGHT
            height = n
            if height == 0:
                # Some SCHIP ROMs use 0 for 16; classic CHIP‑8 ignores.
                height = 16  # makes a few ROMs playable; harmless for classic ROMs
            self.V[0xF] = 0
            for row in range(height):
                sprite = self.memory[(self.I + row) & 0xFFF]
                for bit in range(8):
                    if (sprite & (0x80 >> bit)) != 0:
                        px = (vx + bit) % self.WIDTH
                        py = (vy + row) % self.HEIGHT
                        self._xor_pixel(px, py, 1)
            self.draw_flag = True
            return
        elif opcode & 0xF0FF == 0xE09E:
            # EX9E - SKP Vx
            if self.keypad[self.V[x] & 0xF]:
                self.pc += 2
            return
        elif opcode & 0xF0FF == 0xE0A1:
            # EXA1 - SKNP Vx
            if not self.keypad[self.V[x] & 0xF]:
                self.pc += 2
            return
        elif opcode & 0xF0FF == 0xF007:
            # FX07 - LD Vx, DT
            self.V[x] = self.delay_timer
            return
        elif opcode & 0xF0FF == 0xF00A:
            # FX0A - LD Vx, K (wait for key)
            # Stall by rewinding PC if no key yet
            pressed = next((k for k, v in enumerate(self.keypad) if v), None)
            if pressed is None:
                self.pc -= 2
            else:
                self.V[x] = pressed
            return
        elif opcode & 0xF0FF == 0xF015:
            # FX15 - LD DT, Vx
            self.delay_timer = self.V[x]
            return
        elif opcode & 0xF0FF == 0xF018:
            # FX18 - LD ST, Vx
            self.sound_timer = self.V[x]
            return
        elif opcode & 0xF0FF == 0xF01E:
            # FX1E - ADD I, Vx  (VF unaffected on classic CHIP‑8)
            self.I = (self.I + self.V[x]) & 0xFFF
            return
        elif opcode & 0xF0FF == 0xF029:
            # FX29 - LD F, Vx (I = location of sprite for digit Vx)
            digit = self.V[x] & 0xF
            self.I = self.FONT_ADDR + (digit * 5)
            return
        elif opcode & 0xF0FF == 0xF033:
            # FX33 - LD B, Vx (BCD)
            val = self.V[x]
            self.memory[self.I] = val // 100
            self.memory[self.I + 1] = (val // 10) % 10
            self.memory[self.I + 2] = val % 10
            return
        elif opcode & 0xF0FF == 0xF055:
            # FX55 - Store V0..Vx into memory starting at I
            for r in range(x + 1):
                self.memory[(self.I + r) & 0xFFF] = self.V[r]
            if not self.mem_quirk:
                self.I = (self.I + x + 1) & 0xFFF
            return
        elif opcode & 0xF0FF == 0xF065:
            # FX65 - Load V0..Vx from memory starting at I
            for r in range(x + 1):
                self.V[r] = self.memory[(self.I + r) & 0xFFF]
            if not self.mem_quirk:
                self.I = (self.I + x + 1) & 0xFFF
            return
        else:
            # Unknown opcode: ignore safely
            return


# -------------------------
# Tkinter Frontend
# -------------------------

KEYMAP = {
    # CHIP-8 key -> keyboard
    #  1 2 3 C     => 1 2 3 4
    #  4 5 6 D     => Q W E R
    #  7 8 9 E     => A S D F
    #  A 0 B F     => Z X C V
    '1': 0x1, '2': 0x2, '3': 0x3, '4': 0xC,
    'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xD,
    'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xE,
    'z': 0xA, 'x': 0x0, 'c': 0xB, 'v': 0xF
}

class Chip8App:
    def __init__(self, root, rom_path=None, scale=12, cpu_hz=700, shift_quirk=False, mem_quirk=False):
        self.root = root
        self.root.title(WINDOW_TITLE_BASE)
        self.scale = max(4, int(scale))
        self.cpu_hz = float(cpu_hz)
        self.cycles_accum = 0.0
        self.last_rom_path = None
        self.running = True
        self.frame_ms = int(1000 / 60)  # ~16ms
        self._beep_gate = 0

        self.chip = Chip8(shift_quirk=shift_quirk, mem_quirk=mem_quirk)

        # UI Layout
        self.canvas = Canvas(root,
                             width=Chip8.WIDTH * self.scale,
                             height=Chip8.HEIGHT * self.scale,
                             highlightthickness=0, bd=0, bg="black")
        self.canvas.pack(side=TOP, fill=BOTH, expand=False)

        controls = Frame(root)
        controls.pack(side=TOP, fill=X)
        self.status_var = StringVar(value="Ready.")
        self.status_label = Label(root, textvariable=self.status_var, anchor='w')
        self.status_label.pack(side=BOTTOM, fill=X)

        # Buttons
        self.btn_run = Button(controls, text="Pause", width=8, command=self.toggle_run)
        self.btn_reset = Button(controls, text="Reset", width=8, command=self.reset_soft)
        self.btn_step = Button(controls, text="Step", width=8, command=self.step_once)
        self.btn_open = Button(controls, text="Open ROM…", width=12, command=self.open_rom_dialog)

        self.btn_open.pack(side=LEFT, padx=4, pady=4)
        self.btn_run.pack(side=LEFT, padx=4, pady=4)
        self.btn_step.pack(side=LEFT, padx=4, pady=4)
        self.btn_reset.pack(side=LEFT, padx=4, pady=4)

        Label(controls, text="CPU Hz").pack(side=LEFT, padx=(16, 4))
        self.speed = Scale(controls, from_=60, to=1500, orient=HORIZONTAL, showvalue=True,
                           resolution=10, length=240, command=self._on_speed)
        self.speed.set(int(self.cpu_hz))
        self.speed.pack(side=LEFT, padx=4, pady=4)

        # Menubar
        self._make_menu()

        # Pixel grid cache for fast recolor
        self.pixel_ids = []
        self._init_pixels()

        # Key bindings
        self.root.bind("<KeyPress>", self._on_keydown)
        self.root.bind("<KeyRelease>", self._on_keyup)
        # Quick shortcuts
        self.root.bind("<space>", lambda e: self.toggle_run())
        self.root.bind(".", lambda e: self.step_once())
        self.root.bind("<Control-r>", lambda e: self.reload_rom())
        self.root.bind("<Control-o>", lambda e: self.open_rom_dialog())

        # Initial render
        self.render()

        # Load ROM from CLI if provided
        if rom_path and os.path.isfile(rom_path):
            self.load_rom_file(rom_path)

        # Start main loop at ~60Hz
        self._scheduled = False
        self._schedule_next()

    # ---------- UI Helpers ----------

    def _make_menu(self):
        m = Menu(self.root)
        mf = Menu(m, tearoff=0)
        mf.add_command(label="Open ROM…", accelerator="Ctrl+O", command=self.open_rom_dialog)
        mf.add_command(label="Reload ROM", accelerator="Ctrl+R", command=self.reload_rom)
        mf.add_separator()
        mf.add_command(label="Exit", command=self.root.destroy)
        m.add_cascade(label="File", menu=mf)

        me = Menu(m, tearoff=0)
        me.add_command(label="Pause/Resume", accelerator="Space", command=self.toggle_run)
        me.add_command(label="Step Instruction", accelerator=".", command=self.step_once)
        me.add_command(label="Soft Reset", command=self.reset_soft)
        me.add_command(label="Hard Reset", command=self.reset_hard)
        m.add_cascade(label="Emulation", menu=me)

        mh = Menu(m, tearoff=0)
        mh.add_command(label="Key Mapping…", command=self._show_keymap)
        mh.add_command(label="About…", command=self._show_about)
        m.add_cascade(label="Help", menu=mh)

        self.root.config(menu=m)

    def _init_pixels(self):
        self.canvas.delete("all")
        self.pixel_ids = []
        for y in range(Chip8.HEIGHT):
            row = []
            for x in range(Chip8.WIDTH):
                x0 = x * self.scale
                y0 = y * self.scale
                x1 = x0 + self.scale
                y1 = y0 + self.scale
                rid = self.canvas.create_rectangle(
                    x0, y0, x1, y1, outline="", fill="#000000"
                )
                row.append(rid)
            self.pixel_ids.append(row)

    def _on_speed(self, _val):
        self.cpu_hz = float(self.speed.get())

    def _set_status(self):
        rom = os.path.basename(self.last_rom_path) if self.last_rom_path else "—"
        self.status_var.set(
            f"ROM: {rom} | PC: {self.chip.pc:03X} | I: {self.chip.I:03X} "
            f"| V0:{self.chip.V[0]:02X} V1:{self.chip.V[1]:02X} VF:{self.chip.V[0xF]:02X} "
            f"| DT:{self.chip.delay_timer:02d} ST:{self.chip.sound_timer:02d} "
            f"| {int(self.cpu_hz)} Hz | {'RUN' if self.running else 'PAUSE'}"
        )

    def _schedule_next(self):
        if not self._scheduled:
            self._scheduled = True
            self.root.after(self.frame_ms, self._tick)

    def _tick(self):
        self._scheduled = False

        # Run enough cycles for this ~1/60s frame
        if self.running:
            cycles_per_frame = self.cpu_hz / 60.0
            self.cycles_accum += cycles_per_frame
            ncycles = int(self.cycles_accum)
            self.cycles_accum -= ncycles
            for _ in range(ncycles):
                self.chip.cycle()

        # Timers tick at 60 Hz regardless of CPU speed
        if self.chip.delay_timer > 0:
            self.chip.delay_timer -= 1
        if self.chip.sound_timer > 0:
            self.chip.sound_timer -= 1
            # Gate the bell to avoid an overwhelming buzz; ~12Hz
            self._beep_gate = (self._beep_gate + 1) % 5
            if self._beep_gate == 0:
                try:
                    # Cross-platform "system bell"
                    self.root.bell()
                except Exception:
                    pass

        if self.chip.draw_flag:
            self.render()
            self.chip.draw_flag = False

        self._set_status()
        self._schedule_next()

    # ---------- ROM / Emu control ----------

    def open_rom_dialog(self):
        path = filedialog.askopenfilename(
            title="Open CHIP‑8 ROM",
            filetypes=[("CHIP‑8 ROMs", "*.ch8 *.c8 *.rom *.*"), ("All files", "*.*")]
        )
        if path:
            self.load_rom_file(path)

    def load_rom_file(self, path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.chip.load_rom_bytes(data)
            self.last_rom_path = path
            self.root.title(f"{WINDOW_TITLE_BASE} — {os.path.basename(path)}")
            self.status_var.set(f"Loaded ROM: {os.path.basename(path)} ({len(data)} bytes)")
        except Exception as e:
            messagebox.showerror("Load ROM failed", str(e))

    def reload_rom(self):
        if self.last_rom_path and os.path.isfile(self.last_rom_path):
            self.load_rom_file(self.last_rom_path)
        else:
            messagebox.showinfo("Reload ROM", "No ROM loaded yet.")

    def reset_soft(self):
        self.chip.reset(hard=False)
        self.chip.draw_flag = True
        self.render()

    def reset_hard(self):
        self.chip.reset(hard=True)
        self.render()

    def toggle_run(self):
        self.running = not self.running
        self.btn_run.config(text="Pause" if self.running else "Run")

    def step_once(self):
        if self.running:
            self.toggle_run()
        self.chip.cycle()
        if self.chip.draw_flag:
            self.render()
            self.chip.draw_flag = False
        self._set_status()

    # ---------- Rendering ----------

    def render(self):
        on = "#FFFFFF"
        off = "#000000"
        idx = 0
        for y in range(Chip8.HEIGHT):
            row_ids = self.pixel_ids[y]
            for x in range(Chip8.WIDTH):
                color = on if self.chip.gfx[idx] else off
                self.canvas.itemconfig(row_ids[x], fill=color)
                idx += 1

    # ---------- Input ----------

    def _on_keydown(self, event):
        keysym = (event.keysym or "").lower()
        if keysym in KEYMAP:
            chip_key = KEYMAP[keysym]
            self.chip.keypad[chip_key] = 1

    def _on_keyup(self, event):
        keysym = (event.keysym or "").lower()
        if keysym in KEYMAP:
            chip_key = KEYMAP[keysym]
            self.chip.keypad[chip_key] = 0

    # ---------- Help ----------

    def _show_about(self):
        messagebox.showinfo(
            "About",
            f"{VERSION}\n"
            "Tkinter CHIP‑8 emulator for Windows & macOS\n\n"
            "Copyright (C) 2025 Samsoft Studios\n"
            "License: GPL‑3.0‑or‑later\n\n"
            "Nintendo is a trademark of Nintendo Co., Ltd. Not affiliated.\n"
        )

    def _show_keymap(self):
        messagebox.showinfo(
            "Key Mapping",
            "CHIP‑8 keypad → Keyboard:\n"
            " 1  2  3  C    →  1  2  3  4\n"
            " 4  5  6  D    →  Q  W  E  R\n"
            " 7  8  9  E    →  A  S  D  F\n"
            " A  0  B  F    →  Z  X  C  V\n\n"
            "Emulator controls:\n"
            "  Space  = Pause/Resume\n"
            "  .      = Step one instruction\n"
            "  Ctrl+O = Open ROM\n"
            "  Ctrl+R = Reload ROM\n"
        )


def main():
    parser = argparse.ArgumentParser(description="Cat's CHIP‑8 Emu — Tkinter")
    parser.add_argument("rom", nargs="?", help="Path to a CHIP‑8 ROM")
    parser.add_argument("--hz", type=float, default=700.0, help="CPU speed in Hz (default 700)")
    parser.add_argument("--scale", type=int, default=12, help="Pixel scale (default 12)")
    parser.add_argument("--shift-quirk", action="store_true",
                        help="Use original shift behavior (8XY6/8XYE use Vy as source)")
    parser.add_argument("--mem-quirk", action="store_true",
                        help="Use original FX55/FX65 behavior (I not incremented)")
    args = parser.parse_args()

    root = Tk()
    app = Chip8App(root,
                   rom_path=args.rom,
                   scale=args.scale,
                   cpu_hz=args.hz,
                   shift_quirk=args.shift_quirk,
                   mem_quirk=args.mem_quirk)
    root.resizable(False, False)
    root.mainloop()


if __name__ == "__main__":
    main()
