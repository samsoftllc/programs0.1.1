# chip8.py — single-file educational CHIP‑8 interpreter (pygame)
# MIT License. No external assets. ~60 Hz timers, 64x32 display, 16-key hex keypad.
# Run: python chip8.py path/to/rom.ch8
import sys, time, random, pygame
from pathlib import Path

# ── CHIP‑8 core ────────────────────────────────────────────────────────────────────
class Chip8:
    def __init__(self):
        self.mem = bytearray(4096)
        self.V = [0]*16              # V0..VF
        self.I = 0                   # index
        self.pc = 0x200              # program counter (ROM start)
        self.sp = 0                  # stack pointer
        self.stack = [0]*16
        self.delay = 0               # delay timer (60 Hz)
        self.sound = 0               # sound timer (60 Hz)
        self.keys = [0]*16           # keypad state
        self.draw_flag = False
        self.w, self.h = 64, 32
        self.gfx = [[0]*self.w for _ in range(self.h)]
        # COSMAC VIP font (each 5 bytes)
        font = [
            0xF0,0x90,0x90,0x90,0xF0, 0x20,0x60,0x20,0x20,0x70,
            0xF0,0x10,0xF0,0x80,0xF0, 0xF0,0x10,0xF0,0x10,0xF0,
            0x90,0x90,0xF0,0x10,0x10, 0xF0,0x80,0xF0,0x10,0xF0,
            0xF0,0x80,0xF0,0x90,0xF0, 0xF0,0x10,0x20,0x40,0x40,
            0xF0,0x90,0xF0,0x90,0xF0, 0xF0,0x90,0xF0,0x10,0xF0,
            0xF0,0x90,0xF0,0x90,0x90, 0xE0,0x90,0xE0,0x90,0xE0,
            0xF0,0x80,0x80,0x80,0xF0, 0xE0,0x90,0x90,0x90,0xE0,
            0xF0,0x80,0xF0,0x80,0xF0, 0xF0,0x80,0xF0,0x80,0x80
        ]
        self.mem[0x50:0x50+len(font)] = bytes(font)

    def load(self, rom_bytes: bytes):
        self.mem[0x200:0x200+len(rom_bytes)] = rom_bytes

    def clear(self):
        for y in range(self.h):
            for x in range(self.w):
                self.gfx[y][x] = 0
        self.draw_flag = True

    def fetch(self):
        op = (self.mem[self.pc] << 8) | self.mem[self.pc+1]
        self.pc += 2
        return op

    def step(self):
        op = self.fetch()
        nnn, kk = op & 0x0FFF, op & 0x00FF
        n, x, y = op & 0x000F, (op>>8)&0xF, (op>>4)&0xF
        top = op & 0xF000

        if op == 0x00E0: self.clear()
        elif op == 0x00EE: self.sp-=1; self.pc = self.stack[self.sp]
        elif top == 0x0000: pass  # 0NNN ignored
        elif top == 0x1000: self.pc = nnn
        elif top == 0x2000: self.stack[self.sp]=self.pc; self.sp+=1; self.pc=nnn
        elif top == 0x3000: 
            if self.V[x]==kk: self.pc+=2
        elif top == 0x4000: 
            if self.V[x]!=kk: self.pc+=2
        elif top == 0x5000 and n==0x0:
            if self.V[x]==self.V[y]: self.pc+=2
        elif top == 0x6000: self.V[x]=kk
        elif top == 0x7000: self.V[x]=(self.V[x]+kk)&0xFF
        elif top == 0x8000:
            if   n==0x0: self.V[x]=self.V[y]
            elif n==0x1: self.V[x]|=self.V[y]
            elif n==0x2: self.V[x]&=self.V[y]
            elif n==0x3: self.V[x]^=self.V[y]
            elif n==0x4:
                s=self.V[x]+self.V[y]; self.V[0xF]=1 if s>0xFF else 0; self.V[x]=s&0xFF
            elif n==0x5:
                self.V[0xF]=1 if self.V[x]>self.V[y] else 0; self.V[x]=(self.V[x]-self.V[y])&0xFF
            elif n==0x6:
                self.V[0xF]=self.V[x]&1; self.V[x]=(self.V[x]>>1)&0xFF
            elif n==0x7:
                self.V[0xF]=1 if self.V[y]>self.V[x] else 0; self.V[x]=(self.V[y]-self.V[x])&0xFF
            elif n==0xE:
                self.V[0xF]=(self.V[x]>>7)&1; self.V[x]=(self.V[x]<<1)&0xFF
        elif top == 0x9000 and n==0x0:
            if self.V[x]!=self.V[y]: self.pc+=2
        elif top == 0xA000: self.I = nnn
        elif top == 0xB000: self.pc = nnn + self.V[0]
        elif top == 0xC000: self.V[x] = random.randint(0,255) & kk
        elif top == 0xD000:
            vx, vy, height = self.V[x]%64, self.V[y]%32, n
            self.V[0xF]=0
            for row in range(height):
                sprite = self.mem[self.I+row]
                py = (vy+row)%32
                for col in range(8):
                    if sprite & (0x80>>col):
                        px = (vx+col)%64
                        if self.gfx[py][px]==1: self.V[0xF]=1
                        self.gfx[py][px]^=1
            self.draw_flag=True
        elif top == 0xE000:
            if kk==0x9E and self.keys[self.V[x]&0xF]: self.pc+=2
            if kk==0xA1 and not self.keys[self.V[x]&0xF]: self.pc+=2
        elif top == 0xF000:
            if   kk==0x07: self.V[x]=self.delay
            elif kk==0x0A:
                # wait for key
                for i,k in enumerate(self.keys):
                    if k: self.V[x]=i; break
                else:
                    self.pc-=2  # repeat this op until keypress
            elif kk==0x15: self.delay=self.V[x]
            elif kk==0x18: self.sound=self.V[x]
            elif kk==0x1E: self.I=(self.I+self.V[x])&0xFFF
            elif kk==0x29: self.I=0x50 + (self.V[x]&0xF)*5
            elif kk==0x33:
                v=self.V[x]; self.mem[self.I]=v//100; self.mem[self.I+1]=(v//10)%10; self.mem[self.I+2]=v%10
            elif kk==0x55:
                for i in range(x+1): self.mem[self.I+i]=self.V[i]
            elif kk==0x65:
                for i in range(x+1): self.V[i]=self.mem[self.I+i]
            else: pass
        else:
            pass

