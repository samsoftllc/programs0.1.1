import sys
import struct
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class CatCPU:
    def __init__(self):
        # 32 general-purpose registers (GPRs), 64-bit ints
        self.gpr = [0] * 32
        self.gpr[0] = 0  # $zero always 0
        # Program Counter
        self.pc = 0xBFC00000  # PIF bootstrap start
        # COP0 registers (Status, Cause, EPC, etc.)
        self.cop0 = [0] * 32
        self.cop0[12] = 0xEF000000  # Status: Enable COP0/1
        # HI/LO for mul/div
        self.hi = 0
        self.lo = 0
        # FPU (COP1) stubs
        self.fpr = [0.0] * 32
        # Delay slot and exceptions
        self.in_delay_slot = False
        self.exception = None  # 'TLB', 'INT', etc.

    def execute(self, instr: int, memory) -> int:
        if self.gpr[0] != 0:
            self.gpr[0] = 0  # Enforce $zero
        # Decode
        opcode = (instr >> 26) & 0x3F
        rs = (instr >> 21) & 0x1F
        rt = (instr >> 16) & 0x1F
        rd = (instr >> 11) & 0x1F
        shamt = (instr >> 6) & 0x1F
        funct = instr & 0x3F
        imm = instr & 0xFFFF
        target = instr & 0x3FFFFFF
        logging.debug(f"PC: 0x{self.pc:08X}, Instr: 0x{instr:08X}, Opcode: 0x{opcode:02X}")

        next_pc = self.pc + 4
        if opcode == 0x00:  # R-type
            if funct == 0x20:  # ADD
                self.gpr[rd] = self.gpr[rs] + self.gpr[rt]
            elif funct == 0x21:  # ADDU
                self.gpr[rd] = (self.gpr[rs] + self.gpr[rt]) & 0xFFFFFFFFFFFFFFFF
            elif funct == 0x24:  # AND
                self.gpr[rd] = self.gpr[rs] & self.gpr[rt]
            elif funct == 0x1A:  # DIV
                if self.gpr[rt] != 0:
                    self.lo = self.gpr[rs] // self.gpr[rt]
                    self.hi = self.gpr[rs] % self.gpr[rt]
            elif funct == 0x1B:  # DIVU
                if self.gpr[rt] != 0:
                    self.lo = (self.gpr[rs] & 0xFFFFFFFF) // (self.gpr[rt] & 0xFFFFFFFF)
                    self.hi = (self.gpr[rs] & 0xFFFFFFFF) % (self.gpr[rt] & 0xFFFFFFFF)
            elif funct == 0x08:  # JR
                next_pc = self.gpr[rs]
                self.in_delay_slot = True
            elif funct == 0x09:  # JALR
                self.gpr[31] = self.pc + 8
                next_pc = self.gpr[rs]
                self.in_delay_slot = True
            elif funct == 0x18:  # MULT
                result = self.gpr[rs] * self.gpr[rt]
                self.lo = result & 0xFFFFFFFFFFFFFFFF
                self.hi = (result >> 64) & 0xFFFFFFFFFFFFFFFF
            elif funct == 0x19:  # MULTU
                u_rs, u_rt = self.gpr[rs] & 0xFFFFFFFFFFFFFFFF, self.gpr[rt] & 0xFFFFFFFFFFFFFFFF
                result = u_rs * u_rt
                self.lo = result & 0xFFFFFFFFFFFFFFFF
                self.hi = (result >> 64) & 0xFFFFFFFFFFFFFFFF
            elif funct == 0x25:  # OR
                self.gpr[rd] = self.gpr[rs] | self.gpr[rt]
            elif funct == 0x00:  # SLL
                self.gpr[rd] = self.gpr[rt] << shamt
            elif funct == 0x02:  # SRL
                self.gpr[rd] = self.gpr[rt] >> shamt
            elif funct == 0x03:  # SRA
                self.gpr[rd] = (self.gpr[rt] >> shamt) if self.gpr[rt] >= 0 else ~((~self.gpr[rt]) << (64 - shamt)) >> (64 - 64)
            elif funct == 0x2A:  # SLT
                self.gpr[rd] = 1 if self.gpr[rs] < self.gpr[rt] else 0
            elif funct == 0x22:  # SUB
                self.gpr[rd] = self.gpr[rs] - self.gpr[rt]
            elif funct == 0x23:  # SUBU
                self.gpr[rd] = (self.gpr[rs] - self.gpr[rt]) & 0xFFFFFFFFFFFFFFFF
            elif funct == 0x26:  # XOR
                self.gpr[rd] = self.gpr[rs] ^ self.gpr[rt]
            else:
                raise ValueError(f"Unknown R-type funct: 0x{funct:02X}")
        elif opcode == 0x08:  # ADDI
            imm_s = imm if imm < 0x8000 else imm - 0x10000
            self.gpr[rt] = self.gpr[rs] + imm_s
        elif opcode == 0x09:  # ADDIU
            imm_s = imm if imm < 0x8000 else imm - 0x10000
            self.gpr[rt] = (self.gpr[rs] + imm_s) & 0xFFFFFFFFFFFFFFFF
        elif opcode == 0x0C:  # ANDI
            self.gpr[rt] = self.gpr[rs] & imm
        elif opcode == 0x04:  # BEQ
            if self.gpr[rs] == self.gpr[rt]:
                imm_s = imm if imm < 0x8000 else imm - 0x10000
                next_pc = self.pc + 4 + (imm_s << 2)
                self.in_delay_slot = True
        elif opcode == 0x05:  # BNE
            if self.gpr[rs] != self.gpr[rt]:
                imm_s = imm if imm < 0x8000 else imm - 0x10000
                next_pc = self.pc + 4 + (imm_s << 2)
                self.in_delay_slot = True
        elif opcode == 0x02:  # J
            next_pc = (self.pc & 0xF0000000) | (target << 2)
            self.in_delay_slot = True
        elif opcode == 0x03:  # JAL
            self.gpr[31] = self.pc + 8
            next_pc = (self.pc & 0xF0000000) | (target << 2)
            self.in_delay_slot = True
        elif opcode == 0x0F:  # LUI
            self.gpr[rt] = imm << 16
        elif opcode == 0x20:  # LB
            addr = self.gpr[rs] + (imm if imm < 0x8000 else imm - 0x10000)
            self.gpr[rt] = memory.read8(addr) if addr % 4 == 0 else memory.read8(addr)  # Sign extend
            if self.gpr[rt] & 0x80:
                self.gpr[rt] |= 0xFFFFFFFFFFFFFF00
        elif opcode == 0x21:  # LH
            addr = self.gpr[rs] + (imm if imm < 0x8000 else imm - 0x10000)
            val = memory.read16(addr)
            self.gpr[rt] = val if val < 0x8000 else val - 0x10000
        elif opcode == 0x23:  # LW
            addr = self.gpr[rs] + (imm if imm < 0x8000 else imm - 0x10000)
            self.gpr[rt] = memory.read32(addr)
        elif opcode == 0x0D:  # ORI
            self.gpr[rt] = self.gpr[rs] | imm
        elif opcode == 0x0A:  # SLTI
            imm_s = imm if imm < 0x8000 else imm - 0x10000
            self.gpr[rt] = 1 if self.gpr[rs] < imm_s else 0
        elif opcode == 0x0B:  # SLTIU
            self.gpr[rt] = 1 if (self.gpr[rs] & 0xFFFFFFFFFFFFFFFF) < imm else 0
        elif opcode == 0x28:  # SB
            addr = self.gpr[rs] + (imm if imm < 0x8000 else imm - 0x10000)
            memory.write8(addr, self.gpr[rt] & 0xFF)
        elif opcode == 0x29:  # SH
            addr = self.gpr[rs] + (imm if imm < 0x8000 else imm - 0x10000)
            memory.write16(addr, self.gpr[rt] & 0xFFFF)
        elif opcode == 0x2B:  # SW
            addr = self.gpr[rs] + (imm if imm < 0x8000 else imm - 0x10000)
            memory.write32(addr, self.gpr[rt])
        elif opcode == 0x0E:  # XORI
            self.gpr[rt] = self.gpr[rs] ^ imm
        elif opcode == 0x10:  # COP0
            if (instr >> 25) & 0x1:  # MTC0
                self.cop0[rd] = self.gpr[rt]
                if rd == 12:  # Status
                    logging.debug("COP0 Status updated")
            elif (instr >> 25) & 0x0:  # MFC0
                self.gpr[rt] = self.cop0[rd]
            else:
                raise ValueError(f"Unknown COP0: 0x{instr:08X}")
        else:
            raise ValueError(f"Unknown opcode: 0x{opcode:02X}")

        if self.in_delay_slot:
            # Execute delay slot
            delay_instr = memory.read32(self.pc + 4)
            self.execute(delay_instr, memory)
            self.in_delay_slot = False
            next_pc = self.pc + 8 if not self.in_delay_slot else next_pc  # Adjust if branched

        return next_pc

