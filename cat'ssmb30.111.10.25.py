#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMB3-style single-file Pygame engine (5 worlds × 3 levels, Boom-style bosses).
- External assets are DISABLED (files = off). Everything renders with rectangles,
  circles, and text. Pure code graphics only, enhanced with procedural details inspired by SMB3 sprites.
- Overworld uses node paths and islands (SMB3-inspired).
- Levels are lightweight tilemaps with collisions, a goal, simple enemies,
  and a boss arena per world. Final world level 3 is the finale.
- Physics aim for "SMB3-ish": run acceleration, variable jump, skid, and a
  P-meter that fills while sprinting. When full, you get a short "glide"
  (slow fall) to mimic a simplified tail-flight feel—purely original code.
How to run locally (requires a desktop with a display):
    pip install pygame
    python program.py
Controls (Overworld):
    Arrow keys / WASD – move cursor between unlocked nodes
    Enter/Return – enter level
    Esc – quit
Controls (Inside levels/boss):
    Arrow keys / A/D – move
    Shift – hold to run
    Z / K / Space – jump (hold for higher jump)
    R – quick restart of current level
    Esc – quit game
Notes & Legal:
- Names in comments are purely for reference to gameplay styles. No third‑party
  assets are included. All graphics are procedurally generated, inspired by public descriptions of SMB3 sprites.
