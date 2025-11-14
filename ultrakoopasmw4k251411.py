import pygame
import sys
import math
import random
from pygame.locals import *

# Constants
SCALE = 2
TILE = 16
WIDTH = int(300 * SCALE)
HEIGHT = int(200 * SCALE)
FPS = 60

# NES Palette
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136), 
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0), 
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0), 
    (0, 50, 60), (0, 0, 0), (152, 150, 152), (8, 76, 196), 
    (48, 50, 236), (92, 30, 228), (136, 20, 176), (160, 20, 100), 
    (152, 34, 32), (120, 60, 0), (84, 90, 0), (40, 114, 0), 
    (8, 124, 0), (0, 118, 40), (0, 102, 120), (0, 0, 0), 
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236), 
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32), 
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108), 
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0)
]

# Palette helper
def palette_nearest(color):
    return color  # We'll use direct palette colors

N = palette_nearest

# Game State
class GameState:
    def __init__(self):
        self.slot = 0
        self.progress = [{"max_level": 1}, {"max_level": 1}, {"max_level": 1}]
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.current_level_id = 1  # Current selected level on map
        self.max_level_unlocked = 1  # Max level player has reached
        self.time = 300
        self.mario_size = "small"  # "small" or "big"

state = GameState()

# Scene management
SCENES = []

def push(scene): SCENES.append(scene)
def pop(): SCENES.pop()

class Scene:
    def handle(self, events, keys): ...
    def update(self, dt): ...
    def draw(self, surf): ...

# World themes
THEMES = {
    "grass": {"sky": 27, "ground": 20, "pipe": 14, "block": 33, "water": None, "enemy": "G", "name": "GRASS LAND"},
    "desert": {"sky": 26, "ground": 21, "pipe": 15, "block": 34, "water": None, "enemy": "K", "name": "DESERT HILL"},
    "water": {"sky": 25, "ground": 22, "pipe": 16, "block": 35, "water": 45, "enemy": "F", "name": "AQUA SEA"},
    "sky": {"sky": 23, "ground": 24, "pipe": 18, "block": 37, "water": None, "enemy": "K", "name": "SKY HEIGHTS"},
    "ice": {"sky": 22, "ground": 25, "pipe": 19, "block": 38, "water": None, "enemy": "K", "name": "ICE CAVERN"},
    "castle": {"sky": 21, "ground": 26, "pipe": 20, "block": 39, "water": None, "enemy": "S", "name": "LAVA CASTLE"},
    "final": {"sky": 20, "ground": 27, "pipe": 21, "block": 40, "water": None, "enemy": "S", "name": "FINAL FORTRESS"}
}

# SMW-style level definitions (8 Worlds)
LEVEL_DEFINITIONS = [
    # World 1: Grass Land
    {"id": 1, "name": "1-1", "map_pos": (60, 150), "theme": "grass", "next": [2]},
    # World 2: Donut Plains
    {"id": 2, "name": "2-1", "map_pos": (100, 150), "theme": "grass", "next": [3]},
    # World 3: Vanilla Dome
    {"id": 3, "name": "3-1", "map_pos": (140, 150), "theme": "ice", "next": [4]},
    # World 4: Twin Bridges
    {"id": 4, "name": "4-1", "map_pos": (180, 150), "theme": "desert", "next": [5]},
    # World 5: Forest of Illusion
    {"id": 5, "name": "5-1", "map_pos": (220, 150), "theme": "water", "next": [6]}, # Using water theme for forest
    # World 6: Chocolate Island
    {"id": 6, "name": "6-1", "map_pos": (260, 150), "theme": "desert", "next": [7]}, # Using desert theme for chocolate
    # World 7: Valley of Bowser
    {"id": 7, "name": "7-1", "map_pos": (300, 150), "theme": "castle", "next": [8]},
    # World 8: Final Level
    {"id": 8, "name": "FINAL", "map_pos": (340, 150), "theme": "final", "next": []}, # Final level
]