class CatMemory:
    def __init__(self, rom: bytes, pif_rom: Optional[bytes] = None):
        self.rdram = bytearray(4 * 1024 * 1024)  # 4MB RDRAM
        self.rom = rom
        self.pif_rom = pif_rom or b''  # PIF at 0x1FC00000
        # Basic mappings (Kseg0/1, PIF, etc.)
        self.imem = bytearray(0x1000)  # IMEM stub
        self.dmem = bytearray(0x1000)  # DMEM stub

    def read8(self, addr: int) -> int:
        if 0x10000000 <= addr < 0x10000000 + len(self.rom):
            return self.rom[addr - 0x10000000]
        elif 0x1FC00000 <= addr < 0x1FC00000 + len(self.pif_rom):
            return self.pif_rom[addr - 0x1FC00000]
        elif 0x00000000 <= addr < len(self.rdram):
            return self.rdram[addr]
        else:
            raise ValueError(f"Invalid read8 addr: 0x{addr:08X}")

    def read16(self, addr: int) -> int:
        if addr % 2 != 0:
            raise ValueError("Unaligned read16")
        val = self.read8(addr) << 8 | self.read8(addr + 1)
        return struct.unpack('>H', struct.pack('>H', val))[0]

    def read32(self, addr: int) -> int:
        if addr % 4 != 0:
            raise ValueError("Unaligned read32")
        if 0x10000000 <= addr < 0x10000000 + len(self.rom):
            offset = addr - 0x10000000
            return struct.unpack('>I', self.rom[offset:offset+4])[0]
        elif 0x1FC00000 <= addr < 0x1FC00000 + len(self.pif_rom):
            offset = addr - 0x1FC00000
            return struct.unpack('>I', self.pif_rom[offset:offset+4])[0]
        elif 0x00000000 <= addr < len(self.rdram):
            return struct.unpack('>I', self.rdram[addr:addr+4])[0]
        else:
            raise ValueError(f"Invalid read32 addr: 0x{addr:08X}")

    def write8(self, addr: int, value: int):
        if 0x00000000 <= addr < len(self.rdram):
            self.rdram[addr] = value & 0xFF
        else:
            raise ValueError(f"Invalid write8 addr: 0x{addr:08X}")

    def write16(self, addr: int, value: int):
        if addr % 2 != 0:
            raise ValueError("Unaligned write16")
        self.write8(addr, (value >> 8) & 0xFF)
        self.write8(addr + 1, value & 0xFF)

    def write32(self, addr: int, value: int):
        if addr % 4 != 0:
            raise ValueError("Unaligned write32")
        if 0x00000000 <= addr < len(self.rdram):
            self.rdram[addr:addr+4] = struct.pack('>I', value & 0xFFFFFFFF)
        else:
            raise ValueError(f"Invalid write32 addr: 0x{addr:08X}")

