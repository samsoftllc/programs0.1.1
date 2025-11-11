#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTRA!TETRIS 0.1  —  Copyright-Free Falling Block Engine
[C] Samsoft [2025]  •  [C] The Tetris Company (Acknowledgment only, no assets)
Classic 29-level progression → authentic killscreen speed simulation.
Completely muted (no audio system initialized).
"""

import math, random, sys, pygame
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# ───────── CONFIG ─────────
GRID_WIDTH, GRID_HEIGHT = 10, 20
BLOCK_SIZE = 32
SIDE_PANEL_WIDTH = 200
SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE + SIDE_PANEL_WIDTH
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
FPS = 60
LINES_PER_LEVEL = 10
MAX_LEVEL = 29

BG_COLOR = (10, 15, 25)
GRID_COLOR = (30, 40, 55)
TEXT_COLOR = (240, 240, 255)

# ───────── TETROMINOES ─────────
SHAPES: Dict[str, List[List[List[int]]]] = {
    "I": [
        [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
        [[0,0,1,0],[0,0,1,0],[0,0,1,0],[0,0,1,0]],
    ],
    "J": [
        [[1,0,0],[1,1,1],[0,0,0]],
        [[0,1,1],[0,1,0],[0,1,0]],
        [[0,0,0],[1,1,1],[0,0,1]],
        [[0,1,0],[0,1,0],[1,1,0]],
    ],
    "L": [
        [[0,0,1],[1,1,1],[0,0,0]],
        [[0,1,0],[0,1,0],[0,1,1]],
        [[0,0,0],[1,1,1],[1,0,0]],
        [[1,1,0],[0,1,0],[0,1,0]],
    ],
    "O": [[[1,1],[1,1]]],
    "S": [
        [[0,1,1],[1,1,0],[0,0,0]],
        [[0,1,0],[0,1,1],[0,0,1]],
    ],
    "T": [
        [[0,1,0],[1,1,1],[0,0,0]],
        [[0,1,0],[0,1,1],[0,1,0]],
        [[0,0,0],[1,1,1],[0,1,0]],
        [[0,1,0],[1,1,0],[0,1,0]],
    ],
    "Z": [
        [[1,1,0],[0,1,1],[0,0,0]],
        [[0,0,1],[0,1,1],[0,1,0]],
    ],
}

COLORS = {
    "I": (0,255,255),
    "J": (0,100,255),
    "L": (255,170,0),
    "O": (255,255,0),
    "S": (100,255,100),
    "T": (200,0,255),
    "Z": (255,60,60),
}

# ───────── DATA CLASSES ─────────
@dataclass
class Piece:
    shape_key: str
    matrix_index: int
    x: int
    y: int
    @property
    def matrix(self): return SHAPES[self.shape_key][self.matrix_index % len(SHAPES[self.shape_key])]
    def rotate(self): self.matrix_index = (self.matrix_index + 1) % len(SHAPES[self.shape_key])

# ───────── HELPERS ─────────
def create_board(): return [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
def get_bag(): bag = list(SHAPES.keys()); random.shuffle(bag); return bag

def valid_position(p, board):
    for r,row in enumerate(p.matrix):
        for c,val in enumerate(row):
            if not val: continue
            nx, ny = p.x+c, p.y+r
            if nx<0 or nx>=GRID_WIDTH or ny>=GRID_HEIGHT: return False
            if ny>=0 and board[ny][nx] is not None: return False
    return True

def lock_piece(p, board):
    for r,row in enumerate(p.matrix):
        for c,val in enumerate(row):
            if val:
                x,y = p.x+c, p.y+r
                if 0<=y<GRID_HEIGHT: board[y][x] = p.shape_key

def clear_lines(board):
    new_board = [r for r in board if any(cell is None for cell in r)]
    cleared = GRID_HEIGHT - len(new_board)
    while len(new_board)<GRID_HEIGHT:
        new_board.insert(0,[None]*GRID_WIDTH)
    board[:] = new_board
    return cleared

def calc_level(lines): return min(MAX_LEVEL, lines//LINES_PER_LEVEL)
def fall_speed(lv): return 0.02 if lv>=MAX_LEVEL else max(0.05, 0.8 - (lv*0.05))

def draw_board(surf, board):
    for y,row in enumerate(board):
        for x,cell in enumerate(row):
            rect = pygame.Rect(x*BLOCK_SIZE, y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surf, GRID_COLOR if not cell else COLORS[cell], rect)
            pygame.draw.rect(surf, BG_COLOR, rect, 1)

def draw_piece(surf, piece):
    for r,row in enumerate(piece.matrix):
        for c,val in enumerate(row):
            if not val: continue
            rect = pygame.Rect((piece.x+c)*BLOCK_SIZE, (piece.y+r)*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            if rect.bottom<0: continue
            pygame.draw.rect(surf, COLORS[piece.shape_key], rect)
            pygame.draw.rect(surf, BG_COLOR, rect, 1)

def draw_next(surf, piece, ox, oy):
    for r,row in enumerate(piece.matrix):
        for c,val in enumerate(row):
            if val:
                rect = pygame.Rect(ox+c*BLOCK_SIZE, oy+r*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(surf, COLORS[piece.shape_key], rect)
                pygame.draw.rect(surf, BG_COLOR, rect, 1)

def render_text(surf, font, text, pos):
    surf.blit(font.render(text, True, TEXT_COLOR), pos)

def spawn(bag):
    if not bag: bag.extend(get_bag())
    s = bag.pop()
    m = SHAPES[s][0]
    startx = GRID_WIDTH//2 - len(m[0])//2
    return Piece(s, 0, startx, -2)

def game_over(board): return any(board[0][x] for x in range(GRID_WIDTH))

# ───────── MAIN LOOP ─────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("ULTRA!TETRIS 0.1 — Samsoft Edition")
    clock = pygame.time.Clock()
    font_s = pygame.font.SysFont("fira sans", 18)
    font_l = pygame.font.SysFont("fira sans", 36, bold=True)

    board = create_board()
    bag=[]
    cur, nxt = spawn(bag), spawn(bag)
    fall_t, lines, level, score = 0,0,0,0
    soft=False; running=True

    while running:
        dt = clock.tick(FPS)/1000
        fall_t += dt
        level = calc_level(lines)
        spd = fall_speed(level)
        if soft: spd = min(0.02, spd/3)

        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            elif e.type==pygame.KEYDOWN:
                if e.key==pygame.K_ESCAPE: running=False
                elif e.key==pygame.K_LEFT:
                    p=Piece(cur.shape_key,cur.matrix_index,cur.x-1,cur.y)
                    if valid_position(p,board): cur.x-=1
                elif e.key==pygame.K_RIGHT:
                    p=Piece(cur.shape_key,cur.matrix_index,cur.x+1,cur.y)
                    if valid_position(p,board): cur.x+=1
                elif e.key==pygame.K_DOWN: soft=True
                elif e.key in (pygame.K_UP,pygame.K_x):
                    r=Piece(cur.shape_key,cur.matrix_index,cur.x,cur.y); r.rotate()
                    if valid_position(r,board): cur.rotate()
                elif e.key in (pygame.K_z,pygame.K_LCTRL):
                    r=Piece(cur.shape_key,cur.matrix_index,cur.x,cur.y)
                    r.matrix_index=(cur.matrix_index-1)%len(SHAPES[cur.shape_key])
                    if valid_position(r,board): cur.matrix_index=r.matrix_index
                elif e.key==pygame.K_SPACE:
                    while valid_position(Piece(cur.shape_key,cur.matrix_index,cur.x,cur.y+1),board):
                        cur.y+=1
                    fall_t = spd
            elif e.type==pygame.KEYUP and e.key==pygame.K_DOWN: soft=False

        if fall_t>=spd:
            fall_t=0
            mv=Piece(cur.shape_key,cur.matrix_index,cur.x,cur.y+1)
            if valid_position(mv,board): cur.y+=1
            else:
                lock_piece(cur,board)
                cleared=clear_lines(board)
                if cleared:
                    lines+=cleared
                    base={1:100,2:300,3:500,4:800}
                    score+=base.get(cleared,1200)*(level+1)
                cur,nxt = nxt,spawn(bag)
                if not valid_position(cur,board): running=False

        screen.fill(BG_COLOR)
        pf = pygame.Surface((GRID_WIDTH*BLOCK_SIZE, SCREEN_HEIGHT))
        draw_board(pf,board); draw_piece(pf,cur)
        screen.blit(pf,(0,0))
        px = GRID_WIDTH*BLOCK_SIZE+12
        render_text(screen,font_l,"ULTRA!TETRIS",(px,20))
        render_text(screen,font_s,f"Score: {score}",(px,100))
        render_text(screen,font_s,f"Lines: {lines}",(px,130))
        render_text(screen,font_s,f"Level: {level}",(px,160))
        render_text(screen,font_s,"Next:",(px,210))
        ns = pygame.Surface((4*BLOCK_SIZE,4*BLOCK_SIZE))
        draw_next(ns,nxt,BLOCK_SIZE//2,BLOCK_SIZE//2)
        screen.blit(ns,(px,240))
        if level>=MAX_LEVEL:
            render_text(screen,font_s,"Level 29 — Killscreen!",(px,360))
        pygame.display.flip()

    pygame.quit(); sys.exit()

if __name__=="__main__":
    main()