# Generate a single level's data
def generate_level(level_number, theme_key):
    random.seed(level_number)  # Make level deterministic
    theme = THEMES[theme_key]
    
    level_data = []
    
    # Sky
    for i in range(10):
        level_data.append(" " * 100)
        
    # Platforms
    for i in range(10, 15):
        level_data.append(" " * 100)
        
    # Ground
    for i in range(15, 20):
        if i == 15:
            row = "G" * 100
        else:
            row = "B" * 100
        level_data.append(row)
    
    # Add platforms
    for i in range(5 + (level_number // 2)):  # More platforms in later levels
        platform_y = random.randint(8, 12)
        platform_x = random.randint(10 + i*15, 15 + i*15)
        length = random.randint(4, 8)
        for j in range(length):
            if platform_x+j < 100:
                level_data[platform_y] = level_data[platform_y][:platform_x+j] + "P" + level_data[platform_y][platform_x+j+1:]
    
    # Add pipes
    for i in range(2 + level_number // 4):  # More pipes in later levels
        pipe_x = random.randint(20 + i*30, 25 + i*30)
        pipe_height = random.randint(2, 4)
        for j in range(pipe_height):
            if pipe_x+1 < 100:
                level_data[19-j] = level_data[19-j][:pipe_x] + "T" + level_data[19-j][pipe_x+1:]
                level_data[19-j] = level_data[19-j][:pipe_x+1] + "T" + level_data[19-j][pipe_x+2:]
    
    # Add bricks and question blocks
    for i in range(8 + level_number):  # More blocks in later levels
        block_y = random.randint(5, 10)
        block_x = random.randint(5 + i*10, 8 + i*10)
        block_type = "?" if random.random() > 0.5 else "B"
        if block_x < 100:
            level_data[block_y] = level_data[block_y][:block_x] + block_type + level_data[block_y][block_x+1:]
    
    # Add player start
    level_data[14] = level_data[14][:5] + "S" + level_data[14][6:]
    
    # Add flag at end
    level_data[14] = level_data[14][:95] + "F" + level_data[14][96:]
    
    # Add enemies
    for i in range(5 + level_number):  # More enemies in later levels
        enemy_y = 14
        enemy_x = random.randint(20 + i*10, 25 + i*10)
        enemy_type = theme["enemy"]
        if enemy_x < 100:
            level_data[enemy_y] = level_data[enemy_y][:enemy_x] + enemy_type + level_data[enemy_y][enemy_x+1:]
    
    return level_data

# Generate all levels
def generate_all_levels():
    levels = {}
    for level_def in LEVEL_DEFINITIONS:
        level_id = level_def["id"]
        theme_key = level_def["theme"]
        levels[level_id] = generate_level(level_id, theme_key)
    return levels

LEVELS = generate_all_levels()

# Create thumbnails
THUMBNAILS = {}
for level_def in LEVEL_DEFINITIONS:
    level_id = level_def["id"]
    level_data = LEVELS[level_id]
    theme = THEMES[level_def["theme"]]
    
    thumb = pygame.Surface((32, 24))
    thumb.fill(NES_PALETTE[theme["sky"]])  # Sky color
    
    # Draw a simple representation of the level
    for y, row in enumerate(level_data[10:14]):
        for x, char in enumerate(row[::3]):  # Sample every 3rd column
            if char in ("G", "B", "P", "T"):
                thumb.set_at((x, y+10), NES_PALETTE[theme["ground"]])  # Ground color
            elif char in ("?", "B"):
                thumb.set_at((x, y+10), NES_PALETTE[theme["block"]])  # Block color
    
    THUMBNAILS[level_id] = thumb

# Entity classes
class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = TILE
        self.height = TILE
        self.on_ground = False
        self.facing_right = True
        self.active = True
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def check_collision(self, other):
        return self.get_rect().colliderect(other.get_rect())
        
    def update(self, colliders, dt):
        # Apply gravity
        if not self.on_ground:
            self.vy += 0.5 * dt * 60
            
        # Update position
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        
        # Check collision with ground
        self.on_ground = False
        self.vx_collided = False
        self.vy_collided = False
        
        # Sort colliders by proximity to optimize
        colliders.sort(key=lambda rect: abs(rect.centerx - self.x) + abs(rect.centery - self.y))
        
        for rect in colliders[:10]: # Only check 10 nearest colliders
            if self.get_rect().colliderect(rect):
                # Bottom collision
                if self.vy > 0 and self.get_rect().bottom > rect.top and self.get_rect().top < rect.top:
                    self.y = rect.top - self.height
                    self.vy = 0
                    self.on_ground = True
                    self.vy_collided = True
                # Top collision
                elif self.vy < 0 and self.get_rect().top < rect.bottom and self.get_rect().bottom > rect.bottom:
                    self.y = rect.bottom
                    self.vy = 0
                    self.vy_collided = True
                
                # Re-check rect after vertical correction
                if self.get_rect().colliderect(rect):
                    # Left collision
                    if self.vx > 0 and self.get_rect().right > rect.left and self.get_rect().left < rect.left:
                        self.x = rect.left - self.width
                        self.vx = 0
                        self.vx_collided = True
                    # Right collision
                    elif self.vx < 0 and self.get_rect().left < rect.right and self.get_rect().right > rect.right:
                        self.x = rect.right
                        self.vx = 0
                        self.vx_collided = True
                        
    def draw(self, surf, cam):
        pass

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.jump_power = -5
        self.move_speed = 2
        self.invincible = 0
        self.animation_frame = 0
        self.walk_timer = 0
        
    def update(self, colliders, dt, enemies):
        # Handle input
        keys = pygame.key.get_pressed()
        
        # Horizontal movement
        self.vx = 0
        if keys[K_LEFT]:
            self.vx = -self.move_speed
            self.facing_right = False
        if keys[K_RIGHT]:
            self.vx = self.move_speed
            self.facing_right = True
            
        # Jumping
        if keys[K_SPACE] and self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False
            
        # Update walk animation
        if self.vx != 0:
            self.walk_timer += dt
            if self.walk_timer > 0.1:
                self.walk_timer = 0
                self.animation_frame = (self.animation_frame + 1) % 3
        else:
            self.animation_frame = 0
            
        # Update invincibility
        if self.invincible > 0:
            self.invincible -= dt
            
        super().update(colliders, dt)
        
        # Check collision with enemies
        for enemy in enemies:
            if enemy.active and self.check_collision(enemy):
                # Jumped on enemy
                if self.vy > 0 and self.y + self.height - 5 < enemy.y:
                    enemy.active = False
                    self.vy = self.jump_power / 2
                    state.score += 100
                # Hit by enemy
                elif self.invincible <= 0:
                    if state.mario_size == "big":
                        state.mario_size = "small"
                        self.invincible = 2
                    else:
                        state.lives -= 1
                        if state.lives <= 0:
                            # Game over
                            push(GameOverScene())
                        else:
                            # Reset position
                            self.x = 50
                            self.y = 100
                            self.vx = 0
                            self.vy = 0
                    
    def draw(self, surf, cam):
        if self.invincible > 0 and int(self.invincible * 10) % 2 == 0:
            return  # Blink during invincibility
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Draw Mario based on size
        if state.mario_size == "big":
            # Body
            pygame.draw.rect(surf, NES_PALETTE[33], (x+4, y+8, 8, 16))  # Red overalls
            
            # Head
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y+4, 8, 4))  # Face
            
            # Hat
            pygame.draw.rect(surf, NES_PALETTE[33], (x+2, y, 12, 4))  # Red hat
            
            # Arms
            arm_offset = 0
            if self.animation_frame == 1 and self.vx != 0:
                arm_offset = 2 if self.facing_right else -2
                
            pygame.draw.rect(surf, NES_PALETTE[39], (x+arm_offset, y+10, 4, 6))  # Left arm
            pygame.draw.rect(surf, NES_PALETTE[39], (x+12-arm_offset, y+10, 4, 6))  # Right arm
            
            # Legs
            leg_offset = 0
            if self.animation_frame == 2 and self.vx != 0:
                leg_offset = 2 if self.facing_right else -2
                
            pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+24, 4, 8))  # Left leg
            pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+24-leg_offset, 4, 8+leg_offset))  # Right leg
        else:
            # Small Mario
            # Body
            pygame.draw.rect(surf, NES_PALETTE[33], (x+4, y+8, 8, 8))  # Red overalls
            
            # Head
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y, 8, 8))  # Face
            
            # Hat
            pygame.draw.rect(surf, NES_PALETTE[33], (x+2, y, 12, 2))  # Red hat