class CatsPJ64Emulator:
    def __init__(self, rom_path: str):
        with open(rom_path, 'rb') as f:
            rom = f.read()
        # PIF ROM (stub; in real, load from cart or default)
        pif_path = rom_path.replace('.z64', '_pif.z64')  # Assume separate PIF file
        pif_rom = b''  # Default empty; load if exists
        try:
            with open(pif_path, 'rb') as pf:
                pif_rom = pf.read()
        except FileNotFoundError:
            logging.warning("PIF ROM not found; using stub")
        if rom[:4] != b'\x80\x37\x12\x40':
            raise ValueError("ROM must be big-endian (.Z64)")
        self.memory = CatMemory(rom, pif_rom)
        self.cpu = CatCPU()
        # Init PIF bootstrap
        self.bootstrap_pif()

    def bootstrap_pif(self):
        # Simplified PIF init: Set SP, GP, etc. from PIF code
        self.cpu.gpr[29] = 0xFFFFFFFFA4001FF0  # SP
        self.cpu.gpr[30] = 0xFFFFFFFFA4000040  # S8 (PIF RAM)
        logging.info("PIF bootstrap initialized")

    def run(self, max_cycles: int = 1000000):
        cycles = 0
        while cycles < max_cycles:
            try:
                instr = self.memory.read32(self.cpu.pc)
                next_pc = self.cpu.execute(instr, self.memory)
                self.cpu.pc = next_pc
                cycles += 1
                if cycles % 10000 == 0:
                    logging.info(f"Cycle {cycles}, PC: 0x{self.cpu.pc:08X}")
            except Exception as e:
                logging.error(f"Error at PC 0x{self.cpu.pc:08X}: {e}")
                break
        logging.info("Emulation stopped.")