# ── Pygame front-end ───────────────────────────────────────────────────────────────
KEYMAP = {
    pygame.K_x:0x0, pygame.K_1:0x1, pygame.K_2:0x2, pygame.K_3:0x3,
    pygame.K_q:0x4, pygame.K_w:0x5, pygame.K_e:0x6, pygame.K_a:0x7,
    pygame.K_s:0x8, pygame.K_d:0x9, pygame.K_z:0xA, pygame.K_c:0xB,
    pygame.K_4:0xC, pygame.K_r:0xD, pygame.K_f:0xE, pygame.K_v:0xF
}

def main():
    if len(sys.argv)<2:
        print("Usage: python chip8.py path/to/rom.ch8"); sys.exit(1)
    rom = Path(sys.argv[1]).read_bytes()

    chip = Chip8(); chip.load(rom)
    pygame.init()
    scale = 16  # 64*16 x 32*16 → desktop-friendly
    screen = pygame.display.set_mode((64*scale, 32*scale))
    pygame.display.set_caption("CHIP‑8 (pygame) — ↑/↓ to change speed, R to reset")
    clock = pygame.time.Clock()

    cycles_per_frame = 10  # rough; interpreter is simple, so keep small & stable
    last_timer_tick = time.perf_counter()

    running=True
    while running:
        # input
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: running=False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in KEYMAP: chip.keys[KEYMAP[ev.key]]=1
                elif ev.key == pygame.K_ESCAPE: running=False
                elif ev.key == pygame.K_r:      chip.__init__(); chip.load(rom)
                elif ev.key == pygame.K_UP:     cycles_per_frame=min(40, cycles_per_frame+1)
                elif ev.key == pygame.K_DOWN:   cycles_per_frame=max(1,  cycles_per_frame-1)
            elif ev.type == pygame.KEYUP:
                if ev.key in KEYMAP: chip.keys[KEYMAP[ev.key]]=0

        # execute a small, steady batch of ops per frame
        for _ in range(cycles_per_frame):
            chip.step()

        # 60 Hz timers
        now = time.perf_counter()
        while now - last_timer_tick >= 1/60:
            last_timer_tick += 1/60
            if chip.delay>0: chip.delay-=1
            if chip.sound>0: chip.sound-=1

        # draw
        if chip.draw_flag:
            chip.draw_flag=False
            for y in range(chip.h):
                for x in range(chip.w):
                    c = 255 if chip.gfx[y][x] else 0
                    pygame.draw.rect(screen, (c,c,c), (x*scale, y*scale, scale, scale))
            pygame.display.flip()

        # simple “beep” via title (no audio lib)
        if chip.sound>0:
            pygame.display.set_caption("CHIP‑8 (BEEP!)")
        else:
            pygame.display.set_caption("CHIP‑8 (pygame) — ↑/↓ speed, R reset")

        clock.tick(60)  # aim for ~60 FPS

    pygame.quit()

if __name__=="__main__":
    main()