class Goomba(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.walk_timer = 0
        
    def update(self, colliders, dt):
        # Turn around at edges or walls
        if self.on_ground:
            # Check for edge
            edge_check = pygame.Rect(self.x + (self.width if self.vx > 0 else -1), 
                                     self.y + self.height, 
                                     1, 1)
            edge_found = False
            for rect in colliders[:10]:
                if edge_check.colliderect(rect):
                    edge_found = True
                    break
                    
            if not edge_found or self.vx_collided:
                self.vx *= -1
                
        super().update(colliders, dt)
        
        # Update animation
        self.walk_timer += dt
        if self.walk_timer > 0.2:
            self.walk_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
            
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[21], (x+2, y+4, 12, 12))  # Brown body
        
        # Feet
        foot_offset = 2 if self.animation_frame == 0 else -2
        pygame.draw.rect(surf, NES_PALETTE[21], (x+2, y+14, 4, 2))  # Left foot
        pygame.draw.rect(surf, NES_PALETTE[21], (x+10, y+14+foot_offset, 4, 2))  # Right foot
        
        # Eyes
        eye_dir = 0 if self.vx > 0 else 2
        pygame.draw.rect(surf, NES_PALETTE[0], (x+4+eye_dir, y+6, 2, 2))  # Left eye
        pygame.draw.rect(surf, NES_PALETTE[0], (x+10-eye_dir, y+6, 2, 2))  # Right eye