class CatsPJ64GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cat's PJ64 0.1 - [c] Catsan and Samsoft 1999 [Nintendo] [C] 2025 - Cat")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Custom cat-themed colors
        self.bg_color = "#2B2B2B"  # Dark gray
        self.menu_bg = "#404040"   # Medium gray
        self.accent_color = "#FF6B00"  # Orange accent
        self.text_color = "#FFFFFF"   # White text
        
        self.root.configure(bg=self.bg_color)
        
        # Emulator state
        self.emulator = None
        self.running = False
        
        self.create_menu()
        self.create_toolbar()
        self.create_status_bar()
        self.create_display_area()
        
    def create_menu(self):
        menubar = tk.Menu(self.root, bg=self.menu_bg, fg=self.text_color)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.menu_bg, fg=self.text_color)
        file_menu.add_command(label="Open ROM", command=self.open_rom, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="File", menu=file_menu)
        
        # System menu
        system_menu = tk.Menu(menubar, tearoff=0, bg=self.menu_bg, fg=self.text_color)
        system_menu.add_command(label="Reset", command=self.reset_emulator)
        system_menu.add_command(label="Pause", command=self.pause_emulator)
        system_menu.add_command(label="Stop", command=self.stop_emulator)
        menubar.add_cascade(label="System", menu=system_menu)
        
        # Options menu
        options_menu = tk.Menu(menubar, tearoff=0, bg=self.menu_bg, fg=self.text_color)
        options_menu.add_command(label="Settings", command=self.show_settings)
        menubar.add_cascade(label="Options", menu=options_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.menu_bg, fg=self.text_color)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        
    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg=self.bg_color, relief=tk.RAISED, bd=1)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Toolbar buttons with cat theme
        buttons = [
            ("🐱 Open", self.open_rom),
            ("▶️ Play", self.start_emulator),
            ("⏸️ Pause", self.pause_emulator),
            ("⏹️ Stop", self.stop_emulator),
            ("🔁 Reset", self.reset_emulator)
        ]
        
        for text, command in buttons:
            btn = tk.Button(toolbar, text=text, command=command, 
                          bg=self.menu_bg, fg=self.text_color,
                          activebackground=self.accent_color,
                          relief=tk.RAISED, bd=1, font=("Arial", 9))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            
    def create_display_area(self):
        # Main display frame
        display_frame = tk.Frame(self.root, bg="black", width=640, height=480)
        display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Placeholder for video output
        self.canvas = tk.Canvas(display_frame, bg="black", width=640, height=480)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Display placeholder with cat theme
        self.canvas.create_text(320, 200, text="🐱 Cat's PJ64 0.1", 
                               fill=self.accent_color, font=("Arial", 20, "bold"))
        self.canvas.create_text(320, 240, text="No ROM Loaded", 
                               fill="white", font=("Arial", 14))
        
    def create_status_bar(self):
        status_frame = tk.Frame(self.root, bg=self.bg_color, relief=tk.SUNKEN, bd=1)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="🐱 Ready - Cat's PJ64 0.1", 
                                   bg=self.bg_color, fg=self.text_color, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Copyright info in status bar
        copyright_label = tk.Label(status_frame, 
                                 text="[c] Catsan and Samsoft 1999 [Nintendo] [C] 2025 - Cat",
                                 bg=self.bg_color, fg=self.text_color, anchor=tk.E)
        copyright_label.pack(side=tk.RIGHT, padx=5)
        
    def open_rom(self):
        filename = filedialog.askopenfilename(
            title="Open N64 ROM - Cat's PJ64",
            filetypes=[("N64 ROMs", "*.z64 *.n64 *.v64"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.emulator = CatsPJ64Emulator(filename)
                self.status_label.config(text=f"🐱 Loaded: {filename.split('/')[-1]}")
                self.canvas.delete("all")
                self.canvas.create_text(320, 200, text="🐱 Cat's PJ64 0.1", 
                                       fill=self.accent_color, font=("Arial", 20, "bold"))
                self.canvas.create_text(320, 240, text="ROM Ready - Press Play", 
                                       fill="white", font=("Arial", 14))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load ROM: {str(e)}")
                
    def start_emulator(self):
        if self.emulator and not self.running:
            self.running = True
            self.status_label.config(text="🐱 Running - Emulation Active")
            self.canvas.delete("all")
            self.canvas.create_text(320, 200, text="🐱 Cat's PJ64 0.1", 
                                   fill=self.accent_color, font=("Arial", 20, "bold"))
            self.canvas.create_text(320, 240, text="Emulation Running", 
                                   fill="white", font=("Arial", 14))
            # In real implementation, this would start emulation thread
            
    def pause_emulator(self):
        if self.running:
            self.running = False
            self.status_label.config(text="🐱 Paused")
            
    def stop_emulator(self):
        self.running = False
        if self.emulator:
            self.status_label.config(text="🐱 Stopped")
            self.canvas.delete("all")
            self.canvas.create_text(320, 200, text="🐱 Cat's PJ64 0.1", 
                                   fill=self.accent_color, font=("Arial", 20, "bold"))
            self.canvas.create_text(320, 240, text="No ROM Loaded", 
                                   fill="white", font=("Arial", 16))
            
    def reset_emulator(self):
        if self.emulator:
            # Reset emulator state
            self.emulator.cpu = CatCPU()
            self.emulator.bootstrap_pif()
            self.status_label.config(text="🐱 Reset")
            
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Cat's PJ64 Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.bg_color)
        
        # Cat-themed settings interface
        title_label = tk.Label(settings_window, text="🐱 Cat's PJ64 0.1 Settings", 
                bg=self.bg_color, fg=self.accent_color, font=("Arial", 12, "bold"))
        title_label.pack(pady=10)
        
        # Files = Off setting
        files_var = tk.BooleanVar(value=True)
        files_check = tk.Checkbutton(settings_window, text="Files = Off", 
                      variable=files_var, bg=self.bg_color, fg=self.text_color,
                      selectcolor=self.menu_bg)
        files_check.pack(pady=5)
        
        # Cat mode setting
        cat_mode_var = tk.BooleanVar(value=True)
        cat_mode_check = tk.Checkbutton(settings_window, text="🐱 Cat Mode Enabled", 
                      variable=cat_mode_var, bg=self.bg_color, fg=self.text_color,
                      selectcolor=self.menu_bg)
        cat_mode_check.pack(pady=5)
        
        apply_btn = tk.Button(settings_window, text="Apply", 
                 command=settings_window.destroy,
                 bg=self.menu_bg, fg=self.text_color)
        apply_btn.pack(pady=10)
        
    def show_about(self):
        about_text = """🐱 Cat's PJ64 0.1

The Purr-fect N64 Emulator
Built with feline precision and care

[c] Catsan and Samsoft 1999 [Nintendo] [C] 2025 - Cat

Special Thanks:
- The Cat Community
- SamSoft Networking
- Nintendo for creating amazing games
- All the cats who inspired this project

"Purring since 1999" 🐾"""
        
        messagebox.showinfo("About Cat's PJ64", about_text)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].endswith('.py'):
        # Command line ROM loading
        emu = CatsPJ64Emulator(sys.argv[1])
        emu.run()
    else:
        # GUI mode
        gui = CatsPJ64GUI()
        gui.run()