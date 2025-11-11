#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TETRIS — NES Edition
[C] Samsoft [2025]  •  [C] The Tetris Company (Acknowledgment only, no assets)
Modified to match NES Tetris fully: main menu, all levels/killscreen, OST placeholders, B-Type, accurate mechanics, level-based palettes, high scores with name entry.
Completely muted if music off; music loads with error handling if files missing.
"""

import math, random, sys, pygame, json
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# ───────── CONFIG ─────────
GRID_WIDTH, GRID_HEIGHT = 10, 20
BLOCK_SIZE = 32
SIDE_PANEL_WIDTH = 200
SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE + SIDE_PANEL_WIDTH
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
FPS = 60
GRAVITY_TABLE = [48,43,38,33,28,23,18,13,8,6,5,5,5,4,4,4,3,3,3,2,2,2,2,2,2,2,2,2,2,1] + [1] * 100  # NES NTSC frames per row, level 0-29+
MAX_LEVEL = 255  # Allow beyond 29 for killscreen continuation

BG_COLOR = (10, 15, 25)
GRID_COLOR = (30, 40, 55)
TEXT_COLOR = (240, 240, 255)

# NES-inspired palettes (main piece color RGB for each group of 10 levels)
PALETTES = [
    (15, 99, 255),   # Level 0-9: Blue
    (106, 165, 0),   # 10-19: Green
    (188, 64, 255),  # 20-29: Purple
    (60, 183, 0),    # 30-39: Green
    (44, 183, 94),   # 40-49: Greenish
    (77, 77, 255),   # 50-59: Blue
    (88, 88, 88),    # 60-69: Gray
    (96, 0, 53),     # 70-79: Dark red
    (160, 33, 56),   # 80-89: Red
    (199, 100, 78),  # 90-99: Orange
]

COLORS = {
    'locked': (128, 128, 128),  # Gray for locked pieces, as in NES
}

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
                if 0<=y<GRID_HEIGHT: board[y][x] = 'locked'  # Use 'locked' for gray color

def clear_lines(board):
    new_board = [r for r in board if any(cell is None for cell in r)]
    cleared = GRID_HEIGHT - len(new_board)
    while len(new_board)<GRID_HEIGHT:
        new_board.insert(0,[None]*GRID_WIDTH)
    board[:] = new_board
    return cleared

def effective_level(lines, start_level): return max(start_level, lines // 10)

def draw_board(surf, board):
    for y,row in enumerate(board):
        for x,cell in enumerate(row):
            rect = pygame.Rect(x*BLOCK_SIZE, y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(surf, GRID_COLOR if not cell else COLORS[cell], rect)
            pygame.draw.rect(surf, BG_COLOR, rect, 1)

def draw_piece(surf, piece, color):
    for r,row in enumerate(piece.matrix):
        for c,val in enumerate(row):
            if not val: continue
            rect = pygame.Rect((piece.x+c)*BLOCK_SIZE, (piece.y+r)*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            if rect.bottom<0: continue
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, BG_COLOR, rect, 1)

def draw_next(surf, piece, ox, oy, color):
    for r,row in enumerate(piece.matrix):
        for c,val in enumerate(row):
            if val:
                rect = pygame.Rect(ox+c*BLOCK_SIZE, oy+r*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                pygame.draw.rect(surf, color, rect)
                pygame.draw.rect(surf, BG_COLOR, rect, 1)

def render_text(surf, font, text, pos):
    surf.blit(font.render(text, True, TEXT_COLOR), pos)

def spawn(last_key):
    shapes_list = list(SHAPES.keys())
    roll = random.randrange(8)
    if roll == 7 or (last_key is not None and shapes_list[roll % 7] == last_key):
        roll = random.randrange(7)
    s = shapes_list[roll % 7]
    m = SHAPES[s][0]
    startx = GRID_WIDTH//2 - len(m[0])//2
    return Piece(s, 0, startx, -2), s

def game_over(board): return any(board[0][x] is not None for x in range(GRID_WIDTH))

def load_high_scores():
    try:
        with open('highscores.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'A': [], 'B': []}

def save_high_scores(high_scores):
    with open('highscores.json', 'w') as f:
        json.dump(high_scores, f)

def enter_name(screen, font_s):
    running = True
    name = list('AAA')
    pos = 0
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT: pos = (pos - 1) % 3
                if e.key == pygame.K_RIGHT: pos = (pos + 1) % 3
                if e.key == pygame.K_UP:
                    ord_val = ord(name[pos])
                    name[pos] = chr(ord_val + 1 if ord_val < ord('Z') else ord('A'))
                if e.key == pygame.K_DOWN:
                    ord_val = ord(name[pos])
                    name[pos] = chr(ord_val - 1 if ord_val > ord('A') else ord('Z'))
                if e.key == pygame.K_RETURN: running = False
        screen.fill(BG_COLOR)
        render_text(screen, font_s, "Enter Name:", (SCREEN_WIDTH // 2 - 80, 150))
        render_text(screen, font_s, ''.join(name), (SCREEN_WIDTH // 2 - 40, 200))
        pygame.display.flip()
    return ''.join(name)

def main_menu(screen, clock, font_l, font_s):
    options = {'type': 'A', 'level': 0, 'height': 0, 'music': 1}
    selected = 0
    items = ['type', 'level', 'height', 'music']  # Removed 'next'
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT: sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: sys.exit()
                if e.key == pygame.K_UP: selected = (selected - 1) % len(items)
                if e.key == pygame.K_DOWN: selected = (selected + 1) % len(items)
                if e.key == pygame.K_LEFT:
                    if items[selected] == 'type': options['type'] = 'B' if options['type'] == 'A' else 'A'
                    if items[selected] == 'level': options['level'] = (options['level'] - 1) % 20
                    if items[selected] == 'height' and options['type'] == 'B': options['height'] = (options['height'] - 1) % 6
                    if items[selected] == 'music': options['music'] = (options['music'] - 1) % 4
                if e.key == pygame.K_RIGHT:
                    if items[selected] == 'type': options['type'] = 'B' if options['type'] == 'A' else 'A'
                    if items[selected] == 'level': options['level'] = (options['level'] + 1) % 20
                    if items[selected] == 'height' and options['type'] == 'B': options['height'] = (options['height'] + 1) % 6
                    if items[selected] == 'music': options['music'] = (options['music'] + 1) % 4
                if e.key == pygame.K_RETURN or e.key == pygame.K_SPACE: running = False
        screen.fill(BG_COLOR)
        render_text(screen, font_l, "TETRIS", (SCREEN_WIDTH // 2 - 100, 50))
        y = 120
        render_text(screen, font_s, f"Type: {options['type']}", (100, y))
        pygame.draw.rect(screen, TEXT_COLOR if selected == 0 else BG_COLOR, (90, y - 5, 200, 30), 1)
        y += 40
        render_text(screen, font_s, f"Level: {options['level']}", (100, y))
        pygame.draw.rect(screen, TEXT_COLOR if selected == 1 else BG_COLOR, (90, y - 5, 200, 30), 1)
        y += 40
        if options['type'] == 'B':
            render_text(screen, font_s, f"Height: {options['height']}", (100, y))
            pygame.draw.rect(screen, TEXT_COLOR if selected == 2 else BG_COLOR, (90, y - 5, 200, 30), 1)
            y += 40
        render_text(screen, font_s, f"Music: {'Off' if options['music'] == 0 else options['music']}", (100, y))
        pygame.draw.rect(screen, TEXT_COLOR if selected == (3 if options['type'] == 'A' else 3) else BG_COLOR, (90, y - 5, 200, 30), 1)
        pygame.display.flip()
    options['next'] = True  # Always on for NES authenticity
    return options

def game_over_screen(screen, font_l, font_s, score, lines, level, b_type, won, high_scores, type_key):
    pygame.mixer.music.stop()
    try:
        pygame.mixer.music.load('highscore.mp3')
        pygame.mixer.music.play(-1)
    except pygame.error:
        pass
    if b_type and won:
        try:
            pygame.mixer.music.load('ending.mp3')
            pygame.mixer.music.play(0)
        except pygame.error:
            pass
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN: running = False
        screen.fill(BG_COLOR)
        render_text(screen, font_l, "GAME OVER" if not (b_type and won) else "CONGRATULATIONS!", (SCREEN_WIDTH // 2 - 150, 200))
        render_text(screen, font_s, f"Score: {score}", (SCREEN_WIDTH // 2 - 100, 280))
        render_text(screen, font_s, f"Lines: {lines}", (SCREEN_WIDTH // 2 - 100, 310))
        render_text(screen, font_s, f"Level: {level}", (SCREEN_WIDTH // 2 - 100, 340))
        render_text(screen, font_s, "High Scores:", (SCREEN_WIDTH // 2 - 100, 370))
        for i, (s, n) in enumerate(high_scores[type_key]):
            render_text(screen, font_s, f"{i+1}. {n} - {s}", (SCREEN_WIDTH // 2 - 100, 400 + i * 30))
        pygame.display.flip()

# ───────── MAIN LOOP ─────────
def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except pygame.error:
        print("Audio initialization failed; game will be muted.")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TETRIS — NES Edition")
    clock = pygame.time.Clock()
    font_s = pygame.font.SysFont("fira sans", 18)
    font_l = pygame.font.SysFont("fira sans", 36, bold=True)

    high_scores = load_high_scores()

    while True:  # Loop back to menu after game
        options = main_menu(screen, clock, font_l, font_s)
        start_level = options['level']
        b_type = options['type'] == 'B'
        height = options['height']
        music_choice = options['music']
        show_next = options['next']

        if music_choice > 0:
            try:
                pygame.mixer.music.load(f"music{music_choice}.mp3")
                pygame.mixer.music.play(-1)
            except pygame.error:
                pass

        board = create_board()
        if b_type:
            garbage_heights = [0, 3, 5, 8, 10, 12][height]
            for i in range(garbage_heights):
                row = [random.choice(list(SHAPES.keys())) for _ in range(GRID_WIDTH)]
                hole = random.randint(0, GRID_WIDTH - 1)
                row[hole] = None
                board[GRID_HEIGHT - 1 - i] = row

        last_key = None
        cur, cur_key = spawn(last_key)
        last_key = cur_key
        nxt, nxt_key = spawn(last_key)
        last_key = nxt_key
        fall_t, lines, score = 0, 0, 0
        soft = False
        running = True
        won = False

        while running:
            dt = clock.tick(FPS) / 1000
            fall_t += dt
            level = start_level if b_type else effective_level(lines, start_level)
            frames_per_row = GRAVITY_TABLE[min(level, len(GRAVITY_TABLE) - 1)]
            spd = frames_per_row / FPS
            if soft: spd /= 2  # NES soft drop: twice the speed (half the time interval)

            # Simulate palette index (normal for <100, glitched gray for >=100)
            palette_index = level // 10
            if palette_index < 10:
                current_piece_color = PALETTES[palette_index]
            else:
                current_piece_color = (128, 128, 128)  # Gray for glitched/killscreen

            for e in pygame.event.get():
                if e.type == pygame.QUIT: running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: running = False
                    elif e.key == pygame.K_LEFT:
                        p = Piece(cur.shape_key, cur.matrix_index, cur.x - 1, cur.y)
                        if valid_position(p, board): cur.x -= 1
                    elif e.key == pygame.K_RIGHT:
                        p = Piece(cur.shape_key, cur.matrix_index, cur.x + 1, cur.y)
                        if valid_position(p, board): cur.x += 1
                    elif e.key == pygame.K_DOWN: soft = True
                    elif e.key in (pygame.K_UP, pygame.K_x):
                        r = Piece(cur.shape_key, cur.matrix_index, cur.x, cur.y); r.rotate()
                        if valid_position(r, board): cur.rotate()
                    elif e.key in (pygame.K_z, pygame.K_LCTRL):
                        r = Piece(cur.shape_key, cur.matrix_index, cur.x, cur.y)
                        r.matrix_index = (cur.matrix_index - 1) % len(SHAPES[cur.shape_key])
                        if valid_position(r, board): cur.matrix_index = r.matrix_index
                    elif e.key == pygame.K_SPACE:
                        while valid_position(Piece(cur.shape_key, cur.matrix_index, cur.x, cur.y + 1), board):
                            cur.y += 1
                        fall_t = spd
                elif e.type == pygame.KEYUP and e.key == pygame.K_DOWN: soft = False

            if fall_t >= spd:
                fall_t -= spd
                mv = Piece(cur.shape_key, cur.matrix_index, cur.x, cur.y + 1)
                if valid_position(mv, board):
                    cur.y += 1
                    if soft: score += 1  # NES soft drop points
                else:
                    lock_piece(cur, board)
                    cleared = clear_lines(board)
                    if cleared:
                        lines += cleared
                        base = {1: 40, 2: 100, 3: 300, 4: 1200}
                        score += base.get(cleared, 1200) * (level + 1)
                    cur, nxt = nxt, spawn(last_key)
                    last_key = nxt_key
                    nxt, nxt_key = spawn(last_key)
                    last_key = nxt_key
                    if not valid_position(cur, board) or game_over(board):
                        running = False
                    if b_type and lines >= 25:
                        running = False
                        won = True

            screen.fill(BG_COLOR)
            pf = pygame.Surface((GRID_WIDTH * BLOCK_SIZE, SCREEN_HEIGHT))
            draw_board(pf, board)
            draw_piece(pf, cur, current_piece_color)
            screen.blit(pf, (0, 0))
            px = GRID_WIDTH * BLOCK_SIZE + 12
            render_text(screen, font_l, "TETRIS", (px, 20))
            render_text(screen, font_s, f"Score: {score}", (px, 100))
            render_text(screen, font_s, f"Lines: {lines}", (px, 130))
            render_text(screen, font_s, f"Level: {level}", (px, 160))
            if show_next:
                render_text(screen, font_s, "Next:", (px, 210))
                ns = pygame.Surface((4 * BLOCK_SIZE, 4 * BLOCK_SIZE))
                draw_next(ns, nxt, BLOCK_SIZE // 2, BLOCK_SIZE // 2, current_piece_color)
                screen.blit(ns, (px, 240))
            if level >= 29:
                render_text(screen, font_s, "Level 29 — Killscreen!", (px, 360))
            pygame.display.flip()

        # High score handling
        type_key = 'B' if b_type else 'A'
        scores = high_scores[type_key]
        if len(scores) < 3 or score > min(s[0] for s in scores):
            name = enter_name(screen, font_s)
            scores.append((score, name))
            scores = sorted(scores, key=lambda x: x[0], reverse=True)[:3]
            high_scores[type_key] = scores
            save_high_scores(high_scores)

        game_over_screen(screen, font_l, font_s, score, lines, level, b_type, won, high_scores, type_key)
        pygame.mixer.music.stop()

    pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()