- Pure Python + Pygame implementation.
"""
import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame
# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
WIDTH, HEIGHT = 960, 540
TILE = 32
FPS = 60
# Physics tuned toward "SMB3-ish" feel (not a byte-perfect clone)
GRAVITY = 0.60
JUMP_VEL = -11.6
MIN_JUMP_RELEASE = -4.0 # when player releases jump early, clamp vy
ACCEL_GROUND = 0.55
ACCEL_AIR = 0.32
FRICTION_GROUND = 0.80
MAX_WALK = 3.2
MAX_RUN = 6.0
SKID_THRESHOLD = 0.35
# P-meter (fills while running close to max speed on ground)
PMETER_MAX = 7
PMETER_GAIN_SPEED = 0.08 # per frame while sprinting
PMETER_DECAY_SPEED = 0.04 # per frame when not sprinting
GLIDE_GRAVITY = 0.22 # gravity when P-meter is full and player holding jump in air
GLIDE_TIME = 60 # frames of glide available after leaving ground with full meter
# Gameplay
START_HEARTS = 3
INVULN_FRAMES = 60
# Colours (soft toy-like palette, inspired by SMB3)
WHITE = (255, 255, 255)
BLACK = ( 20, 20, 22)
GRAY = (140, 140, 140)
LIGHT = (224, 232, 248)
SKY = (160, 208, 255)
SEA = ( 83, 153, 211)
GRASS = ( 84, 196, 96)
DIRT = (149, 109, 63)
ROCK = (101, 79, 58)
GOLD = (255, 208, 64)
RED = (231, 76, 60)
ORANGE = (255, 159, 67)
BLUE = ( 75, 119, 190)
PURPLE = (142, 84, 233)
BEIGE = (248, 216, 120) # SMB3 title screen background color
SKIN = (255, 204, 153) # Approximate Mario skin tone
BROWN = (139, 69, 19) # For Goomba, etc.
# Game states
STATE_TITLE = "title"
STATE_OVERWORLD = "overworld"
STATE_LEVEL = "level"
STATE_BOSS = "boss"
STATE_ENDING = "ending"
# -----------------------------------------------------------------------------
# SMALL UTILS
# -----------------------------------------------------------------------------
def clamp(v, lo, hi):
    return max(lo, min(hi, v))
def rect_from_tile(x, y):
    return pygame.Rect(x*TILE, y*TILE, TILE, TILE)
def text(surface, font, msg, pos, color=BLACK, center=False, shadow=True):
    if shadow:
        s = font.render(msg, True, (0,0,0))
        sp = (pos[0]+1, pos[1]+1)
        if center:
            sr = s.get_rect(center=pos)
            sp = (sr.x+1, sr.y+1)
        surface.blit(s, sp)
    img = font.render(msg, True, color)
    if center:
        r = img.get_rect(center=pos)
        surface.blit(img, r)
    else:
        surface.blit(img, pos)
# -----------------------------------------------------------------------------
# CORE ENTITIES
# -----------------------------------------------------------------------------
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 32)  # SMB3-like size for big Mario
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.spawn = (x, y)
        self.hearts = START_HEARTS
        self.max_hearts = START_HEARTS
        self.invuln = 0
        # P-meter / glide
        self.pmeter = 0.0
        self.glide_left = 0
        self.jump_held = False
    # -------------------------- Input & Physics -----------------------------
    def input_move(self, keys):
        move = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move += 1
        running = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        target_speed = MAX_RUN if running else MAX_WALK
        # Facing & skid
        if move != 0:
            self.facing = 1 if move > 0 else -1
        accel = ACCEL_GROUND if self.on_ground else ACCEL_AIR
        # Accelerate toward target in input direction
        if move != 0:
            desired = move * target_speed
            if self.vx < desired:
                self.vx = min(desired, self.vx + accel)
            elif self.vx > desired:
                self.vx = max(desired, self.vx - accel)
        else:
            # No input → friction if on ground
            if self.on_ground:
                self.vx *= FRICTION_GROUND
                if abs(self.vx) < 0.05:
                    self.vx = 0.0
        # P-meter handling (only increases while sprinting near max on ground)
        if self.on_ground and running and move != 0 and abs(self.vx) >= MAX_RUN - 0.5:
            self.pmeter = min(PMETER_MAX, self.pmeter + PMETER_GAIN_SPEED)
        else:
            self.pmeter = max(0.0, self.pmeter - PMETER_DECAY_SPEED)
    def input_jump(self, keys):
        pressed = (keys[pygame.K_z] or keys[pygame.K_k] or keys[pygame.K_SPACE])
        if pressed and not self.jump_held and self.on_ground:
            self.vy = JUMP_VEL
            self.on_ground = False
            # If P-meter is full at takeoff, prime glide
            if self.pmeter >= PMETER_MAX - 1e-6:
                self.glide_left = GLIDE_TIME
        # variable-height jump when released early
        if not pressed and self.jump_held and self.vy < MIN_JUMP_RELEASE:
            self.vy = MIN_JUMP_RELEASE
        self.jump_held = pressed
    def apply_gravity(self):
        if self.glide_left > 0 and not self.on_ground and self.jump_held:
            # gentle descent
            self.vy += GLIDE_GRAVITY
            self.glide_left -= 1
        else:
            self.vy += GRAVITY
        self.vy = clamp(self.vy, -50, 20)
    def collides(self, rects: List[pygame.Rect]) -> List[pygame.Rect]:
        hits = []
        pr = self.rect
        for r in rects:
            # Quick AABB test
            if pr.right > r.left and pr.left < r.right and pr.bottom > r.top and pr.top < r.bottom:
                hits.append(r)
        return hits
    def move_and_collide(self, solids: List[pygame.Rect]):
        # Horizontal
        self.rect.x += int(round(self.vx))
        hits = self.collides(solids)
        for h in hits:
            if self.vx > 0:
                self.rect.right = h.left
            elif self.vx < 0:
                self.rect.left = h.right
            self.vx = 0.0
        # Vertical
        self.rect.y += int(round(self.vy))
        hits = self.collides(solids)
        self.on_ground = False
        for h in hits:
            if self.vy > 0:
                self.rect.bottom = h.top
                self.vy = 0.0
                self.on_ground = True
            elif self.vy < 0:
                self.rect.top = h.bottom
                self.vy = 0.0
    # ------------------------------ Combat ----------------------------------
    def hurt(self):
        if self.invuln > 0:
            return
        self.hearts -= 1
        self.invuln = INVULN_FRAMES
        if self.hearts <= 0:
            self.reset()
    def reset(self):
        self.rect.topleft = self.spawn
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.hearts = self.max_hearts
        self.invuln = 0
        self.pmeter = 0.0
        self.glide_left = 0
        self.jump_held = False
    # ------------------------------ Update ----------------------------------
    def update(self, keys, solids, hazards, enemies, projectiles):
        self.input_move(keys)
        self.input_jump(keys)
        self.apply_gravity()
        self.move_and_collide(solids)
        # Hazards (instant respawn)
        for hz in hazards:
            if self.rect.colliderect(hz):
                self.reset()
        # Enemies
        for e in enemies:
            if not e.alive:
                continue
            if self.rect.colliderect(e.rect):
                # Stomp from above vs side-hit
                if self.vy > 2 and self.rect.bottom - e.rect.top < 16:
                    e.stomped()
                    self.vy = JUMP_VEL * 0.6
                else:
                    self.hurt()
        # Projectiles (unused for basic enemies; left for boss patterns)
        for p in projectiles:
            if p.alive and self.rect.colliderect(p.rect):
                self.hurt()
                p.alive = False
        if self.invuln > 0:
            self.invuln -= 1
    def draw(self, surface, camera_x):
        r = self.rect.move(-camera_x, 0)
        if self.invuln > 0 and (self.invuln // 4) % 2 == 1:
            flash_color = WHITE
        else:
            flash_color = None
        # Procedural Mario-inspired sprite (approximate big Mario)
        # Overall body
        pygame.draw.rect(surface, BLUE if flash_color is None else flash_color, (r.x, r.y+16, r.width, r.height-16))  # Blue overalls
        pygame.draw.rect(surface, RED if flash_color is None else flash_color, (r.x, r.y+8, r.width, 8))  # Red shirt
        # Hat
        pygame.draw.rect(surface, RED if flash_color is None else flash_color, (r.x+2, r.y, r.width-4, 4))  # Hat brim
        pygame.draw.rect(surface, RED if flash_color is None else flash_color, (r.x+4, r.y-4, r.width-8, 4))  # Hat top
        # Face
        pygame.draw.rect(surface, SKIN if flash_color is None else flash_color, (r.x+4, r.y+4, r.width-8, 4))  # Face
        pygame.draw.circle(surface, BLACK if flash_color is None else flash_color, (r.centerx + 4*self.facing, r.y + 6), 2)  # Eye
        # Mustache approximation
        pygame.draw.rect(surface, BLACK if flash_color is None else flash_color, (r.centerx + 2*self.facing, r.y+8, 4, 2))
        # Shoes
        pygame.draw.rect(surface, BROWN if flash_color is None else flash_color, (r.x+2, r.bottom-4, r.width-4, 4))
        # P-meter glow effect when full
        if self.pmeter >= PMETER_MAX - 1e-6:
            glow = pygame.Surface((r.width+8, r.height+8), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 255, 100, 60), glow.get_rect())
            surface.blit(glow, (r.x-4, r.y-4), special_flags=pygame.BLEND_ALPHA_SDL2)
class Projectile:
    def __init__(self, x, y, vx, vy, radius=6, color=PURPLE):
        self.rect = pygame.Rect(int(x-radius), int(y-radius), int(radius*2), int(radius*2))
        self.vx, self.vy = vx, vy
        self.color = color
        self.alive = True
    def update(self, solids):
        if not self.alive:
            return
        self.rect.x += int(round(self.vx))
        self.rect.y += int(round(self.vy))
        for s in solids:
            if self.rect.colliderect(s):
                self.alive = False
                break
    def draw(self, surface, camera_x):
        if not self.alive: return
        pygame.draw.ellipse(surface, self.color, self.rect.move(-camera_x, 0))
# -----------------------------------------------------------------------------
# ENEMIES
# -----------------------------------------------------------------------------
class Walker:
    """Simple goomba-like walker that flips at edges/walls."""
    def __init__(self, x, y, dir=1):
        self.rect = pygame.Rect(x, y, 16, 16)  # SMB3 Goomba size
        self.vx = 1.2 * dir
        self.alive = True
        self.squash_timer = 0
    def stomped(self):
        self.squash_timer = 20
        self.alive = False
    def update(self, solids: List[pygame.Rect]):
        if not self.alive:
            return
        # Move & collide
        self.rect.x += int(round(self.vx))
        blocked = False
        for s in solids:
            if self.rect.colliderect(s):
                blocked = True
                if self.vx > 0:
                    self.rect.right = s.left
                else:
                    self.rect.left = s.right
                break
        if blocked:
            self.vx = -self.vx
        # Edge check: if tile below ahead is empty, flip
        ahead = self.rect.move(int(8 * (1 if self.vx > 0 else -1)), 1)
        has_floor = False
        # Downward probe
        probe = self.rect.move(int(10 * (1 if self.vx > 0 else -1)), 1)
        probe.height = TILE*2
        for s in solids:
            if s.collidepoint(probe.midbottom):
                has_floor = True
                break
        if not has_floor:
            self.vx = -self.vx
    def draw(self, surface, camera_x):
        r = self.rect.move(-camera_x, 0)
        if not self.alive:
            # Squashed Goomba
            r.height = 8
            r.y += 8
            pygame.draw.ellipse(surface, BROWN, r)  # Flat brown body
            return
        # Procedural Goomba-inspired sprite
        # Body
        pygame.draw.ellipse(surface, BROWN, (r.x, r.y, r.width, r.height-4))  # Mushroom top
        pygame.draw.rect(surface, BLACK, (r.x+2, r.y+ r.height-4, r.width-4, 4))  # Feet
        # Eyes
        pygame.draw.circle(surface, WHITE, (r.centerx-4, r.y+6), 3)
        pygame.draw.circle(surface, WHITE, (r.centerx+4, r.y+6), 3)
        pygame.draw.circle(surface, BLACK, (r.centerx-4, r.y+6), 1)
        pygame.draw.circle(surface, BLACK, (r.centerx+4, r.y+6), 1)
        # Frown
        pygame.draw.arc(surface, BLACK, (r.x+4, r.y+10, r.width-8, 4), math.pi, 2*math.pi, 2)
# -----------------------------------------------------------------------------
# BOSSES
# -----------------------------------------------------------------------------
class BoomStyleBoss:
    """Small arena boss: patrol + hop, vulnerable to stomps, 3+ hits based on world."""
    def __init__(self, arena_rect: pygame.Rect, difficulty: int):
        base_hits = 3
        self.max_hp = base_hits + difficulty # scale across worlds
        self.hp = self.max_hp
        self.arena = arena_rect
        self.pos = pygame.Vector2(arena_rect.centerx, arena_rect.bottom - 40)
        self.vel = pygame.Vector2(2.0 + difficulty*0.3, 0.0)
        self.timer = 0
        self.state = "patrol"
        self.alive = True
        self.hurt_timer = 0
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.pos.x)-18, int(self.pos.y)-24, 36, 48)
    def stomped(self):
        if not self.alive: return
        self.hp -= 1
        self.hurt_timer = 20
        self.vel.y = JUMP_VEL * 0.6
        if self.hp <= 0:
            self.alive = False
    def update(self, player: Player, solids: List[pygame.Rect], projectiles: List[Projectile]):
        if not self.alive: return
        self.timer += 1
        # simple hop every so often
        if self.timer % 90 == 0 and self.rect().bottom >= self.arena.bottom - 2:
            self.vel.y = JUMP_VEL * 0.9
        # gravity
        self.vel.y += GRAVITY
        # horizontal patrol
        self.pos.x += self.vel.x
        self.pos.y += self.vel.y
        # Clamp to arena and bounce on walls/floor
        r = self.rect()
        if r.left <= self.arena.left or r.right >= self.arena.right:
            self.vel.x = -self.vel.x
            self.pos.x = clamp(self.pos.x, self.arena.left+18, self.arena.right-18)
        if r.bottom >= self.arena.bottom:
            self.pos.y = self.arena.bottom - 24
            self.vel.y = 0
        # Throw an occasional projectile to keep you moving
        if self.timer % 70 == 0:
            direction = 1 if (player.rect.centerx > self.pos.x) else -1
            vx = direction * random.uniform(2.5, 3.5)
            vy = random.uniform(-3.0, -2.0)
            projectiles.append(Projectile(self.pos.x, self.pos.y - 18, vx, vy, radius=6, color=ORANGE))
        # Stomp window
        pr = player.rect
        br = self.rect()
        if pr.colliderect(br) and player.vy > 2 and pr.bottom <= br.top + 16:
            self.stomped()
            player.vy = JUMP_VEL * 0.6
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
    def draw(self, surface, camera_x):
        r = self.rect().move(-camera_x, 0)
        base = BLUE if (self.hurt_timer // 2) % 2 == 0 else WHITE
        # Procedural Boom Boom-inspired sprite
        # Body
        pygame.draw.rect(surface, base, r, border_radius=8)
        # Head
        pygame.draw.ellipse(surface, base, (r.x+4, r.y-4, r.width-8, 12))
        # Eyes
        pygame.draw.circle(surface, BLACK, (r.centerx-5, r.y+18), 3)
        pygame.draw.circle(surface, BLACK, (r.centerx+5, r.y+18), 3)
        # Mouth
        pygame.draw.arc(surface, BLACK, (r.x+6, r.y+26, 24, 10), math.pi*0.2, math.pi-0.2, 2)
        # Arms (simple)
        pygame.draw.rect(surface, base, (r.left-8, r.centery, 8, 12))
        pygame.draw.rect(surface, base, (r.right, r.centery, 8, 12))
        # HP bar
        bw, bh = 220, 12
        bx, by = WIDTH//2 - bw//2, 16
        pygame.draw.rect(surface, BLACK, (bx-2, by-2, bw+4, bh+4), border_radius=4)
        pct = clamp(self.hp / max(1, self.max_hp), 0, 1)
        pygame.draw.rect(surface, ORANGE, (bx, by, int(bw*pct), bh), border_radius=3)
# -----------------------------------------------------------------------------
# LEVELS
# -----------------------------------------------------------------------------
@dataclass
class Level:
    raw: List[str]
    solids: List[pygame.Rect]
    hazards: List[pygame.Rect]
    enemies: List[Walker]
    goal: Optional[pygame.Rect]
    spawn: Tuple[int,int]
    width: int
    height: int
    arena_rect: Optional[pygame.Rect]
    @staticmethod
    def from_raw(raw_map: List[str]) -> "Level":
        solids: List[pygame.Rect] = []
        hazards: List[pygame.Rect] = []
        enemies: List[Walker] = []
        goal = None
        spawn = (64, 64)
        arena_rect = None
        h = len(raw_map)
        w = len(raw_map[0]) if h > 0 else 0
        for y, line in enumerate(raw_map):
            for x, ch in enumerate(line):
                if ch in ("X", "#", "-"):
                    solids.append(rect_from_tile(x, y))
                elif ch == "^":
                    hazards.append(rect_from_tile(x, y))
                elif ch == "G":
                    goal = rect_from_tile(x, y)
                elif ch == "P":
                    spawn = (x*TILE, y*TILE-2)
                elif ch == "b":
                    # enemy walker
                    enemies.append(Walker(x*TILE+5, y*TILE+10, dir=random.choice([-1,1])))
                elif ch == "B":
                    # boss arena marker row (center line); create rectangle once
                    if not arena_rect:
                        arena_rect = pygame.Rect(x*TILE-32, y*TILE-8, 20*TILE, 12*TILE)
        return Level(
            raw=raw_map,
            solids=solids,
            hazards=hazards,
            enemies=enemies,
            goal=goal,
            spawn=spawn,
            width=w*TILE,
            height=h*TILE,
            arena_rect=arena_rect
        )
    def draw_bg(self, surface, camera_x, theme=0):
        surface.fill(SKY if theme == 0 else (186, 214, 255))
        # distant clouds / hills
        for i in range(7):
            base_x = (i*220 - camera_x*0.2) % (WIDTH+300) - 150
            h = 100 + (i%3)*30
            pygame.draw.ellipse(surface, (190, 238, 255), (base_x, 40+(i%2)*10, 180, 60), 0)
            pygame.draw.ellipse(surface, (120, 200, 120), (base_x, HEIGHT-60-h, 240, h*2), 0)
        pygame.draw.rect(surface, (95, 180, 100), (0, HEIGHT-60, WIDTH, 60))
        pygame.draw.rect(surface, (75, 150, 85), (0, HEIGHT-48, WIDTH, 12))
    def draw_tiles(self, surface, camera_x):
        for r in self.solids:
            rr = r.move(-camera_x, 0)
            # Procedural ground tile inspired by SMB3 grass block
            pygame.draw.rect(surface, DIRT, rr)
            pygame.draw.rect(surface, ROCK, rr, 2)
            # Add grass top if top row
            pygame.draw.rect(surface, GRASS, (rr.x, rr.y, rr.width, 4))  # Grass layer
            pygame.draw.line(surface, BLACK, (rr.x, rr.y+4), (rr.right, rr.y+4), 1)  # Edge
        for r in self.hazards:
            rr = r.move(-camera_x, 0)
            # Procedural spike inspired by SMB3
            pygame.draw.polygon(surface, RED, [(rr.left, rr.bottom), (rr.centerx, rr.top), (rr.right, rr.bottom)])
            pygame.draw.line(surface, BLACK, (rr.left, rr.bottom), (rr.centerx, rr.top), 1)
            pygame.draw.line(surface, BLACK, (rr.right, rr.bottom), (rr.centerx, rr.top), 1)
        if self.goal:
            rr = self.goal.move(-camera_x, 0)
            # Procedural flag goal inspired by SMB3
            pygame.draw.rect(surface, GOLD, rr)
            # flag pole
            pygame.draw.rect(surface, (200, 200, 200), (rr.centerx-2, rr.y-60, 4, 60))
            pygame.draw.polygon(surface, RED, [(rr.centerx, rr.y-60), (rr.centerx+20, rr.y-50), (rr.centerx, rr.y-40)])
            # Add triangle flag details
            pygame.draw.line(surface, BLACK, (rr.centerx, rr.y-60), (rr.centerx+20, rr.y-50), 1)
            pygame.draw.line(surface, BLACK, (rr.centerx+20, rr.y-50), (rr.centerx, rr.y-40), 1)
# -----------------------------------------------------------------------------
# OVERWORLD (SMB3-inspired)
# -----------------------------------------------------------------------------
class Node:
    def __init__(self, world, index, pos):
        self.world = world
        self.index = index
        self.pos = pos
        self.unlocked = (world == 0 and index == 0)
        self.cleared = False
class OverworldMap:
    def __init__(self, worlds_levels: List[int]):
        self.worlds_levels = worlds_levels # counts per world
        self.nodes: List[Node] = []
        self.paths: List[Tuple[int,int]] = []
        self.cursor = 0
        self._build()
    def _build(self):
        # Layout five islands horizontally
        margin_x = 120
        gap_x = (WIDTH - 2*margin_x) // 4
        y_base = HEIGHT//2 + 40
        idx = 0
        for w, count in enumerate(self.worlds_levels):
            cx = margin_x + w*gap_x
            for i in range(count):
                angle = i * (math.pi*2 / max(4, count))
                r = 58 + (i%2)*22
                x = int(cx + math.cos(angle)*r)
                y = int(y_base + math.sin(angle)*r*0.55 - (w%2)*22)
                self.nodes.append(Node(w, i, (x, y)))
                if i > 0:
                    self.paths.append((idx-1, idx))
                idx += 1
    def unlock_path_after_clear(self, world, index):
        # Unlock next node in world, else first node of next world
        for i, n in enumerate(self.nodes):
            if n.world == world and n.index == index:
                n.cleared = True
                # next in same world
                for m in self.nodes:
                    if m.world == world and m.index == index+1:
                        m.unlocked = True
                # last in world -> unlock first of next
                if index + 1 >= self.worlds_levels[world]:
                    for m in self.nodes:
                        if m.world == world+1 and m.index == 0:
                            m.unlocked = True
                break
    def move_cursor(self, dx, dy):
        if dx == dy == 0: return
        cur = self.nodes[self.cursor]
        best = None
        best_score = 1e9
        for i, n in enumerate(self.nodes):
            if not n.unlocked: continue
            v = (n.pos[0]-cur.pos[0], n.pos[1]-cur.pos[1])
            dot = v[0]*dx + v[1]*dy
            if dot <= 0: continue
            dist = abs(v[0])+abs(v[1])
            if dist < best_score:
                best_score = dist
                best = i
        if best is not None:
            self.cursor = best
    def draw(self, surface, font, progress_text):
        # sky + ocean
        surface.fill(SKY)
        pygame.draw.rect(surface, SEA, (0, HEIGHT-160, WIDTH, 160))
        # islands
        for i in range(5):
            cx = 100 + i* (WIDTH-200)//4
            pygame.draw.ellipse(surface, (232, 211, 163), (cx-120, HEIGHT-120, 240, 120))
            pygame.draw.ellipse(surface, GRASS, (cx-110, HEIGHT-130, 220, 100))
        # paths
        for a, b in self.paths:
            pa = self.nodes[a].pos
            pb = self.nodes[b].pos
            pygame.draw.line(surface, (210, 210, 210), pa, pb, 4)
            pygame.draw.line(surface, WHITE, (pa[0], pa[1]-1), (pb[0], pb[1]-1), 2)
        # nodes (procedural level icons inspired by SMB3 map)
        for i, n in enumerate(self.nodes):
            c = (230,230,230) if n.unlocked else (150,150,150)
            pygame.draw.circle(surface, c, n.pos, 12)
            if n.cleared:
                pygame.draw.circle(surface, GOLD, n.pos, 6)
            # Add small castle icon for boss nodes
            if n.index == self.worlds_levels[n.world]-1:
                pygame.draw.rect(surface, RED, (n.pos[0]-6, n.pos[1]-8, 12, 8))  # Tower
                pygame.draw.triangle(surface, RED, (n.pos[0]-6, n.pos[1]-8), (n.pos[0]+6, n.pos[1]-8), (n.pos[0], n.pos[1]-14))
        # cursor ring
        cur = self.nodes[self.cursor]
        pygame.draw.circle(surface, ORANGE, cur.pos, 16, 3)
        label = f"World {cur.world+1} - Stage {cur.index+1}"
        text(surface, font, label, (WIDTH//2, 40), BLACK, center=True)
        text(surface, font, progress_text, (WIDTH//2, 70), BLACK, center=True)
# -----------------------------------------------------------------------------
# MAP TEMPLATES
# -----------------------------------------------------------------------------
def make_basic_level(width_tiles=70, height_tiles=18, seed=0):
    random.seed(seed)
    rows = []
    for y in range(height_tiles):
        line = []
        for x in range(width_tiles):
            ch = " "
            if y >= height_tiles-2:
                ch = "X" # ground
            line.append(ch)
        rows.append(line)
    # Scatter low & mid platforms
    for _ in range(28):
        px = random.randint(4, width_tiles-8)
        py = random.randint(5, height_tiles-7)
        ln = random.randint(3, 8)
        for i in range(ln):
            rows[py][clamp(px+i, 0, width_tiles-1)] = "X"
    # Walkers
    for _ in range(8):
        x = random.randint(10, width_tiles-10)
        y = height_tiles-3
        rows[y][x] = "b"
    # Hazards on ground
    for _ in range(10):
        x = random.randint(8, width_tiles-8)
        rows[height_tiles-2][x] = "^"
    # start + goal
    rows[height_tiles-4][2] = "P"
    rows[height_tiles-3][width_tiles-3] = "G"
    return ["".join(r) for r in rows]
def make_boss_level(width_tiles=52, height_tiles=18):
    rows = []
    for y in range(height_tiles):
        line = []
        for x in range(width_tiles):
            ch = " "
            if y >= height_tiles-2: ch = "X"
            line.append(ch)
        rows.append(line)
    # Platforms and a 'B' line to mark the arena center
    midy = height_tiles//2
    for x in range(8, width_tiles-8):
        rows[midy][x] = "B"
    for x in range(10, width_tiles-10, 6):
        for dx in range(3):
            rows[midy-3][x+dx] = "X"
    # spawn and a few hazards
    rows[height_tiles-4][4] = "P"
    for x in range(12, width_tiles-12, 10):
        rows[height_tiles-2][x] = "^"
    return ["".join(r) for r in rows]
# -----------------------------------------------------------------------------
# GAME
# -----------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SMB3-Style Engine (Single File) - No Assets")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18, bold=True)
        self.big = pygame.font.SysFont("arial", 40, bold=True)
        self.state = STATE_TITLE
        self.world_index = 0
        self.stage_index = 0
        # Worlds: 5 worlds, 3 stages each (2 normal + 1 boss)
        self.world_stage_counts = [3,3,3,3,3]
        self.overworld = OverworldMap(self.world_stage_counts)
        self.progress_clears = [[False]*c for c in self.world_stage_counts]
        self.total_stages = sum(self.world_stage_counts)
        # Runtime
        self.level: Optional[Level] = None
        self.player: Optional[Player] = None
        self.enemies: List[Walker] = []
        self.boss: Optional[BoomStyleBoss] = None
        self.projectiles: List[Projectile] = []
        self.camera_x = 0
        # Title screen animation
        self.title_curtain_pos = 0 # For curtain opening animation
        # Cache levels
        self.level_cache = {}
    # ------------------------------ Scenes ----------------------------------
    def run(self):
        while True:
            if self.state == STATE_TITLE:
                self.loop_title()
            elif self.state == STATE_OVERWORLD:
                self.loop_overworld()
            elif self.state == STATE_LEVEL:
                self.loop_level(is_boss=False)
            elif self.state == STATE_BOSS:
                self.loop_level(is_boss=True)
            elif self.state == STATE_ENDING:
                self.loop_ending()
            else:
                pygame.quit()
                sys.exit(0)
    # ------------------------------ Title -----------------------------------
    def loop_title(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    self.state = STATE_OVERWORLD
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
        # Curtain opening animation
        if self.title_curtain_pos < WIDTH // 2:
            self.title_curtain_pos = min(self.title_curtain_pos + 10, WIDTH // 2) # Open speed
        # Draw SMB3-style title screen
        self.screen.fill(BEIGE) # Beige background like SMB3 title
        # Checkered floor at bottom
        tile_size = 32
        floor_height = tile_size * 2
        for x in range(0, WIDTH, tile_size):
            for y in range(HEIGHT - floor_height, HEIGHT, tile_size):
                color = BLACK if ((x // tile_size) + ((y - (HEIGHT - floor_height)) // tile_size)) % 2 == 0 else WHITE
                pygame.draw.rect(self.screen, color, (x, y, tile_size, tile_size))
        # Title text
        text(self.screen, self.big, "Samsoft Ultra Simulator — SMB3-Style Engine", (WIDTH//2, HEIGHT//2-60), BLACK, center=True)
        text(self.screen, self.font, "Node-map overworld • 5 Worlds × 3 Stages • Boom-style Boss each world", (WIDTH//2, HEIGHT//2-18), BLACK, center=True)
        text(self.screen, self.font, "Press Enter to start • Esc to quit", (WIDTH//2, HEIGHT//2+26), BLACK, center=True)
        # Draw parting curtains (procedural, inspired by SMB3 red curtains with scallops)
        curtain_width = WIDTH // 2 - self.title_curtain_pos
        if curtain_width > 0:
            # Left curtain
            pygame.draw.rect(self.screen, RED, (0, 0, curtain_width, HEIGHT))
            # Add scallop pattern
            for yy in range(0, HEIGHT, 20):
                pygame.draw.arc(self.screen, BLACK, (curtain_width-10, yy, 20, 20), math.pi, 2*math.pi, 2)
            # Right curtain
            pygame.draw.rect(self.screen, RED, (WIDTH - curtain_width, 0, curtain_width, HEIGHT))
            for yy in range(0, HEIGHT, 20):
                pygame.draw.arc(self.screen, BLACK, (WIDTH - curtain_width -10, yy, 20, 20), 0, math.pi, 2)
        pygame.display.flip()
        self.clock.tick(FPS)
    # ----------------------------- Overworld --------------------------------
    def loop_overworld(self):
        cleared = sum(1 for w in self.progress_clears for c in w if c)
        progress_txt = f"Progress: {cleared}/{self.total_stages} stages cleared"
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
                if ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    node = self.overworld.nodes[self.overworld.cursor]
                    if node.unlocked:
                        self.world_index = node.world
                        self.stage_index = node.index
                        last_stage = (self.stage_index == self.world_stage_counts[self.world_index]-1)
                        self.start_level(is_boss=last_stage)
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.overworld.move_cursor(-1, 0)
                if ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.overworld.move_cursor(1, 0)
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self.overworld.move_cursor(0, -1)
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.overworld.move_cursor(0, 1)
        self.overworld.draw(self.screen, self.font, progress_txt)
        for i in range(5):
            lbl = f"W{i+1}"
            x = 100 + i* (WIDTH-200)//4
            text(self.screen, self.font, lbl, (x, HEIGHT-150), BLACK, center=True)
        pygame.display.flip()
        self.clock.tick(FPS)
    # ------------------------------ Level -----------------------------------
    def start_level(self, is_boss=False):
        key = (self.world_index, self.stage_index, is_boss)
        if key not in self.level_cache:
            if is_boss:
                raw = make_boss_level()
            else:
                seed = self.world_index*101 + self.stage_index*13 + 7
                raw = make_basic_level(seed=seed)
            self.level_cache[key] = Level.from_raw(raw)
        self.level = self.level_cache[key]
        self.player = Player(*self.level.spawn)
        self.enemies = [Walker(e.rect.x, e.rect.y, dir=1) for e in self.level.enemies] # copy template enemies
        self.projectiles = []
        self.camera_x = 0
        self.boss = None
        if is_boss:
            diff = self.world_index # 0..4
            arena = self.level.arena_rect or pygame.Rect(200,120, WIDTH-400, HEIGHT-240)
            self.boss = BoomStyleBoss(arena, difficulty=diff)
            self.state = STATE_BOSS
        else:
            self.state = STATE_LEVEL
    def level_common_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit(0)
                if ev.key == pygame.K_r:
                    self.start_level(is_boss=(self.state==STATE_BOSS))
    def loop_level(self, is_boss=False):
        self.level_common_events()
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.level.solids, self.level.hazards, self.enemies, self.projectiles)
        # Enemies
        for e in self.enemies:
            e.update(self.level.solids)
        self.enemies = [e for e in self.enemies if e.alive or e.squash_timer > 0]
        # Boss + projectiles
        if self.boss:
            self.boss.update(self.player, self.level.solids, self.projectiles)
        for p in self.projectiles:
            p.update(self.level.solids)
        self.projectiles = [p for p in self.projectiles if p.alive]
        # Camera follow
        target_x = clamp(self.player.rect.centerx - WIDTH//2, 0, self.level.width - WIDTH)
        self.camera_x += (target_x - self.camera_x) * 0.1
        # Win conditions
        if self.state == STATE_LEVEL and self.level.goal and self.player.rect.colliderect(self.level.goal):
            self.on_level_clear()
            return
        if self.state == STATE_BOSS and self.boss and not self.boss.alive:
            self.on_level_clear()
            return
        # DRAW
        theme = self.world_index % 2
        self.level.draw_bg(self.screen, self.camera_x, theme=theme)
        self.level.draw_tiles(self.screen, self.camera_x)
        # projectiles
        for p in self.projectiles:
            p.draw(self.screen, self.camera_x)
        # enemies
        for e in self.enemies:
            e.draw(self.screen, self.camera_x)
        # boss
        if self.boss:
            self.boss.draw(self.screen, self.camera_x)
        # player + HUD
        self.player.draw(self.screen, self.camera_x)
        self.draw_hud()
        pygame.display.flip()
        self.clock.tick(FPS)
    def on_level_clear(self):
        # mark progress, unlock next
        self.progress_clears[self.world_index][self.stage_index] = True
        self.overworld.unlock_path_after_clear(self.world_index, self.stage_index)
        # if final world/stage cleared:
        if self.world_index == 4 and self.stage_index == self.world_stage_counts[4]-1:
            self.state = STATE_ENDING
        else:
            self.state = STATE_OVERWORLD
    # ----------------------------- Ending -----------------------------------
    def loop_ending(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit(0)
        self.screen.fill((245, 245, 255))
        text(self.screen, self.big, "Thank you for playing!", (WIDTH//2, HEIGHT//2-40), BLACK, center=True)
        text(self.screen, self.font, "All 5 worlds cleared. Bosses defeated.", (WIDTH//2, HEIGHT//2+5), BLACK, center=True)
        text(self.screen, self.font, "Press Enter or Esc to quit.", (WIDTH//2, HEIGHT//2+34), BLACK, center=True)
        pygame.display.flip()
        self.clock.tick(FPS)
    # ----------------------------- HUD --------------------------------------
    def draw_hud(self):
        # hearts
        for i in range(self.player.max_hearts):
            cx, cy = 16 + i*22, 16
            pygame.draw.circle(self.screen, BLACK, (cx, cy), 9)
            color = RED if i < self.player.hearts else GRAY
            pygame.draw.circle(self.screen, color, (cx, cy), 7)
        # world/stage label
        lbl = f"W{self.world_index+1}-{self.stage_index+1}"
        text(self.screen, self.font, lbl, (WIDTH-90, 14), BLACK)
        # P-meter
        px, py = WIDTH//2 - 60, 14
        w, h = 120, 12
        pygame.draw.rect(self.screen, BLACK, (px-2, py-2, w+4, h+4), border_radius=4)
        pct = clamp(self.player.pmeter/PMETER_MAX, 0, 1)
        pygame.draw.rect(self.screen, ORANGE, (px, py, int(w*pct), h), border_radius=3)
# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    try:
        Game().run()
    except KeyboardInterrupt:
        pygame.quit()
if __name__ == "__main__":
    main()