class Koopa(Goomba):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.shell_mode = False
        
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Shell
        pygame.draw.ellipse(surf, NES_PALETTE[14], (x+2, y+4, 12, 12))  # Green shell
        
        # Head and feet
        if not self.shell_mode:
            pygame.draw.rect(surf, NES_PALETTE[39], (x+4, y, 8, 4))  # Head
            pygame.draw.rect(surf, NES_PALETTE[14], (x+2, y+14, 4, 2))  # Left foot
            pygame.draw.rect(surf, NES_PALETTE[14], (x+10, y+14, 4, 2))  # Right foot

class Fish(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = -0.5
        self.animation_frame = 0
        self.swim_timer = 0
        self.in_water = True
        
    def update(self, colliders, dt):
        # Move in sine wave pattern
        self.swim_timer += dt
        self.y += math.sin(self.swim_timer * 5) * 0.5
        
        # No gravity in water
        self.x += self.vx * dt * 60
        
        # Turn around
        if self.vx_collided:
            self.vx *= -1
            
    def draw(self, surf, cam):
        if not self.active:
            return
            
        x = int(self.x - cam)
        y = int(self.y)
        
        # Body
        pygame.draw.ellipse(surf, NES_PALETTE[31], (x, y, 16, 8))  # Blue fish
        
        # Tail
        pygame.draw.polygon(surf, NES_PALETTE[31], [(x, y+4), (x-5, y), (x-5, y+8)])
        
        # Eye
        pygame.draw.circle(surf, NES_PALETTE[0], (x+12, y+4), 2)

class Spike(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.width = TILE
        self.height = TILE
        
    def draw(self, surf, cam):
        x = int(self.x - cam)
        y = int(self.y)
        
        # Spike base
        pygame.draw.rect(surf, NES_PALETTE[33], (x, y, TILE, TILE))
        
        # Spike
        pygame.draw.polygon(surf, NES_PALETTE[39], [
            (x + TILE//2, y),
            (x, y + TILE),
            (x + TILE, y + TILE)
        ])

class TileMap:
    def __init__(self, level_data, theme):
        self.tiles = []
        self.colliders = []
        self.width = len(level_data[0]) * TILE
        self.height = len(level_data) * TILE
        self.theme = theme
        
        # Parse level data
        for y, row in enumerate(level_data):
            for x, char in enumerate(row):
                if char != " ":
                    rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                    self.tiles.append((x * TILE, y * TILE, char))
                    
                    if char in ("G", "B", "P", "T", "?"):
                        self.colliders.append(rect)
    
    def draw(self, surf, cam):
        # Draw sky
        surf.fill(NES_PALETTE[self.theme["sky"]])
        
        # Draw clouds
        for i in range(10):
            x = (i * 80 + int(cam/3)) % (self.width + 200) - 100
            y = 30 + (i % 3) * 20
            pygame.draw.ellipse(surf, NES_PALETTE[31], (x, y, 30, 15))
            pygame.draw.ellipse(surf, NES_PALETTE[31], (x+15, y-5, 25, 15))
        
        # Draw tiles
        for x, y, char in self.tiles:
            draw_x = int(x - cam)
            if draw_x < -TILE or draw_x > WIDTH:
                continue
                
            if char == "G":  # Green ground top
                pygame.draw.rect(surf, NES_PALETTE[self.theme["ground"]], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[self.theme["ground"]-1], (draw_x, y+8, TILE, TILE-8))
                pygame.draw.rect(surf, NES_PALETTE[self.theme["ground"]-2], (draw_x+4, y+4, TILE-8, 4))
            elif char == "B":  # Brown block
                pygame.draw.rect(surf, NES_PALETTE[self.theme["block"]], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[self.theme["block"]-1], (draw_x+2, y+2, TILE-4, TILE-4))
            elif char == "P":  # Platform
                pygame.draw.rect(surf, NES_PALETTE[self.theme["ground"]], (draw_x, y, TILE, TILE))
            elif char == "T":  # Pipe
                pygame.draw.rect(surf, NES_PALETTE[self.theme["pipe"]], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[self.theme["pipe"]-1], (draw_x+2, y+2, TILE-4, TILE-4))
            elif char == "?":  # Question block
                pygame.draw.rect(surf, NES_PALETTE[self.theme["block"]], (draw_x, y, TILE, TILE))
                pygame.draw.rect(surf, NES_PALETTE[39], (draw_x+4, y+4, 8, 4))
                pygame.draw.rect(surf, NES_PALETTE[39], (draw_x+4, y+8, 2, 2))
                pygame.draw.rect(surf, NES_PALETTE[39], (draw_x+10, y+8, 2, 2))
            elif char == "F":  # Flag
                pygame.draw.rect(surf, NES_PALETTE[31], (draw_x+6, y, 4, TILE*4))
                pygame.draw.rect(surf, NES_PALETTE[33], (draw_x, y, 10, 6))

# Scenes
class TitleScreen(Scene):
    def __init__(self):
        self.timer = 0
        self.animation_frame = 0
        self.logo_y = -50
        self.logo_target_y = HEIGHT // 2 - 60
        
    def handle(self, events, keys):
        for e in events:
            if e.type == KEYDOWN and e.key == K_RETURN:
                push(FileSelect())
                
    def update(self, dt):
        self.timer += dt
        if self.timer > 0.1:
            self.timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
            
        # Animate logo coming down
        if self.logo_y < self.logo_target_y:
            self.logo_y += 3
            
    def draw(self, surf):
        # Background
        surf.fill(NES_PALETTE[27])
        
        # Engine Box
        box_width, box_height = 240, 100
        box_x = (WIDTH - box_width) // 2
        box_y = self.logo_y
        
        # Draw box with border
        pygame.draw.rect(surf, NES_PALETTE[0], (box_x-4, box_y-4, box_width+8, box_height+8))
        pygame.draw.rect(surf, NES_PALETTE[33], (box_x, box_y, box_width, box_height))
        
        # Title inside box
        title_font = pygame.font.SysFont(None, 32)
        title = title_font.render("SMW ENGINE", True, NES_PALETTE[39])
        surf.blit(title, (box_x + (box_width - title.get_width()) // 2, box_y + 15))
        
        subtitle_font = pygame.font.SysFont(None, 16)
        subtitle = subtitle_font.render("SMB1-Style Edition", True, NES_PALETTE[21])
        surf.blit(subtitle, (box_x + (box_width - subtitle.get_width()) // 2, box_y + 50))
        
        # Copyright
        copyright_font = pygame.font.SysFont(None, 14)
        copyright = copyright_font.render("[C] User Request 20XX [1985] - Nintendo", True, NES_PALETTE[0])
        surf.blit(copyright, (WIDTH//2 - copyright.get_width()//2, box_y + box_height + 20))
        
        # Mario and enemies
        mario_x = WIDTH//2 - 100
        mario_y = box_y + box_height + 50
        pygame.draw.rect(surf, NES_PALETTE[33], (mario_x+4, mario_y+8, 8, 16))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x+4, mario_y+4, 8, 4))
        pygame.draw.rect(surf, NES_PALETTE[33], (mario_x+2, mario_y, 12, 4))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x, mario_y+10, 4, 6))
        pygame.draw.rect(surf, NES_PALETTE[39], (mario_x+16, mario_y+10, 4, 6))
        pygame.draw.rect(surf, NES_PALETTE[21], (mario_x+2, mario_y+24, 4, 8))
        pygame.draw.rect(surf, NES_PALETTE[21], (mario_x+10, mario_y+24, 4, 8))
        
        # Goomba
        goomba_x = WIDTH//2 + 30
        goomba_y = mario_y + 20
        pygame.draw.ellipse(surf, NES_PALETTE[21], (goomba_x+2, goomba_y+4, 12, 12))
        pygame.draw.rect(surf, NES_PALETTE[21], (goomba_x+2, goomba_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[21], (goomba_x+10, goomba_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (goomba_x+4, goomba_y+6, 2, 2))
        pygame.draw.rect(surf, NES_PALETTE[0], (goomba_x+10, goomba_y+6, 2, 2))
        
        # Koopa
        koopa_x = WIDTH//2 + 70
        koopa_y = mario_y + 20
        pygame.draw.ellipse(surf, NES_PALETTE[14], (koopa_x+2, koopa_y+4, 12, 12))
        pygame.draw.rect(surf, NES_PALETTE[39], (koopa_x+4, koopa_y, 8, 4))
        pygame.draw.rect(surf, NES_PALETTE[14], (koopa_x+2, koopa_y+14, 4, 2))
        pygame.draw.rect(surf, NES_PALETTE[14], (koopa_x+10, koopa_y+14, 4, 2))
        
        # Press Start
        if self.logo_y >= self.logo_target_y and int(self.timer * 10) % 2 == 0:
            font = pygame.font.SysFont(None, 24)
            text = font.render("PRESS ENTER", True, NES_PALETTE[39])
            surf.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 30))

class FileSelect(Scene):
    def __init__(self):
        self.offset = 0
        self.selected = 0
        
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                if e.key in (K_1, K_2, K_3):
                    self.selected = e.key - K_1
                elif e.key == K_RETURN:
                    state.slot = self.selected
                    # Load progress
                    state.max_level_unlocked = state.progress[state.slot]["max_level"]
                    state.current_level_id = state.max_level_unlocked  # Start at the farthest level
                    push(WorldMapScene())
                elif e.key == K_ESCAPE:
                    push(TitleScreen())
                    
    def update(self, dt):
        self.offset += dt
        
    def draw(self, s):
        s.fill(NES_PALETTE[27])
        
        # Title
        font = pygame.font.SysFont(None, 30)
        title = font.render("SELECT PLAYER", True, NES_PALETTE[33])
        s.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Draw file slots
        for i in range(3):
            x = 50 + i * 100
            y = 90 + 5 * math.sin(self.offset * 3 + i)
            
            # Slot background
            pygame.draw.rect(s, NES_PALETTE[21], (x-5, y-5, 50, 70))
            pygame.draw.rect(s, NES_PALETTE[33], (x, y, 40, 60))
            
            # Slot number
            slot_font = pygame.font.SysFont(None, 20)
            slot_text = slot_font.render(f"{i+1}", True, NES_PALETTE[39])
            s.blit(slot_text, (x+18, y+5))
            
            # Selection indicator
            if i == self.selected:
                pygame.draw.rect(s, NES_PALETTE[39], (x-2, y-2, 44, 64), 2)
                
            # Level progress
            if state.progress[i]:
                max_level = state.progress[i]["max_level"]
                level_font = pygame.font.SysFont(None, 16)
                level_text = level_font.render(f"LEVEL {max_level}", True, NES_PALETTE[39])
                s.blit(level_text, (x+20 - level_text.get_width()//2, y+50))
                
                # Draw thumbnail
                thumb = THUMBNAILS.get(max_level, THUMBNAILS[1])
                s.blit(thumb, (x+4, y+20))

class WorldMapScene(Scene):
    def __init__(self):
        self.selection = state.current_level_id  # Get from game state
        self.offset = 0
        self.cursor_timer = 0
        
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN:
                current_level_def = LEVEL_DEFINITIONS[self.selection - 1]
                
                if e.key == K_RIGHT or e.key == K_UP:
                    if current_level_def["next"]:
                        next_level_id = current_level_def["next"][0]  # Just take the first path
                        if next_level_id <= state.max_level_unlocked:
                            self.selection = next_level_id
                elif e.key == K_LEFT or e.key == K_DOWN:
                    # Need to find which level leads to this one
                    for lvl in LEVEL_DEFINITIONS:
                        if self.selection in lvl["next"]:
                            self.selection = lvl["id"]
                            break  # Found the previous level
                            
                elif e.key == K_RETURN:
                    if self.selection <= state.max_level_unlocked:
                        state.current_level_id = self.selection
                        level_def = LEVEL_DEFINITIONS[self.selection - 1]
                        push(LevelScene(level_def["id"], level_def["theme"]))
                elif e.key == K_ESCAPE:
                    pop() # Back to File Select
                    
    def update(self, dt):
        self.offset += dt
        self.cursor_timer += dt
        
    def draw(self, s):
        s.fill(NES_PALETTE[27])  # Green map background
        
        # Draw paths
        for level_def in LEVEL_DEFINITIONS:
            for next_id in level_def["next"]:
                next_level_def = LEVEL_DEFINITIONS[next_id - 1]
                pygame.draw.line(s, NES_PALETTE[39], 
                                 (level_def["map_pos"][0] + 10, level_def["map_pos"][1] + 10), 
                                 (next_level_def["map_pos"][0] + 10, next_level_def["map_pos"][1] + 10), 3)

        # Draw level nodes
        world_size = 20
        for level_def in LEVEL_DEFINITIONS:
            x, y = level_def["map_pos"]
            theme = THEMES[level_def["theme"]]
            
            # Draw world tile
            if level_def["id"] <= state.max_level_unlocked:
                pygame.draw.rect(s, NES_PALETTE[theme["ground"]], (x, y, world_size, world_size))
                pygame.draw.rect(s, NES_PALETTE[theme["block"]], (x+5, y+5, world_size-10, world_size-10))
            else:
                pygame.draw.rect(s, NES_PALETTE[0], (x, y, world_size, world_size))  # Locked
                pygame.draw.rect(s, NES_PALETTE[28], (x+5, y+5, world_size-10, world_size-10))
            
            # Draw level name
            world_font = pygame.font.SysFont(None, 16)
            world_text = world_font.render(level_def["name"], True, NES_PALETTE[39])
            s.blit(world_text, (x + world_size//2 - world_text.get_width()//2, y + world_size + 2))
            
            # Draw world name if selected
            if level_def["id"] == self.selection:
                name_font = pygame.font.SysFont(None, 14)
                name_text = name_font.render(THEMES[level_def["theme"]]["name"], True, NES_PALETTE[39])
                s.blit(name_text, (WIDTH//2 - name_text.get_width()//2, HEIGHT - 40))
                
        # Draw Mario at selected world
        selected_def = LEVEL_DEFINITIONS[self.selection - 1]
        x, y = selected_def["map_pos"]
        
        # Animated cursor
        cursor_offset = math.sin(self.cursor_timer * 5) * 3
        mario_x = x + world_size//2 - 8
        mario_y = y - 25 + cursor_offset
        pygame.draw.rect(s, NES_PALETTE[33], (mario_x+4, mario_y+8, 8, 8))
        pygame.draw.rect(s, NES_PALETTE[39], (mario_x+4, mario_y, 8, 8))
        
        # Draw instructions
        font = pygame.font.SysFont(None, 14)
        text = font.render("Arrow keys: Move  Enter: Select  Esc: Back", True, NES_PALETTE[39])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 20))

class LevelScene(Scene):
    def __init__(self, level_id, theme_key):
        self.level_id = level_id
        self.theme = THEMES[theme_key]
        self.map = TileMap(LEVELS[self.level_id], self.theme)
        self.player = Player(50, 100)
        self.enemies = []
        self.cam = 0.0
        self.time = 300
        self.coins = 0
        self.end_level = False
        self.end_timer = 0
        self.mushrooms = []
        
        # Parse level for enemies and player start
        for y, row in enumerate(LEVELS[self.level_id]):
            for x, char in enumerate(row):
                if char == "S":
                    self.player.x = x * TILE
                    self.player.y = y * TILE
                elif char == "G":
                    self.enemies.append(Goomba(x * TILE, y * TILE))
                elif char == "K":
                    self.enemies.append(Koopa(x * TILE, y * TILE))
                elif char == "F":
                    self.enemies.append(Fish(x * TILE, y * TILE))
                elif char == "S":
                    self.enemies.append(Spike(x * TILE, y * TILE))
    
    def handle(self, evts, keys):
        for e in evts:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pop() # Back to World Map
                
    def update(self, dt):
        # Update time
        self.time -= dt
        
        # Update player
        self.player.update(self.map.colliders, dt, self.enemies)
        
        # Update enemies
        for enemy in self.enemies:
            if enemy.active and abs(enemy.x - self.player.x) < WIDTH: # Only update nearby enemies
                enemy.update(self.map.colliders, dt)
        
        # Camera follow player
        target = self.player.x - WIDTH // 2
        self.cam += (target - self.cam) * 0.1
        self.cam = max(0, min(self.cam, self.map.width - WIDTH))
        
        # Check for end of level
        if self.player.x > self.map.width - 100 and not self.end_level:
            self.end_level = True
            self.end_timer = 3  # 3 seconds to show end sequence
            
        if self.end_level:
            self.end_timer -= dt
            if self.end_timer <= 0:
                current_level_def = LEVEL_DEFINITIONS[self.level_id - 1]
                
                # Check for win
                if not current_level_def["next"]:
                    push(WinScreen())
                    return

                # Unlock next level(s)
                for next_id in current_level_def["next"]:
                    if next_id > state.max_level_unlocked:
                        state.max_level_unlocked = next_id
                
                # Update progress in save slot
                state.progress[state.slot]["max_level"] = state.max_level_unlocked
                
                # Set map selection to next level
                state.current_level_id = current_level_def["next"][0] 
                
                pop()  # Back to map
    
    def draw(self, s):
        # Draw map
        self.map.draw(s, self.cam)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(s, self.cam)
            
        # Draw player
        self.player.draw(s, self.cam)
        
        # Draw HUD
        pygame.draw.rect(s, NES_PALETTE[0], (0, 0, WIDTH, 20))
        
        # Score
        font = pygame.font.SysFont(None, 16)
        score_text = font.render(f"SCORE {state.score:06d}", True, NES_PALETTE[39])
        s.blit(score_text, (10, 4))
        
        # Coins
        coin_text = font.render(f"COINS {state.coins:02d}", True, NES_PALETTE[39])
        s.blit(coin_text, (150, 4))
        
        # World
        world_text = font.render(f"LEVEL {LEVEL_DEFINITIONS[self.level_id-1]['name']}", True, NES_PALETTE[39])
        s.blit(world_text, (250, 4))
        
        # Time
        time_text = font.render(f"TIME {int(self.time):03d}", True, NES_PALETTE[39])
        s.blit(time_text, (350, 4))
        
        # Lives
        lives_text = font.render(f"x{state.lives}", True, NES_PALETTE[39])
        s.blit(lives_text, (WIDTH - 60, 4))
        # Draw small mario for lives indicator
        pygame.draw.rect(s, NES_PALETTE[33], (WIDTH - 80, 6, 8, 8))
        pygame.draw.rect(s, NES_PALETTE[39], (WIDTH - 80, 2, 8, 8))
        
        # Draw world theme name
        theme_text = font.render(self.theme["name"], True, NES_PALETTE[39])
        s.blit(theme_text, (WIDTH//2 - theme_text.get_width()//2, HEIGHT - 20))

class GameOverScene(Scene):
    def __init__(self):
        self.timer = 3
        
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            pop()  # Pop LevelScene
            pop()  # Pop WorldMapScene, back to file select
            state.lives = 3
            state.score = 0
            
    def draw(self, s):
        s.fill(NES_PALETTE[0])
        font = pygame.font.SysFont(None, 40)
        text = font.render("GAME OVER", True, NES_PALETTE[33])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 20))
        
        font = pygame.font.SysFont(None, 20)
        text = font.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[39])
        s.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 20))

class WinScreen(Scene):
    def __init__(self):
        self.timer = 5
        self.fireworks = []
        
    def update(self, dt):
        self.timer -= dt
        
        # Add fireworks
        if random.random() < 0.2:
            fw = {
                "x": random.randint(50, WIDTH-50),
                "y": HEIGHT,
                "vy": random.uniform(-8, -5),
                "size": random.randint(20, 40),
                "color": random.choice([NES_PALETTE[33], NES_PALETTE[39], NES_PALETTE[31]]),
                "particles": [],
                "exploded": False
            }
            self.fireworks.append(fw)
            
        # Update fireworks
        for fw in self.fireworks[:]:
            if not fw["exploded"]:
                fw["y"] += fw["vy"]
                fw["vy"] += 0.1 # gravity
                if fw["vy"] >= 0:
                    # Explode
                    fw["exploded"] = True
                    for i in range(20):
                        angle = random.uniform(0, math.pi*2)
                        speed = random.uniform(1, 4)
                        fw["particles"].append({
                            "x": fw["x"],
                            "y": fw["y"],
                            "vx": math.cos(angle) * speed,
                            "vy": math.sin(angle) * speed,
                            "life": 1.0
                        })
            else:
                # Update particles
                all_dead = True
                for p in fw["particles"][:]:
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    p["vy"] += 0.1
                    p["life"] -= 0.02
                    if p["life"] <= 0:
                        fw["particles"].remove(p)
                    else:
                        all_dead = False
                if all_dead:
                    self.fireworks.remove(fw)
                    
        if self.timer <= 0:
            while len(SCENES) > 1: # Pop all scenes until title screen
                pop()
            
    def draw(self, s):
        s.fill(NES_PALETTE[0])
        
        # Draw fireworks
        for fw in self.fireworks:
            if not fw["exploded"]:
                pygame.draw.circle(s, NES_PALETTE[39], (int(fw["x"]), int(fw["y"])), 3)
            else:
                for p in fw["particles"]:
                    color = fw["color"]
                    pygame.draw.circle(s, color, (int(p["x"]), int(p["y"])), 2)
        
        # Text
        font = pygame.font.SysFont(None, 40)
        text = font.render("CONGRATULATIONS!", True, NES_PALETTE[33])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 50))
        
        font = pygame.font.SysFont(None, 30)
        text = font.render("YOU SAVED THE PRINCESS!", True, NES_PALETTE[39])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 100))
        
        font = pygame.font.SysFont(None, 24)
        text = font.render(f"FINAL SCORE: {state.score}", True, NES_PALETTE[31])
        s.blit(text, (WIDTH//2 - text.get_width()//2, 150))

# Main game
pygame.init()
pygame.font.init() # Ensure font module is initialized
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SMW ENGINE - SMB1-Style Edition")
clock = pygame.time.Clock()

# Start with title screen
push(TitleScreen())

while SCENES:
    dt = clock.tick(FPS) / 1000.0
    # Cap delta time to avoid physics explosions
    if dt > 0.1:
        dt = 0.1
        
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    
    # Handle quit events
    for e in events:
        if e.type == QUIT:
            pygame.quit()
            sys.exit()
    
    # Update current scene
    scene = SCENES[-1]
    scene.handle(events, keys)
    scene.update(dt)
    scene.draw(screen)
    
    pygame.display.flip()

pygame.quit()
sys.exit()
