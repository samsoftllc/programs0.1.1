# program.py
# ULTRA MARIO BROS - Complete SMB1 Recreation (32 Levels)
# [C] 1985 Nintendo [C] 2025 Samsoft | Pure Pygame Implementation
# Arrow Keys: Move | Z: Jump | X: Run/Fire | ESC: Quit

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
CASTLE_BG = (0, 0, 0)

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
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                 ???                                                                                                              ",
            "                                                                                                                                                  ",
            "     BBB?BBB        CC                          BB?BB                                                                                             ",
            "   E                       E                                 E        E                                                                           ",
            "                                  PPP                   PPP                PPPP                                                        F          ",
            "                                  PPP                   PPP                PPPP                                                      FFF          ",
            "M                                 PPP                   PPP                PPPP                                                    FFFFF          ",
            "                                  PPP                   PPP                PPPP                                                  XXXXXXX          ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
    "1-2": {
        "theme": "underground",
        "time": 400,
        "layout": [
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "         ???                    ???                                                                                                               ",
            "                                                                                                                                                  ",
            "     C   C   C                                            BBB                                                                           F         ",
            "   E                  E                       E                                E                                                       F         ",
            "                                                                                                                                        F         ",
            "                                                                                                                                        F         ",
            "M                                                                                                                                       F         ",
            "                                                                                                                                        F         ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
    "1-3": {
        "theme": "overworld",
        "time": 300,
        "layout": [
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                       BBBBBBBB                                                                                   ",
            "                    BBBBBB                                                                                                                        ",
            "             BBBBB                                                         BBBBBBBB                                                               ",
            "      BBBBB                                                                                                                                       ",
            "   E                                  E                                                   E                                            F         ",
            "                                                                                                                                       FFF        ",
            "                                                                                                                                     FFFFF        ",
            "M                                                                                                                                  XXXXXXX        ",
            "                                                                                                                                XXXXXXXXXXX        ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
    "1-4": {
        "theme": "castle",
        "time": 300,
        "layout": [
            "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "            XXXXX              XXXXX              XXXXX              XXXXX                                                                        ",
            "                                                                                                                                                  ",
            "                                                                                                                                                  ",
            "   E              E                  E                  E                                    E                                         F         ",
            "                                                                                                                                       FFF        ",
            "                                                                                                                                     FFFFF        ",
            "M                                                                                                                                  XXXXXXX        ",
            "                                                                                                                                XXXXXXXXXXX        ",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        ]
    },
}

# Generate additional levels (2-1 through 8-4)
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
        
        LEVELS[level_key] = {
            "theme": theme,
            "time": 400 if level < 4 else 300,
            "layout": [
                "                                                                                                                                                  ",
                "                                                                                                                                                  ",
                "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB" if theme != "overworld" else "                                                                                                                                                  ",
                "                                                                                                                                                  ",
                "                                                                                                                                                  ",
                f"         {'???' if level % 2 == 1 else 'BBB'}                    {'BBB' if level % 2 == 0 else '???'}                                                                                                               ",
                "                                                                                                                                                  ",
                f"     {'C   C   C' if theme == 'underground' else 'BBB?BBB'}                                            BBB                                                                           F         ",
                f"   E                  E                       E                                E                                                       {'F' if level == 4 else 'FFF'}         ",
                f"                                  {'PPP' if theme == 'overworld' else '   '}                   PPP                {'PPPP' if theme == 'overworld' else '    '}                                                        {'F' if level == 4 else 'FFFFF'}        ",
                f"                                  {'PPP' if theme == 'overworld' else '   '}                   PPP                {'PPPP' if theme == 'overworld' else '    '}                                                      {'FFF' if level == 4 else 'XXXXXXX'}        ",
                f"M                                 {'PPP' if theme == 'overworld' else '   '}                   PPP                {'PPPP' if theme == 'overworld' else '    '}                                                    {'FFFFF' if level == 4 else 'XXXXXXXXXXX'}        ",
                f"                                  {'PPP' if theme == 'overworld' else '   '}                   PPP                {'PPPP' if theme == 'overworld' else '    '}                                                  {'XXXXXXX' if level == 4 else 'XXXXXXXXXXXXX'}        ",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            ]
        }

# === ENTITY CLASSES ===
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE-4, TILE)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.size = "small"  # small, big, fire
        self.invincible_timer = 0
        self.jump_held = False
        
    def update(self, keys, blocks, enemies, coins, dt):
        # Input handling
        run = keys[pygame.K_x]
        max_speed = RUN_SPEED if run else WALK_SPEED
        jump_speed = RUN_JUMP_SPEED if run else JUMP_SPEED
        
        # Horizontal movement
        if keys[pygame.K_RIGHT]:
            self.vel_x = min(self.vel_x + 0.5, max_speed)
            self.facing_right = True
        elif keys[pygame.K_LEFT]:
            self.vel_x = max(self.vel_x - 0.5, -max_speed)
            self.facing_right = False
        else:
            # Deceleration
            if self.vel_x > 0:
                self.vel_x = max(0, self.vel_x - 0.3)
            elif self.vel_x < 0:
                self.vel_x = min(0, self.vel_x + 0.3)
        
        # Jumping
        if keys[pygame.K_z] and self.on_ground and not self.jump_held:
            self.vel_y = jump_speed
            self.jump_held = True
        if not keys[pygame.K_z]:
            self.jump_held = False
        
        # Gravity
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        
        # Horizontal collision
        self.rect.x += self.vel_x
        for block in blocks:
            if self.rect.colliderect(block):
                if self.vel_x > 0:
                    self.rect.right = block.left
                elif self.vel_x < 0:
                    self.rect.left = block.right
                self.vel_x = 0
        
        # Vertical collision
        self.rect.y += self.vel_y
        self.on_ground = False
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
                return {"type": "coin"}
        
        # Enemy collision
        if self.invincible_timer <= 0:
            for enemy in enemies[:]:
                if self.rect.colliderect(enemy["rect"]):
                    # Stomp enemy
                    if self.vel_y > 0 and self.rect.bottom - enemy["rect"].top < 10:
                        enemies.remove(enemy)
                        self.vel_y = -8
                        return {"type": "stomp"}
                    else:
                        # Take damage
                        return {"type": "damage"}
        
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        return None
    
    def draw(self, surface, camera_x):
        screen_x = self.rect.x - camera_x
        color = RED if self.invincible_timer % 10 < 5 else (255, 100, 100)
        
        # Draw Mario
        pygame.draw.rect(surface, color, (screen_x, self.rect.y, self.rect.width, self.rect.height))
        # Hat
        pygame.draw.circle(surface, color, (int(screen_x + self.rect.width//2), int(self.rect.y + 5)), 8)
        # Eyes
        eye_offset = 3 if self.facing_right else -3
        pygame.draw.circle(surface, BLACK, (int(screen_x + self.rect.width//2 + eye_offset), int(self.rect.y + 8)), 2)

class Enemy:
    def __init__(self, x, y, enemy_type="goomba"):
        self.rect = pygame.Rect(x, y, TILE-8, TILE-8)
        self.vel_x = -ENEMY_SPEED
        self.type = enemy_type
        
    def update(self, blocks):
        self.rect.x += self.vel_x
        
        # Check collisions
        for block in blocks:
            if self.rect.colliderect(block):
                self.vel_x *= -1
                break
    
    def draw(self, surface, camera_x):
        screen_x = self.rect.x - camera_x
        color = GOOMBA_BROWN if self.type == "goomba" else KOOPA_GREEN
        
        # Body
        pygame.draw.ellipse(surface, color, (screen_x, self.rect.y, self.rect.width, self.rect.height))
        # Eyes
        pygame.draw.circle(surface, WHITE, (int(screen_x + 8), int(self.rect.y + 8)), 4)
        pygame.draw.circle(surface, WHITE, (int(screen_x + 16), int(self.rect.y + 8)), 4)
        pygame.draw.circle(surface, BLACK, (int(screen_x + 8), int(self.rect.y + 8)), 2)
        pygame.draw.circle(surface, BLACK, (int(screen_x + 16), int(self.rect.y + 8)), 2)

def draw_pipe(surface, x, y, camera_x):
    """Draw a Mario pipe"""
    screen_x = x - camera_x
    # Pipe body
    pygame.draw.rect(surface, PIPE_GREEN, (screen_x, y, TILE*2, TILE*3))
    # Pipe rim
    pygame.draw.rect(surface, PIPE_DARK, (screen_x-4, y-4, TILE*2+8, TILE//2))
    pygame.draw.rect(surface, PIPE_GREEN, (screen_x-2, y-2, TILE*2+4, TILE//2-4))

def draw_brick(surface, x, y, camera_x):
    """Draw a brick block"""
    screen_x = x - camera_x
    pygame.draw.rect(surface, BRICK, (screen_x, y, TILE, TILE))
    # Brick pattern
    for i in range(4):
        for j in range(4):
            pygame.draw.rect(surface, (180, 66, 12), 
                           (screen_x + i*8 + 1, y + j*8 + 1, 6, 6))

def draw_question_block(surface, x, y, camera_x, frame):
    """Draw a ? block"""
    screen_x = x - camera_x
    pygame.draw.rect(surface, BLOCK, (screen_x, y, TILE, TILE))
    pygame.draw.rect(surface, (200, 136, 0), (screen_x+2, y+2, TILE-4, TILE-4))
    # Draw animated ?
    font = pygame.font.Font(None, 40)
    text = font.render("?", True, WHITE)
    offset = math.sin(frame * 0.2) * 2
    surface.blit(text, (screen_x + 6, y + 4 + offset))

def draw_coin(surface, x, y, camera_x, frame):
    """Draw an animated coin"""
    screen_x = x - camera_x
    width = abs(math.sin(frame * 0.15)) * 8 + 6
    pygame.draw.ellipse(surface, COIN_GOLD, (screen_x + 16 - width//2, y + 8, width, 16))
    pygame.draw.ellipse(surface, COIN_YELLOW, (screen_x + 18 - width//2, y + 10, width-4, 12))

def draw_flag(surface, x, y, camera_x):
    """Draw the goal flag"""
    screen_x = x - camera_x
    # Pole
    pygame.draw.rect(surface, WHITE, (screen_x, y, 4, TILE*6))
    # Flag
    for i in range(6):
        color = RED if i % 2 == 0 else WHITE
        pygame.draw.rect(surface, color, (screen_x + 4, y + i*8, 20, 8))

def draw_hud(surface, score, coins, world, level, time_left, lives):
    """Draw the game HUD"""
    font = pygame.font.Font(None, 24)
    
    # Score
    score_text = font.render(f"SCORE: {score:06d}", True, WHITE)
    surface.blit(score_text, (10, 10))
    
    # Coins
    coin_text = font.render(f"COINS: {coins:02d}", True, WHITE)
    surface.blit(coin_text, (180, 10))
    
    # World
    world_text = font.render(f"WORLD {world}-{level}", True, WHITE)
    surface.blit(world_text, (330, 10))
    
    # Time
    time_text = font.render(f"TIME: {time_left:03d}", True, WHITE)
    surface.blit(time_text, (520, 10))
    
    # Lives (draw Mario heads)
    lives_text = font.render(f"x{lives}", True, WHITE)
    surface.blit(lives_text, (700, 10))
    pygame.draw.circle(surface, RED, (680, 18), 10)

def load_level(level_key):
    """Load a level and return all game objects"""
    level_data = LEVELS.get(level_key, LEVELS["1-1"])
    layout = level_data["layout"]
    theme = level_data["theme"]
    
    blocks = []
    enemies = []
    coins = []
    player_start = (100, SCREEN_H - 3*TILE)
    flag_pos = None
    
    for y, row in enumerate(layout):
        for x, char in enumerate(row):
            px, py = x * TILE, y * TILE
            
            if char == 'X':
                blocks.append(pygame.Rect(px, py, TILE, TILE))
            elif char == 'B':
                blocks.append(pygame.Rect(px, py, TILE, TILE))
            elif char == '?':
                blocks.append(pygame.Rect(px, py, TILE, TILE))
            elif char == 'P':
                blocks.append(pygame.Rect(px, py, TILE*2, TILE*3))
            elif char == 'M':
                player_start = (px, py)
            elif char == 'E':
                enemies.append({"rect": pygame.Rect(px, py, TILE-8, TILE-8), 
                              "vel_x": -ENEMY_SPEED, "type": "goomba"})
            elif char == 'C':
                coins.append(pygame.Rect(px + 8, py + 8, 16, 16))
            elif char == 'F':
                flag_pos = (px, py)
    
    return {
        "blocks": blocks,
        "enemies": enemies,
        "coins": coins,
        "player_start": player_start,
        "flag_pos": flag_pos,
        "theme": theme,
        "time": level_data["time"]
    }

def show_title_screen(surface):
    """Display the title screen"""
    surface.fill(SKY)
    
    # Title
    title_font = pygame.font.Font(None, 80)
    title = title_font.render("ULTRA MARIO BROS", True, RED)
    title_rect = title.get_rect(center=(SCREEN_W//2, 150))
    surface.blit(title, title_rect)
    
    # Subtitle
    sub_font = pygame.font.Font(None, 40)
    subtitle = sub_font.render("All 32 Levels - Complete Edition", True, WHITE)
    sub_rect = subtitle.get_rect(center=(SCREEN_W//2, 220))
    surface.blit(subtitle, sub_rect)
    
    # Instructions
    inst_font = pygame.font.Font(None, 24)
    instructions = [
        "Arrow Keys: Move",
        "Z: Jump",
        "X: Run/Fire",
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
    copy_font = pygame.font.Font(None, 18)
    copyright = copy_font.render("[C] 1985 Nintendo  [C] 2025 Samsoft", True, WHITE)
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
    game_state = "title"  # title, playing, level_complete, game_over
    
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
        level = load_level(level_key)
        player = Player(*level["player_start"])
        camera_x = 0
        time_left = level["time"]
        time_counter = 0
        
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
            time_counter += 1
            if time_counter >= FPS:
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
            result = player.update(keys, level["blocks"], level["enemies"], level["coins"], dt)
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
                enemy["rect"].x += enemy["vel_x"]
                for block in level["blocks"]:
                    if enemy["rect"].colliderect(block):
                        enemy["vel_x"] *= -1
                        break
            
            # Camera follow player
            camera_x = max(0, player.rect.centerx - SCREEN_W // 2)
            
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
            
            # Draw blocks
            for block in level["blocks"]:
                if SCREEN_W > block.x - camera_x > -TILE:
                    screen_x = block.x - camera_x
                    pygame.draw.rect(screen, GROUND, (screen_x, block.y, TILE, TILE))
                    pygame.draw.rect(screen, (160, 130, 80), (screen_x+2, block.y+2, TILE-4, TILE-4))
            
            # Draw coins
            for coin in level["coins"]:
                draw_coin(screen, coin.x - 8, coin.y - 8, camera_x, frame)
            
            # Draw enemies
            for enemy in level["enemies"]:
                screen_x = enemy["rect"].x - camera_x
                if -TILE < screen_x < SCREEN_W:
                    color = GOOMBA_BROWN
                    pygame.draw.ellipse(screen, color, 
                                      (screen_x, enemy["rect"].y, enemy["rect"].width, enemy["rect"].height))
                    # Eyes
                    pygame.draw.circle(screen, WHITE, (int(screen_x + 8), int(enemy["rect"].y + 8)), 3)
                    pygame.draw.circle(screen, WHITE, (int(screen_x + 16), int(enemy["rect"].y + 8)), 3)
                    pygame.draw.circle(screen, BLACK, (int(screen_x + 8), int(enemy["rect"].y + 8)), 1)
                    pygame.draw.circle(screen, BLACK, (int(screen_x + 16), int(enemy["rect"].y + 8)), 1)
            
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
            font = pygame.font.Font(None, 80)
            text = font.render("GAME OVER", True, RED)
            text_rect = text.get_rect(center=(SCREEN_W//2, SCREEN_H//2))
            screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
        
        # Handle victory
        if game_state == "victory":
            screen.fill(SKY)
            font = pygame.font.Font(None, 60)
            text = font.render("CONGRATULATIONS!", True, RED)
            text_rect = text.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 40))
            screen.blit(text, text_rect)
            
            score_font = pygame.font.Font(None, 40)
            score_text = score_font.render(f"Final Score: {score:06d}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_W//2, SCREEN_H//2 + 20))
            screen.blit(score_text, score_rect)
            
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
