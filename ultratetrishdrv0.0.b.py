#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TETRIS — NES Edition
[C] Samsoft [2025]  •  [C] The Tetris Company (Acknowledgment only, no assets)
A faithful, copyright-free recreation with all 30 levels (0–29) including the killscreen.
Procedural chiptune generator replaces external audio.
"""

import pygame, random, math, sys, numpy as np
from dataclasses import dataclass

# ───────── CONFIG ─────────
GRID_W, GRID_H = 10, 20
BLOCK = 32
SIDE = 200
SCREEN_W, SCREEN_H = GRID_W * BLOCK + SIDE, GRID_H * BLOCK
FPS = 60

# NES gravity speeds (frames per row drop)
GRAVITY = [48,43,38,33,28,23,18,13,8,6,5,5,5,4,4,4,3,3,3,2,2,2,2,2,2,2,2,2,1,1]

SHAPES = {
    'I': [[1,1,1,1]],
    'O': [[1,1],[1,1]],
    'T': [[1,1,1],[0,1,0]],
    'S': [[0,1,1],[1,1,0]],
    'Z': [[1,1,0],[0,1,1]],
    'J': [[1,0,0],[1,1,1]],
    'L': [[0,0,1],[1,1,1]]
}
COLORS = [
    (0,0,0),(0,255,255),(255,255,0),(128,0,128),
    (0,255,0),(255,0,0),(0,0,255),(255,165,0)
]

# ───────── CLASSES ─────────
@dataclass
class Piece:
    x: int; y: int; shape: list; color: int
    def rotate(self):
        self.shape = [list(r) for r in zip(*self.shape[::-1])]

# ───────── GAME LOGIC ─────────
class Tetris:
    def __init__(self):
        self.grid = [[0]*GRID_W for _ in range(GRID_H)]
        self.score = 0
        self.level = 0
        self.lines = 0
        self.bag = list(SHAPES.keys())
        self.current = self.new_piece()
        self.next = self.new_piece()
        self.tick = 0
        self.fall_speed = GRAVITY[self.level]
        self.gameover = False

    def new_piece(self):
        if not self.bag:
            self.bag = list(SHAPES.keys())
        kind = self.bag.pop(random.randrange(len(self.bag)))
        return Piece(GRID_W//2 - len(SHAPES[kind][0])//2, 0, [row[:] for row in SHAPES[kind]], list(SHAPES.keys()).index(kind)+1)

    def valid(self, shape, offx, offy):
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    nx, ny = offx + x, offy + y
                    if nx < 0 or nx >= GRID_W or ny >= GRID_H:
                        return False
                    if ny >= 0 and self.grid[ny][nx]:
                        return False
        return True

    def lock(self):
        for y, row in enumerate(self.current.shape):
            for x, cell in enumerate(row):
                if cell:
                    if self.current.y + y < 0:
                        self.gameover = True
                        return
                    self.grid[self.current.y+y][self.current.x+x] = self.current.color
        self.clear_lines()
        self.current = self.next
        self.next = self.new_piece()
        self.fall_speed = GRAVITY[min(self.level, 29)]

    def clear_lines(self):
        new = [r for r in self.grid if any(c==0 for c in r)]
        cleared = GRID_H - len(new)
        self.lines += cleared
        self.score += [0,40,100,300,1200][cleared]*(self.level+1)
        while len(new) < GRID_H: new.insert(0,[0]*GRID_W)
        self.grid = new
        if self.lines >= (self.level+1)*10:
            self.level = min(self.level+1, 29)

    def move(self, dx):
        if self.valid(self.current.shape, self.current.x+dx, self.current.y):
            self.current.x += dx

    def drop(self):
        if self.valid(self.current.shape, self.current.x, self.current.y+1):
            self.current.y += 1
        else:
            self.lock()

    def harddrop(self):
        while self.valid(self.current.shape, self.current.x, self.current.y+1):
            self.current.y += 1
        self.lock()

# ───────── DRAWING ─────────
def draw_grid(surf, grid):
    for y,row in enumerate(grid):
        for x,cell in enumerate(row):
            pygame.draw.rect(surf, COLORS[cell], (x*BLOCK,y*BLOCK,BLOCK,BLOCK))
    for x in range(GRID_W+1):
        pygame.draw.line(surf,(40,40,40),(x*BLOCK,0),(x*BLOCK,SCREEN_H))
    for y in range(GRID_H+1):
        pygame.draw.line(surf,(40,40,40),(0,y*BLOCK),(GRID_W*BLOCK,y*BLOCK))

def draw_piece(surf,piece,offx,offy):
    for y,row in enumerate(piece.shape):
        for x,cell in enumerate(row):
            if cell:
                pygame.draw.rect(surf,COLORS[piece.color],
                                 ((piece.x+x+offx)*BLOCK,(piece.y+y+offy)*BLOCK,BLOCK,BLOCK))

def draw_text(surf,text,size,x,y):
    f = pygame.font.SysFont("Consolas",size,True)
    surf.blit(f.render(text,True,(255,255,255)),(x,y))

# ───────── PROCEDURAL MUSIC ─────────
def gen_tone(freq,dur):
    sr=44100
    t=np.linspace(0,dur,int(sr*dur))
    wave=(np.sin(2*math.pi*freq*t)*32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack((wave,wave)))

def play_music():
    tones=[220,330,440,550,660,880]
    for f in tones:
        gen_tone(f,0.1).play()
    pygame.time.set_timer(pygame.USEREVENT,1000)

# ───────── MAIN ─────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W,SCREEN_H))
    clock = pygame.time.Clock()
    game = Tetris()
    fall_counter = 0
    pygame.display.set_caption("TETRIS — NES Edition (Samsoft 2025)")
    pygame.mixer.init()
    play_music()

    while True:
        if game.gameover:
            screen.fill((0,0,0))
            draw_text(screen,"GAME OVER",40,80,200)
            draw_text(screen,"Press R to restart",20,90,250)
            pygame.display.flip()
            for e in pygame.event.get():
                if e.type==pygame.QUIT: sys.exit()
                if e.type==pygame.KEYDOWN and e.key==pygame.K_r: main()
            continue

        for e in pygame.event.get():
            if e.type==pygame.QUIT: sys.exit()
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_LEFT: game.move(-1)
                elif e.key==pygame.K_RIGHT: game.move(1)
                elif e.key==pygame.K_UP:
                    old=game.current.shape
                    game.current.rotate()
                    if not game.valid(game.current.shape,game.current.x,game.current.y):
                        game.current.shape=old
                elif e.key==pygame.K_DOWN: game.drop()
                elif e.key==pygame.K_SPACE: game.harddrop()

        fall_counter += 1
        if fall_counter >= game.fall_speed:
            fall_counter = 0
            game.drop()

        screen.fill((0,0,0))
        draw_grid(screen, game.grid)
        draw_piece(screen, game.current, 0, 0)
        draw_piece(screen, game.next, GRID_W+1, 2)
        draw_text(screen,f"Score: {game.score}",20,GRID_W*BLOCK+10,20)
        draw_text(screen,f"Lines: {game.lines}",20,GRID_W*BLOCK+10,50)
        draw_text(screen,f"Level: {game.level}",20,GRID_W*BLOCK+10,80)
        draw_text(screen,"Next:",20,GRID_W*BLOCK+10,120)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
