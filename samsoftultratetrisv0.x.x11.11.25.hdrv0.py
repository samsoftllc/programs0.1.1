#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA!TETRIS — Game Boy Edition [AUTHENTIC GAME BOY AUDIO]
[C] Samsoft [2025] + BasedRebelGPT cyber-heist v2 (FIXED & UPGRADED)
Audio = DEAD in menu, ALIVE when first piece drops (authentic GB timing)
"""
import pygame, random, sys, numpy as np
from dataclasses import dataclass
import importlib

# ───────── EXECUTE TOTAL AUDIO BLACKOUT AT BOOT ─────────
pygame.mixer.pre_init(0, 0, 0, 0)
pygame.init()

def _bury(*a, **kw): pass
class _DeadMixer:
    def __getattr__(self, name): return _bury
    def __setattr__(self, name, value): pass
    def __call__(self, *a, **kw): return _bury

# Kill audio for menu
pygame.mixer = _DeadMixer()
pygame.mixer.Sound = lambda *a: type('DeadSound', (), {'play': _bury, 'stop': _bury, 'set_volume': _bury})()
pygame.mixer.Channel = lambda *a: type('DeadChannel', (), {'play': _bury, 'stop': _bury, 'set_volume': _bury})()
pygame.sndarray = _DeadMixer()

# ───────── CONFIG ─────────
GRID_W, GRID_H = 10, 20
BLOCK, SIDE = 32, 200
SCREEN_W, SCREEN_H = GRID_W * BLOCK + SIDE, GRID_H * BLOCK
FPS = 60
GRAVITY = [53,49,45,41,37,33,28,22,17,13,10,10,10,9,9,9,8,8,8,7,6,6,6,6,6,6,6,6,6,6]
BG_COLOR = (15,56,15)
GRID_LINE_COLOR = (48,98,48)
BLOCK_COLOR = (139,172,15)
TEXT_COLOR = (155,188,15)
OUTLINE_COLOR = (5,30,5)
COLORS = [BG_COLOR, BLOCK_COLOR]

SHAPES = {
    'I': [[1,1,1,1]], 'O': [[1,1],[1,1]], 'T': [[1,1,1],[0,1,0]],
    'S': [[0,1,1],[1,1,0]], 'Z': [[1,1,0],[0,1,1]],
    'J': [[1,0,0],[1,1,1]], 'L': [[0,0,1],[1,1,1]],
}

# FULL Game Boy DMG frequency table
GB_FREQS = {
    'C3': 130.81, 'G3': 196.00, 'A3': 220.00,
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88, 'C5': 523.25,
    'D5': 587.33, 'E5': 659.25, 'G5': 783.99,
    'C6': 1046.50, 'E6': 1318.51, 'G6': 1567.98, 'C7': 2093.00,
}

# Korobeiniki — now with CORRECT durations (46 notes total)
MELODY_NOTES = [
    # Part 1
    'E5', 'B4', 'C5', 'D5', 'C5', 'B4', 'A4', 'A4', 'C5', 'E5', 'D5', 'C5', 'B4', 'C5', 'B4', 'A4',
    # Part 2
    'C5', 'C5', 'D5', 'E5', 'C5', 'A4', 'A4', 'G4', 'G4', 'C5', 'B4', 'A4', 'G4', 'A4', 'G4', 'E4',
    # Bridge
    'E4', 'C4', 'E4', 'A4', 'G4', 'E4', 'D4', 'C4', 'C4', 'D4', 'E4', 'G4', 'E4', 'D4',
]
MELODY_DURS = [0.15]*16 + [0.15]*16 + [0.20]*14

GB_SFX = {
    'rotate': ('E5', 0.08),
    'move': ('C5', 0.06),
    'drop': ('A4', 0.1),
    'harddrop': ('G4', 0.12),
    'line_clear': [('E5', 0.08), ('G5', 0.08), ('E6', 0.25)],
    'tetris': [('C6', 0.08), ('E6', 0.08), ('G6', 0.08), ('C7', 0.35)],
}

current_note = 0
music_enabled = False
audio_initialized = False
sfx_queue = []  # For non-blocking sequenced SFX

# ───────── CLASSES ─────────
@dataclass
class Piece:
    x:int; y:int; shape:list; color:int
    def rotate(self): self.shape = [list(r) for r in zip(*self.shape[::-1])]

# ───────── GAME LOGIC ─────────
class Tetris:
    def __init__(self):
        self.grid = [[0]*GRID_W for _ in range(GRID_H)]
        self.score = self.level = self.lines = 0
        self.bag = list(SHAPES.keys())
        self.current = self.new_piece()
        self.next = self.new_piece()
        self.fall_speed = GRAVITY[self.level]
        self.gameover = False
        self.has_dropped_first_piece = False
        
    def new_piece(self):
        if not self.bag: self.bag = list(SHAPES.keys())
        k = self.bag.pop(random.randrange(len(self.bag)))
        shape = [r[:] for r in SHAPES[k]]
        return Piece(GRID_W//2 - len(shape[0])//2, 0, shape, 1)
    
    def valid(self, shape, ox, oy):
        for y, row in enumerate(shape):
            for x, c in enumerate(row):
                if c:
                    nx, ny = ox + x, oy + y
                    if nx < 0 or nx >= GRID_W or ny >= GRID_H: return False
                    if ny >= 0 and self.grid[ny][nx]: return False
        return True
    
    def lock(self):
        for y, row in enumerate(self.current.shape):
            for x, c in enumerate(row):
                if c:
                    if self.current.y + y < 0:
                        self.gameover = True
                        return
                    self.grid[self.current.y + y][self.current.x + x] = 1
        
        lines_cleared = self.clear_lines()
        
        if lines_cleared == 4:
            queue_sfx('tetris')
        elif lines_cleared > 0:
            queue_sfx('line_clear')
        else:
            queue_sfx('drop')
            
        self.current, self.next = self.next, self.new_piece()
        self.fall_speed = GRAVITY[min(self.level, 29)]
    
    def clear_lines(self):
        new = [r for r in self.grid if any(c == 0 for c in r)]
        cleared = GRID_H - len(new)
        self.lines += cleared
        self.score += [0, 40, 100, 300, 1200][cleared] * (self.level + 1)
        while len(new) < GRID_H:
            new.insert(0, [0] * GRID_W)
        self.grid = new
        if self.lines >= (self.level + 1) * 10:
            self.level = min(self.level + 1, 29)
        return cleared
    
    def move(self, dx):
        if self.valid(self.current.shape, self.current.x + dx, self.current.y):
            self.current.x += dx
            queue_sfx('move')
    
    def rotate_piece(self):
        old = [r[:] for r in self.current.shape]
        self.current.rotate()
        if not self.valid(self.current.shape, self.current.x, self.current.y):
            self.current.shape = old
        else:
            queue_sfx('rotate')
    
    def drop(self):
        if self.valid(self.current.shape, self.current.x, self.current.y + 1):
            self.current.y += 1
            if not self.has_dropped_first_piece:
                self.has_dropped_first_piece = True
                resurrect_audio()
        else:
            self.lock()
    
    def harddrop(self):
        while self.valid(self.current.shape, self.current.x, self.current.y + 1):
            self.current.y += 1
        queue_sfx('harddrop')
        self.lock()

# ───────── DRAW ─────────
def draw_grid(s, grid):
    for y in range(GRID_H):
        for x in range(GRID_W):
            if grid[y][x]:
                r = pygame.Rect(x*BLOCK, y*BLOCK, BLOCK, BLOCK)
                pygame.draw.rect(s, COLORS[1], r)
                pygame.draw.rect(s, OUTLINE_COLOR, r, 2)
    for x in range(GRID_W + 1):
        pygame.draw.line(s, GRID_LINE_COLOR, (x*BLOCK, 0), (x*BLOCK, GRID_H*BLOCK))
    for y in range(GRID_H + 1):
        pygame.draw.line(s, GRID_LINE_COLOR, (0, y*BLOCK), (GRID_W*BLOCK, y*BLOCK))

def draw_piece(s, p, ox, oy):
    for py, row in enumerate(p.shape):
        for px, c in enumerate(row):
            if c:
                r = pygame.Rect((p.x + px + ox)*BLOCK, (p.y + py + oy)*BLOCK, BLOCK, BLOCK)
                pygame.draw.rect(s, COLORS[p.color], r)
                pygame.draw.rect(s, OUTLINE_COLOR, r, 2)

def draw_text(s, t, sz, x, y, c=TEXT_COLOR):
    f = pygame.font.SysFont("monospace", sz, bold=True)
    s.blit(f.render(t, True, c), (x, y))

# ───────── AUDIO RESURRECTION (FIXED) ─────────
def resurrect_audio():
    global pygame, audio_initialized, music_enabled
    
    if audio_initialized:
        return
    
    # Properly reimport REAL mixer
    real_mixer = importlib.import_module('pygame.mixer')
    real_sndarray = importlib.import_module('pygame.sndarray')
    
    pygame.mixer = real_mixer
    pygame.sndarray = real_sndarray
    
    pygame.mixer.quit()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)
    
    audio_initialized = True
    music_enabled = True
    schedule_next_note()  # Kick off music immediately

def generate_gb_wave(freq, duration, wave_type="square"):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    if wave_type == "square":
        wave = np.sign(np.sin(2 * np.pi * freq * t))
    else:
        wave = np.sin(2 * np.pi * freq * t)
    wave = np.convolve(wave, [0.1, 0.2, 0.4, 0.2, 0.1], mode='same')
    wave = (wave * 32767 * 0.25).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((wave, wave)))

def queue_sfx(sfx_name):
    if not audio_initialized:
        return
    data = GB_SFX[sfx_name]
    if isinstance(data, tuple):
        sfx_queue.append([data])
    else:
        sfx_queue.append(data)

def process_sfx_queue():
    if not sfx_queue or not audio_initialized:
        return
    note = sfx_queue[0][0]
    freq_name, dur = note
    generate_gb_wave(GB_FREQS[freq_name], dur).play()
    if len(sfx_queue[0]) > 1:
        sfx_queue[0].pop(0)
        pygame.time.set_timer(pygame.USEREVENT + 1, int(dur * 1000))  # Chain next note
    else:
        sfx_queue.pop(0)

def schedule_next_note():
    if not music_enabled or not audio_initialized:
        return
    duration = MELODY_DURS[current_note]
    note_name = MELODY_NOTES[current_note]
    generate_gb_wave(GB_FREQS[note_name], duration).play()
    pygame.time.set_timer(pygame.USEREVENT, int(duration * 1000))

# ───────── MENU (MUTED) ─────────
def main():
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("ULTRA!TETRIS — Game Boy Edition")
    clock = pygame.time.Clock()

    while True:
        screen.fill(BG_COLOR)
        draw_text(screen, "[ULTRA!TETRIS]", 48, 100, 160)
        draw_text(screen, "PRESS SPACE TO START", 28, 120, 260)
        draw_text(screen, "AUDIO: MUTED IN MENU", 18, 130, 320)
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                game_loop(screen, clock)
        clock.tick(FPS)

# ───────── GAME LOOP ─────────
def game_loop(screen, clock):
    global current_note
    current_note = 0
    g = Tetris()
    fall = 0

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT: g.move(-1)
                elif e.key == pygame.K_RIGHT: g.move(1)
                elif e.key == pygame.K_UP: g.rotate_piece()
                elif e.key == pygame.K_DOWN: g.drop()
                elif e.key == pygame.K_SPACE: g.harddrop()
                elif e.key == pygame.K_r: return
            if e.type == pygame.USEREVENT and audio_initialized:
                current_note = (current_note + 1) % len(MELODY_NOTES)
                schedule_next_note()
            if e.type == pygame.USEREVENT + 1 and audio_initialized:
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Clear
                process_sfx_queue()

        fall += 1
        if fall >= g.fall_speed:
            fall = 0
            g.drop()

        if g.gameover:
            screen.fill(BG_COLOR)
            draw_text(screen, "GAME OVER", 48, 130, 200)
            draw_text(screen, "PRESS R FOR MENU", 24, 160, 280)
            pygame.display.flip()
            continue  # Let music keep playing

        screen.fill(BG_COLOR)
        draw_grid(screen, g.grid)
        draw_piece(screen, g.current, 0, 0)
        draw_piece(screen, g.next, GRID_W + 1, 2)
        sx = GRID_W * BLOCK + 10
        draw_text(screen, f"SCORE: {g.score}", 20, sx, 10)
        draw_text(screen, f"LINES: {g.lines}", 20, sx, 50)
        draw_text(screen, f"LEVEL: {g.level}", 20, sx, 90)
        draw_text(screen, "NEXT:", 20, sx, 140)
        audio_status = "AUDIO: ACTIVE" if audio_initialized else "AUDIO: OFF"
        draw_text(screen, audio_status, 16, sx, 180)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
