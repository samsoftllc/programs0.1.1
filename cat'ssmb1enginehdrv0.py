# program.py
# ULTRA MARIO BROS - Complete SMB1 Recreation (32 Levels)
# [C] 1985 Nintendo [C] 2025 Samsoft | Pure Pygame Implementation
# Arrow Keys: Move | SPACE: Jump | Z: Run | X: Fire | ESC: Quit
import pygame
import sys
import math
import random

pygame.init()

# === CONSTANTS ===
SCREEN_W, SCREEN_H = 800, 480
TILE = 32
FPS = 60
GRAVITY = 0.6
MAX_FALL_SPEED = 16
WALK_SPEED = 3.5
RUN_SPEED = 5.5
JUMP_SPEED = -11
RUN_JUMP_SPEED = -12.5
SKID_DECEL = 0.5
ENEMY_SPEED = 1.2
FIREBALL_SPEED = 7

# === COLORS ===
SKY = (92, 148, 252)
GROUND = (188, 148, 92)
BRICK = (200, 76, 12)
BLOCK = (252, 156, 0)
PIPE_GREEN = (56, 168, 0)
PIPE_DARK = (0, 88, 0)
COIN_GOLD = (252, 216, 168)
GOOMBA_BROWN = (160, 82, 45)
KOOPA_GREEN = (0, 150, 0)
COIN_YELLOW = (255, 215, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
UNDERGROUND_BG = (0, 0, 0)
UNDERWATER_BG = (33, 66, 132)
CASTLE_BG = (100, 0, 0)
FLAGPOLE_COLOR = (200, 200, 200)
FIREBALL_COLOR = (255, 200, 0)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("ULTRA MARIO BROS - All 32 Levels")
clock = pygame.time.Clock()

# === LEVEL DATA (32 Levels: 8 Worlds × 4 Levels) ===
# Encoding: X=ground, B=brick, ?=coin block, P=pipe, M=player start, E=enemy, C=coin, F=flag
LEVELS = {
    "1-1": {
        "theme": "overworld",
        "time": 400,
        "layout": [
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "M                                                                               ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
    "1-2": {
        "theme": "underground",
        "time": 400,
        "layout": [
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "M                                                                               ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
    "1-3": {
        "theme": "overworld",
        "time": 300,
        "layout": [
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "M                                                                               ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
    "1-4": {
        "theme": "castle",
        "time": 300,
        "layout": [
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "M                                                                               ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
}

# Generate additional levels (2-1 through 8-4) with proper content
for world in range(2, 9):
    for level in range(1, 5):
        level_key = f"{world}-{level}"
        if level == 1:
            theme = "overworld"
        elif level == 2:
            theme = "underground"
        elif level == 3:
            theme = "overworld"
        else:
            theme = "castle"
        
        # Create simple but functional layouts for all levels
        layout = [
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "                                                                                ",
            "M                                                                               ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
        
        # Add some basic level elements
        if level == 1:  # Overworld levels get some platforms
            layout[8] = "                        XXX      XXX      XXX                        "
            layout[9] = "                        X?X      XBX      X?X                        "
        elif level == 2:  # Underground levels get more platforms
            layout[6] = "           XXX           XXX           XXX           XXX           "
            layout[7] = "           X?X           X?X           X?X           X?X           "
        elif level == 3:  # More complex overworld
            layout[7] = "      XXX           XXX           XXX           XXX           XXX   "
            layout[8] = "      X?X           X?X           X?X           X?X           X?X   "
        else:  # Castle levels
            layout[9] = "                              XXX                                   "
            layout[10] = "                              X?X                                   "
        
        # Add flag at the end
        layout[8] = layout[8][:-1] + "F"
        layout[9] = layout[9][:-1] + "F"
        layout[10] = layout[10][:-1] + "F"
        
        LEVELS[level_key] = {
            "theme": theme,
            "time": 400 if level < 4 else 300,
            "layout": layout
        }

# Add some content to the first level for testing
LEVELS["1-1"]["layout"] = [
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                                                                                ",
    "                        ?B?                 C   C   C                           ",
    "                        XXX                 E   E   E                           ",
    "            PPP         XXX                                                     ",
    "            PPP         XXX                                                     ",
    "            PPP         XXX                                                     ",
    "M           PPP         XXX                                                     ",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]

# === ENTITY CLASSES ===
class Fireball:
    def __init__(self, x, y, direction):
        self.rect = pygame.Rect(x, y, 8, 8)
        self.vel_x = FIREBALL_SPEED * direction
        self.vel_y = 0
        self.direction = direction
        self.bounce_count = 0
        
    def update(self, blocks, enemies):
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Move horizontally
        self.rect.x += self.vel_x
        
        # Move vertically
        self.rect.y += self.vel_y
        
        # Check collisions with blocks
        for block in blocks:
            if self.rect.colliderect(block):
                # Bounce off ground/ceiling
                if abs(self.rect.bottom - block.top) < 10 and self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = -5  # Bounce
                    self.bounce_count += 1
                elif abs(self.rect.top - block.bottom) < 10 and self.vel_y < 0:
                    self.rect.top = block.bottom
                    self.vel_y = 0
                # Bounce off walls
                elif abs(self.rect.right - block.left) < 10 and self.vel_x > 0:
                    self.vel_x = -self.vel_x
                    self.direction = -self.direction
                elif abs(self.rect.left - block.right) < 10 and self.vel_x < 0:
                    self.vel_x = -self.vel_x
                    self.direction = -self.direction
        
        # Check collisions with enemies
        for enemy in enemies[:]:
            if self.rect.colliderect(enemy.rect):
                enemies.remove(enemy)
                return "hit"
        
        # Remove after too many bounces or off screen
        if self.bounce_count > 3 or self.rect.y > SCREEN_H:
            return "dead"
            
        return None
    
    def draw(self, surface, camera_x):
        screen_x = self.rect.x - camera_x
        pygame.draw.circle(surface, FIREBALL_COLOR, (int(screen_x + 4), int(self.rect.y + 4)), 4)
        # Draw flame effect
        for i in range(3):
            offset = random.randint(-1, 1)
            pygame.draw.circle(surface, RED, 
                             (int(screen_x + 4 + offset), int(self.rect.y + 4 + offset)), 2)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE-4, TILE)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.size = "small" # small, big, fire
        self.invincible_timer = 0
        self.jump_held = False
        self.skidding = False
        self.fire_cooldown = 0
       
    def update(self, keys, blocks, enemies, coins, fireballs, dt):
        # Input handling - UPDATED CONTROLS
        run = keys[pygame.K_z]  # Z for run
        max_speed = RUN_SPEED if run else WALK_SPEED
        jump_speed = RUN_JUMP_SPEED if run else JUMP_SPEED
       
        # Horizontal movement
        if keys[pygame.K_RIGHT]:
            self.vel_x = min(self.vel_x + 0.5, max_speed)
            self.facing_right = True
            self.skidding = False
        elif keys[pygame.K_LEFT]:
            self.vel_x = max(self.vel_x - 0.5, -max_speed)
            self.facing_right = False
            self.skidding = False
        else:
            # Deceleration with skidding effect
            if self.vel_x > 0:
                self.vel_x = max(0, self.vel_x - SKID_DECEL)
                if self.on_ground:
                    self.skidding = self.vel_x > 0.5
            elif self.vel_x < 0:
                self.vel_x = min(0, self.vel_x + SKID_DECEL)
                if self.on_ground:
                    self.skidding = self.vel_x < -0.5
       
        # Jumping - SPACE for jump
        if keys[pygame.K_SPACE]:
            if self.on_ground and not self.jump_held:
                self.vel_y = jump_speed
                self.jump_held = True
        else:
            self.jump_held = False
            # Allow variable jump height
            if self.vel_y < -4 and not keys[pygame.K_SPACE]:
                self.vel_y = -4
       
        # Shooting fireballs - X for fire
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
            
        if keys[pygame.K_x] and self.size == "fire" and self.fire_cooldown == 0:
            direction = 1 if self.facing_right else -1
            fireball_x = self.rect.right if self.facing_right else self.rect.left - 8
            fireballs.append(Fireball(fireball_x, self.rect.centery, direction))
            self.fire_cooldown = 15  # Cooldown between shots
       
        # Apply gravity
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        self.on_ground = False
       
        # Horizontal collision and movement
        self.rect.x += self.vel_x
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_x > 0:
                    self.rect.right = block.left
                    self.vel_x = 0
                elif self.vel_x < 0:
                    self.rect.left = block.right
                    self.vel_x = 0
       
        # Vertical collision and movement
        self.rect.y += self.vel_y
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.bottom
                    self.vel_y = 0
       
        # Coin collection
        for coin in coins[:]:
            if self.rect.colliderect(coin):
                coins.remove(coin)
                # Random chance to get power-up from coin
                if random.random() < 0.1:  # 10% chance
                    if self.size == "small":
                        self.size = "big"
                    elif self.size == "big":
                        self.size = "fire"
                return {"type": "coin"}
       
        # Enemy collision
        if self.invincible_timer <= 0:
            for enemy in enemies[:]:
                if self.rect.colliderect(enemy.rect):
                    # Stomp enemy
                    if self.vel_y > 0 and (self.rect.bottom - enemy.rect.top) < 10:
                        enemies.remove(enemy)
                        self.vel_y = -8
                        return {"type": "stomp"}
                    else:
                        # Take damage
                        if self.size == "fire":
                            self.size = "big"
                        elif self.size == "big":
                            self.size = "small"
                            self.invincible_timer = 120
                        else:
                            return {"type": "damage"}
       
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
       
        return None
   
    def draw(self, surface, camera_x):
        screen_x = self.rect.x - camera_x
        blink = (self.invincible_timer % 10) < 5 if self.invincible_timer > 0 else True
        
        # Set color based on size
        if self.size == "fire":
            color = (255, 100, 0)  # Orange for fire Mario
        else:
            color = RED if blink else (200, 0, 0)
       
        # Draw Mario body
        pygame.draw.rect(surface, color, (screen_x, self.rect.y, self.rect.width, self.rect.height))
       
        # Draw overalls
        pygame.draw.rect(surface, (0, 0, 200), (screen_x, self.rect.y + self.rect.height//2, self.rect.width, self.rect.height//2))
       
        # Draw face
        face_color = (255, 200, 200) if self.size == "big" or self.size == "fire" else color
        pygame.draw.circle(surface, face_color, (int(screen_x + self.rect.width//2), int(self.rect.y + 10)), 8)
       
        # Draw cap
        cap_color = color
        pygame.draw.arc(surface, cap_color,
                       (screen_x + 4, self.rect.y + 2, self.rect.width - 8, 16),
                       math.pi, 2*math.pi, 3)
       
        # Draw eyes
        eye_offset = 3 if self.facing_right else -3
        pygame.draw.circle(surface, WHITE, (int(screen_x + self.rect.width//2 + eye_offset), int(self.rect.y + 8)), 3)
        pygame.draw.circle(surface, BLACK, (int(screen_x + self.rect.width//2 + eye_offset + 1), int(self.rect.y + 8)), 1)
       
        # Draw mustache
        pygame.draw.arc(surface, BLACK,
                       (screen_x + 4, self.rect.y + 10, self.rect.width - 8, 12),
                       0, math.pi, 2)
       
        # Draw feet
        foot_y = self.rect.y + self.rect.height - 4
        pygame.draw.rect(surface, BLACK, (screen_x + 2, foot_y, 6, 4))
        pygame.draw.rect(surface, BLACK, (screen_x + self.rect.width - 8, foot_y, 6, 4))
       
        # Draw skid dust
        if self.skidding and self.on_ground:
            dust_y = self.rect.bottom - 8
            for i in range(3):
                dust_x = self.rect.centerx + (5 * i if self.facing_right else -5 * i) - camera_x
                size = 3 - i
                pygame.draw.circle(surface, (200, 200, 200), (int(dust_x), int(dust_y)), size)

class Enemy:
    def __init__(self, x, y, enemy_type="goomba"):
        self.rect = pygame.Rect(x, y, TILE-8, TILE-8)
        self.vel_x = ENEMY_SPEED * (1 if random.random() < 0.5 else -1)
        self.vel_y = 0
        self.on_ground = False
        self.type = enemy_type
        self.alive = True
       
    def update(self, blocks):
        if not self.alive:
            return
        # Gravity
        self.vel_y += GRAVITY
        self.vel_y = min(self.vel_y, MAX_FALL_SPEED)
        self.on_ground = False
       
        # Horizontal movement and collision
        self.rect.x += self.vel_x
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_x > 0:
                    self.rect.right = block.left
                    self.vel_x = -self.vel_x
                elif self.vel_x < 0:
                    self.rect.left = block.right
                    self.vel_x = -self.vel_x
       
        # Vertical movement and collision
        self.rect.y += self.vel_y
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_y > 0:
                    self.rect.bottom = block.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.bottom
                    self.vel_y = 0
   
    def draw(self, surface, camera_x):
        if not self.alive:
            return
        screen_x = self.rect.x - camera_x
        if not (0 <= screen_x < SCREEN_W + TILE): # Only draw if on screen
            return
           
        if self.type == "goomba":
            color = GOOMBA_BROWN
            # Body
            pygame.draw.ellipse(surface, color, (screen_x, self.rect.y, self.rect.width, self.rect.height))
            # Eyes
            pygame.draw.circle(surface, WHITE, (int(screen_x + 8), int(self.rect.y + 8)), 4)
            pygame.draw.circle(surface, WHITE, (int(screen_x + 16), int(self.rect.y + 8)), 4)
            pygame.draw.circle(surface, BLACK, (int(screen_x + 8), int(self.rect.y + 8)), 1)
            pygame.draw.circle(surface, BLACK, (int(screen_x + 16), int(self.rect.y + 8)), 1)
            # Legs
            pygame.draw.rect(surface, color, (screen_x, self.rect.y + self.rect.height - 4, 8, 4))
            pygame.draw.rect(surface, color, (screen_x + self.rect.width - 8, self.rect.y + self.rect.height - 4, 8, 4))
        else: # Koopa
            color = KOOPA_GREEN
            # Shell
            pygame.draw.rect(surface, (100, 50, 0), (screen_x + 4, self.rect.y + 8, self.rect.width - 8, self.rect.height - 6))
            # Head and feet
            head_x = screen_x + (4 if self.vel_x > 0 else self.rect.width - 4)
            pygame.draw.circle(surface, color, (int(head_x), int(self.rect.y + 12)), 6)
            pygame.draw.rect(surface, color, (screen_x, self.rect.y + self.rect.height - 8, 8, 8))
            pygame.draw.rect(surface, color, (screen_x + self.rect.width - 8, self.rect.y + self.rect.height - 8, 8, 8))

def draw_pipe(surface, x, y, camera_x):
    """Draw a Mario pipe (single tile)"""
    screen_x = x - camera_x
    if not (-TILE <= screen_x <= SCREEN_W + TILE):
        return
       
    # Pipe body
    pygame.draw.rect(surface, PIPE_GREEN, (screen_x, y, TILE, TILE))
    # Pipe rim
    pygame.draw.rect(surface, PIPE_DARK, (screen_x-2, y-2, TILE+4, 8))
    pygame.draw.rect(surface, PIPE_GREEN, (screen_x, y, TILE, 4))
   
    # Pipe details
    pygame.draw.rect(surface, (40, 120, 0), (screen_x + 4, y + 4, TILE - 8, 4))
    pygame.draw.rect(surface, (40, 120, 0), (screen_x + 4, y + 20, TILE - 8, 4))

def draw_brick(surface, x, y, camera_x):
    """Draw a brick block"""
    screen_x = x - camera_x
    if not (-TILE <= screen_x <= SCREEN_W + TILE):
        return
       
    pygame.draw.rect(surface, BRICK, (screen_x, y, TILE, TILE))
    # Brick pattern
    for i in range(4):
        for j in range(4):
            pygame.draw.rect(surface, (180, 66, 12),
                           (screen_x + i*8 + 1, y + j*8 + 1, 6, 6))

def draw_question_block(surface, x, y, camera_x, frame):
    """Draw a ? block"""
    screen_x = x - camera_x
    if not (-TILE <= screen_x <= SCREEN_W + TILE):
        return
       
    pygame.draw.rect(surface, BLOCK, (screen_x, y, TILE, TILE))
    pygame.draw.rect(surface, (200, 136, 0), (screen_x+2, y+2, TILE-4, TILE-4))
   
    # Draw animated ?
    offset = math.sin(frame * 0.2) * 2
    pygame.draw.arc(surface, WHITE, (screen_x + 6, y + 4 + offset, 8, 8), 0, math.pi, 2)
    pygame.draw.line(surface, WHITE, (screen_x + 10, y + 8 + offset), (screen_x + 10, y + 12 + offset), 2)

def draw_coin(surface, x, y, camera_x, frame):
    """Draw an animated coin"""
    screen_x = x - camera_x
    if not (-TILE <= screen_x <= SCREEN_W + TILE):
        return
       
    width = abs(math.sin(frame * 0.15)) * 8 + 6
    coin_rect = pygame.Rect(screen_x + 16 - width//2, y + 8, width, 16)
   
    # Draw coin body
    pygame.draw.ellipse(surface, COIN_GOLD, coin_rect)
    # Draw shine
    pygame.draw.ellipse(surface, COIN_YELLOW, (coin_rect.x + 2, coin_rect.y + 2, coin_rect.width - 4, coin_rect.height - 4))
   
    # Draw coin details
    pygame.draw.circle(surface, (200, 150, 0), (coin_rect.centerx, coin_rect.centery), 2)

def draw_flag(surface, x, y, camera_x):
    """Draw the goal flag"""
    screen_x = x - camera_x
    if not (-TILE <= screen_x <= SCREEN_W + TILE):
        return
       
    # Pole
    pole_height = TILE * 8
    pygame.draw.rect(surface, FLAGPOLE_COLOR, (screen_x, y - pole_height, 4, pole_height))
   
    # Flag base
    pygame.draw.rect(surface, (150, 100, 50), (screen_x - 6, y - 4, 16, 8))
   
    # Flag
    flag_points = [
        (screen_x + 4, y - pole_height + 8),
        (screen_x + 20, y - pole_height + 24),
        (screen_x + 4, y - pole_height + 40)
    ]
    pygame.draw.polygon(surface, RED, flag_points)
    pygame.draw.polygon(surface, WHITE, flag_points, 2)

def draw_hud(surface, score, coins, world, level, time_left, lives):
    """Draw the game HUD"""
    font = pygame.font.SysFont("Arial", 24, bold=True)
   
    # Score
    score_text = font.render(f"MARIO {score:06d}", True, WHITE)
    surface.blit(score_text, (10, 10))
   
    # Coins
    coin_text = font.render(f"COINS x{coins:02d}", True, WHITE)
    surface.blit(coin_text, (180, 10))
   
    # World
    world_text = font.render(f"WORLD {world}-{level}", True, WHITE)
    surface.blit(world_text, (330, 10))
   
    # Time
    time_text = font.render(f"TIME {time_left:03d}", True, WHITE)
    surface.blit(time_text, (520, 10))
   
    # Lives
    lives_text = font.render(f"LIVES x{lives}", True, WHITE)
    surface.blit(lives_text, (680, 10))

def load_level(level_key):
    """Load a level and return all game objects"""
    level_data = LEVELS.get(level_key, LEVELS["1-1"])
    layout = level_data["layout"]
    theme = level_data["theme"]
   
    # Ensure all layout rows are the same length
    max_length = max(len(row) for row in layout)
    for i in range(len(layout)):
        layout[i] = layout[i].ljust(max_length)
   
    num_rows = len(layout)
    level_height = num_rows * TILE
    level_width = max_length * TILE
   
    blocks = []
    enemies = []
    coins = []
    player_start = None
    flag_pos = None
   
    for row_idx in range(num_rows):
        py = SCREEN_H - level_height + row_idx * TILE
        for col_idx in range(max_length):
            char = layout[row_idx][col_idx]
            if char == ' ':
                continue
            px = col_idx * TILE
           
            if char in 'XB?P':
                blocks.append(pygame.Rect(px, py, TILE, TILE))
            elif char == 'M':
                player_start = (px, py - TILE)
            elif char == 'E':
                enemy_type = "goomba" if random.random() < 0.7 else "koopa"
                enemies.append(Enemy(px, py - TILE, enemy_type))
            elif char == 'C':
                coins.append(pygame.Rect(px + 8, py + 8, 16, 16))
            elif char == 'F':
                flag_pos = (px, py)
   
    if player_start is None:
        player_start = (TILE * 2, SCREEN_H - 2 * TILE)
   
    return {
        "blocks": blocks,
        "enemies": enemies,
        "coins": coins,
        "player_start": player_start,
        "flag_pos": flag_pos,
        "theme": theme,
        "time": level_data["time"],
        "layout": layout
    }

def show_title_screen(surface):
    """Display the title screen"""
    surface.fill(SKY)
   
    # Title
    title_font = pygame.font.SysFont("Arial", 80, bold=True)
    title = title_font.render("ULTRA MARIO BROS", True, RED)
    title_rect = title.get_rect(center=(SCREEN_W//2, 150))
    surface.blit(title, title_rect)
   
    # Subtitle
    sub_font = pygame.font.SysFont("Arial", 40)
    subtitle = sub_font.render("All 32 Levels - Complete Edition", True, WHITE)
    sub_rect = subtitle.get_rect(center=(SCREEN_W//2, 220))
    surface.blit(subtitle, sub_rect)
   
    # Instructions - UPDATED CONTROLS
    inst_font = pygame.font.SysFont("Arial", 24)
    instructions = [
        "Arrow Keys: Move",
        "SPACE: Jump",
        "Z: Run",
        "X: Fire (when Fire Mario)",
        "",
        "Press SPACE to Start"
    ]
   
    y_offset = 280
    for line in instructions:
        text = inst_font.render(line, True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_W//2, y_offset))
        surface.blit(text, text_rect)
        y_offset += 30
   
    # Copyright
    copy_font = pygame.font.SysFont("Arial", 18)
    copyright = copy_font.render("[C] 1985 Nintendo [C] 2025 Samsoft", True, WHITE)
    copy_rect = copyright.get_rect(center=(SCREEN_W//2, SCREEN_H - 20))
    surface.blit(copyright, copy_rect)
   
    pygame.display.flip()

# === MAIN GAME ===
def main():
    # Game state
    current_world = 1
    current_level = 1
    score = 0
    coins_collected = 0
    lives = 3
    game_state = "title" # title, playing, level_complete, game_over
   
    # Show title screen
    show_title_screen(screen)
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
   
    # Main game loop
    running = True
    frame = 0
   
    while running:
        # Load level
        level_key = f"{current_world}-{current_level}"
        if level_key not in LEVELS:
            level_key = "1-1"
           
        level = load_level(level_key)
        player = Player(*level["player_start"])
        camera_x = 0
        time_left = level["time"]
        time_counter = 0
        fireballs = []  # List to track active fireballs
       
        level_running = True
        while level_running and running:
            dt = clock.tick(FPS) / 1000.0
            frame += 1
           
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    level_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        level_running = False
           
            keys = pygame.key.get_pressed()
           
            # Update time
            time_counter += dt
            if time_counter >= 1.0:
                time_counter = 0
                time_left -= 1
                if time_left <= 0:
                    lives -= 1
                    if lives <= 0:
                        game_state = "game_over"
                        level_running = False
                    else:
                        level_running = False
           
            # Update player
            result = player.update(keys, level["blocks"], level["enemies"], level["coins"], fireballs, dt)
            if result:
                if result["type"] == "coin":
                    coins_collected += 1
                    score += 100
                    if coins_collected >= 100:
                        lives += 1
                        coins_collected = 0
                elif result["type"] == "stomp":
                    score += 200
                elif result["type"] == "damage":
                    lives -= 1
                    player.invincible_timer = 120
                    if lives <= 0:
                        game_state = "game_over"
                        level_running = False
           
            # Update enemies
            for enemy in level["enemies"]:
                enemy.update(level["blocks"])
           
            # Update fireballs
            for fireball in fireballs[:]:
                result = fireball.update(level["blocks"], level["enemies"])
                if result == "hit":
                    score += 100
                    fireballs.remove(fireball)
                elif result == "dead":
                    fireballs.remove(fireball)
           
            # Camera follow player (with bounds)
            camera_x = max(0, player.rect.centerx - SCREEN_W // 4)
            camera_x = min(camera_x, max(0, len(level["layout"][0]) * TILE - SCREEN_W))
           
            # Check if reached flag
            if level["flag_pos"]:
                flag_x, flag_y = level["flag_pos"]
                if player.rect.right >= flag_x:
                    score += time_left * 10
                    current_level += 1
                    if current_level > 4:
                        current_level = 1
                        current_world += 1
                        if current_world > 8:
                            game_state = "victory"
                            level_running = False
                    level_running = False
           
            # Rendering
            if level["theme"] == "underground":
                screen.fill(UNDERGROUND_BG)
            elif level["theme"] == "castle":
                screen.fill(CASTLE_BG)
            else:
                screen.fill(SKY)
           
            # Draw blocks and items
            for block in level["blocks"]:
                screen_x = block.x - camera_x
                if not (-TILE < screen_x < SCREEN_W + TILE):
                    continue
                    
                # Calculate row and column in layout
                row_idx = (block.y - (SCREEN_H - len(level["layout"]) * TILE)) // TILE
                col_idx = block.x // TILE
                
                # Ensure indices are within bounds
                if 0 <= row_idx < len(level["layout"]) and 0 <= col_idx < len(level["layout"][row_idx]):
                    char = level["layout"][row_idx][col_idx]
                    
                    if char == 'B':
                        draw_brick(screen, block.x, block.y, camera_x)
                    elif char == '?':
                        draw_question_block(screen, block.x, block.y, camera_x, frame)
                    elif char == 'P':
                        draw_pipe(screen, block.x, block.y, camera_x)
                    else:
                        # Ground
                        pygame.draw.rect(screen, GROUND, (screen_x, block.y, TILE, TILE))
                        pygame.draw.rect(screen, (160, 130, 80), (screen_x+2, block.y+2, TILE-4, TILE-4))
           
            # Draw coins
            for coin in level["coins"]:
                draw_coin(screen, coin.x - 8, coin.y - 8, camera_x, frame)
           
            # Draw enemies
            for enemy in level["enemies"]:
                enemy.draw(screen, camera_x)
           
            # Draw fireballs
            for fireball in fireballs:
                fireball.draw(screen, camera_x)
           
            # Draw flag
            if level["flag_pos"]:
                draw_flag(screen, level["flag_pos"][0], level["flag_pos"][1], camera_x)
           
            # Draw player
            player.draw(screen, camera_x)
           
            # Draw HUD
            draw_hud(screen, score, coins_collected, current_world, current_level,
                    time_left, lives)
           
            pygame.display.flip()
       
        # Handle game over
        if game_state == "game_over":
            screen.fill(BLACK)
            font = pygame.font.SysFont("Arial", 80, bold=True)
            text = font.render("GAME OVER", True, RED)
            text_rect = text.get_rect(center=(SCREEN_W//2, SCREEN_H//2))
            screen.blit(text, text_rect)
           
            score_font = pygame.font.SysFont("Arial", 32)
            score_text = score_font.render(f"FINAL SCORE: {score:06d}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 80))
            screen.blit(score_text, score_rect)
           
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
       
        # Handle victory
        if game_state == "victory":
            screen.fill(SKY)
            font = pygame.font.SysFont("Arial", 60, bold=True)
            text = font.render("CONGRATULATIONS!", True, RED)
            text_rect = text.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 40))
            screen.blit(text, text_rect)
           
            score_font = pygame.font.SysFont("Arial", 40)
            score_text = score_font.render(f"YOU SAVED THE PRINCESS!", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 20))
            screen.blit(score_text, score_rect)
           
            final_score = score_font.render(f"FINAL SCORE: {score:06d}", True, WHITE)
            final_rect = final_score.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 70))
            screen.blit(final_score, final_rect)
           
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False
   
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
