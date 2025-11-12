import pygame
import sys
import math

# --- CONSTANTS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.8
PLAYER_JUMP_STRENGTH = -18
PLAYER_MAX_SPEED = 6
PLAYER_ACCEL = 0.15
PLAYER_FRICTION = 0.15
PLAYER_SKID_ACCEL = 0.2
ENEMY_SPEED = 2

# Colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
DARK_GREEN = (0, 100, 0)

# Menu-specific Colors
MENU_BG_COLOR = (100, 149, 237)
TITLE_COLOR = (252, 216, 168)
TITLE_SHADOW_COLOR = (139, 69, 19)
MENU_TEXT_COLOR = (255, 255, 255)
GROUND_COLOR = (218, 165, 32)
BRICK_COLOR = (188, 74, 46)

LEVELS = [
    [
        "                                         F",
        "                                          ",
        "                                          ",
        "                                          ",
        "                                          ",
        "                ?                         ",
        "            - - - - - - -                 ",
        "                                          ",
        "P   X           G         G               X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    [
        "                                          F",
        "                                          ",
        "                                          ",
        "      ?           ?                       ",
        " - - - - - - - - - - - - - - - - - - - - - ",
        "                                          ",
        "P       G           G       G             X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    [
        "                                            F",
        "                                            ",
        "                                            ",
        "      ?                         ?           ",
        " - - - - - - - - - - - - - - - - - - - - - - ",
        "                                            ",
        "P   G       G           G       G       G   X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ]
]

TILE_SIZE = 40

def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    return 0


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
        self.image.fill(RED)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect = pygame.Rect(int(self.pos_x), int(self.pos_y), TILE_SIZE, TILE_SIZE)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.input_dir = 0
        self.jump_held = False

    def jump(self):
        if self.on_ground:
            self.vel_y = PLAYER_JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms):
        if self.on_ground:
            if self.input_dir != 0:
                accel = PLAYER_ACCEL if sign(self.input_dir) == sign(self.vel_x) or abs(self.vel_x) < 1 else PLAYER_SKID_ACCEL
                self.vel_x += self.input_dir * accel
            else:
                if abs(self.vel_x) > PLAYER_FRICTION:
                    self.vel_x -= sign(self.vel_x) * PLAYER_FRICTION
                else:
                    self.vel_x = 0
        else:
            if self.input_dir != 0:
                self.vel_x += self.input_dir * PLAYER_ACCEL * 0.5

        if abs(self.vel_x) > PLAYER_MAX_SPEED:
            self.vel_x = sign(self.vel_x) * PLAYER_MAX_SPEED

        self.vel_y += GRAVITY
        if self.vel_y > 20:
            self.vel_y = 20

        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)
        self.check_collisions(platforms, "horizontal")
        self.pos_x = float(self.rect.x)

        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        self.on_ground = False
        self.check_collisions(platforms, "vertical")
        self.pos_y = float(self.rect.y)

        if self.pos_y > SCREEN_HEIGHT + TILE_SIZE * 2:
            return True
        return False

    def check_collisions(self, platforms, direction):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if direction == "horizontal":
                    if self.vel_x > 0:
                        self.rect.right = platform.rect.left
                    elif self.vel_x < 0:
                        self.rect.left = platform.rect.right
                    self.vel_x = 0
                elif direction == "vertical":
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:
                        self.rect.top = platform.rect.bottom
                        self.vel_y = 0
                        if platform.tile_type == "?":
                            platform.image.fill(ORANGE)
                            platform.tile_type = "-"
                            print("Coin collected!")


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
        self.image.fill(DARK_GREEN)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rect = pygame.Rect(int(self.pos_x), int(self.pos_y), TILE_SIZE, TILE_SIZE)
        self.vel_x = -ENEMY_SPEED
        self.vel_y = 0.0

    def update(self, platforms):
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)
        self.check_collisions(platforms, "horizontal")
        self.pos_x = float(self.rect.x)

        self.vel_y += GRAVITY
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        self.check_collisions(platforms, "vertical")
        self.pos_y = float(self.rect.y)

    def check_collisions(self, platforms, direction):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if direction == "horizontal":
                    if self.vel_x > 0:
                        self.rect.right = platform.rect.left
                    elif self.vel_x < 0:
                        self.rect.left = platform.rect.right
                    self.vel_x *= -1
                elif direction == "vertical":
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                    elif self.vel_y < 0:
                        self.rect.top = platform.rect.bottom
                        self.vel_y = 0


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, tile_type):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
        if tile_type == "X":
            self.image.fill(BROWN)
        elif tile_type == "-":
            self.image.fill(ORANGE)
        elif tile_type == "?":
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.tile_type = tile_type


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ultra Mario 2d bros v0")
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_level_index = 0
        self.scroll = 0
        self.level_width = 0

        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player = None
        self.flag_rect = None

        self.game_state = "MENU"
        self.selected_option = 0
        self.top_score = 0

        try:
            self.title_font = pygame.font.SysFont('Consolas', 50, bold=True)
            self.copyright_font = pygame.font.SysFont('Consolas', 20)
            self.menu_font = pygame.font.SysFont('Consolas', 28)
            self.top_score_font = pygame.font.SysFont('Consolas', 28)
        except:
            print("Consolas font not found.")
            self.title_font = pygame.font.Font(None, 60)
            self.copyright_font = pygame.font.Font(None, 24)
            self.menu_font = pygame.font.Font(None, 32)
            self.top_score_font = pygame.font.Font(None, 32)

        self.load_level(self.current_level_index)

    def load_level(self, index):
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()
        self.scroll = 0
        layout = LEVELS[index]
        self.level_width = len(layout[0]) * TILE_SIZE

        for y, row in enumerate(layout):
            for x, tile in enumerate(row):
                world_x, world_y = x * TILE_SIZE, y * TILE_SIZE
                if tile == "P":
                    self.player = Player(world_x, world_y)
                    self.all_sprites.add(self.player)
                elif tile in ["X", "-", "?"]:
                    platform = Platform(world_x, world_y, tile)
                    self.platforms.add(platform)
                    self.all_sprites.add(platform)
                elif tile == "G":
                    enemy = Enemy(world_x, world_y)
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
                elif tile == "F":
                    self.flag_rect = pygame.Rect(world_x, world_y - TILE_SIZE*3, TILE_SIZE, TILE_SIZE * 4)

        if not self.player:
            self.player = Player(100, SCREEN_HEIGHT - TILE_SIZE * 2)
            self.all_sprites.add(self.player)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self.player.jump()
                    self.player.jump_held = True
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    self.player.jump_held = False
                    if self.player.vel_y < -8:
                        self.player.vel_y = -8

        keys = pygame.key.get_pressed()
        self.player.input_dir = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])

    def handle_menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = 0
                elif event.key == pygame.K_DOWN:
                    self.selected_option = 1
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.current_level_index = 0
                    self.load_level(self.current_level_index)
                    self.game_state = "PLAYING"

    def update(self):
        if self.player.update(self.platforms):
            self.load_level(self.current_level_index)
            return
        for enemy in self.enemies:
            enemy.update(self.platforms)
            if self.player.rect.colliderect(enemy.rect):
                if self.player.vel_y > 0 and self.player.rect.bottom < enemy.rect.centery + 10:
                    enemy.kill()
                    self.player.vel_y = PLAYER_JUMP_STRENGTH / 2
                else:
                    self.load_level(self.current_level_index)
                    return
        target_scroll = self.player.rect.x - SCREEN_WIDTH / 2
        target_scroll = max(0, min(target_scroll, self.level_width - SCREEN_WIDTH))
        self.scroll += (target_scroll - self.scroll) * 0.1
        if self.flag_rect and self.player.rect.colliderect(self.flag_rect):
            self.current_level_index += 1
            if self.current_level_index < len(LEVELS):
                self.load_level(self.current_level_index)
            else:
                print("YOU WIN!")
                self.game_state = "MENU"
                self.current_level_index = 0
                self.load_level(self.current_level_index)

    def draw_menu(self):
        self.screen.fill(MENU_BG_COLOR)
        ground_height = 80
        pygame.draw.rect(self.screen, GROUND_COLOR, (0, SCREEN_HEIGHT - ground_height, SCREEN_WIDTH, ground_height))
        for x in range(0, SCREEN_WIDTH, TILE_SIZE):
            pygame.draw.rect(self.screen, BRICK_COLOR, (x, SCREEN_HEIGHT - ground_height, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(self.screen, BLACK, (x, SCREEN_HEIGHT - ground_height, TILE_SIZE, TILE_SIZE), 1)
        title_text = "Ultra Mario 2d bros v0"
        shadow_surf = self.title_font.render(title_text, True, TITLE_SHADOW_COLOR)
        title_surf = self.title_font.render(title_text, True, TITLE_COLOR)
        padding_x, padding_y = 20, 20
        box_width = title_surf.get_width() + 2 * padding_x
        box_height = title_surf.get_height() + 2 * padding_y
        box_x = SCREEN_WIDTH // 2 - box_width // 2
        box_y = 90
        pygame.draw.rect(self.screen, BROWN, (box_x, box_y, box_width, box_height), border_radius=5)
        shadow_pos = (box_x + padding_x, box_y + padding_y)
        title_pos = (box_x + padding_x - 4, box_y + padding_y - 4)
        self.screen.blit(shadow_surf, shadow_pos)
        self.screen.blit(title_surf, title_pos)
        copyright_text = "© Samsoft 2025"
        copyright_surf = self.copyright_font.render(copyright_text, True, MENU_TEXT_COLOR)
        copyright_pos = (SCREEN_WIDTH // 2 - copyright_surf.get_width() // 2, box_y + box_height + 10)
        self.screen.blit(copyright_surf, copyright_pos)
        option1_text = "1 PLAYER GAME"
        option2_text = "2 PLAYER GAME"
        option1_surf = self.menu_font.render(option1_text, True, MENU_TEXT_COLOR)
        option2_surf = self.menu_font.render(option2_text, True, MENU_TEXT_COLOR)
        option1_y = 280
        option2_y = option1_y + 50
        option1_pos = (SCREEN_WIDTH // 2 - option1_surf.get_width() // 2, option1_y)
        option2_pos = (SCREEN_WIDTH // 2 - option2_surf.get_width() // 2, option2_y)
        self.screen.blit(option1_surf, option1_pos)
        self.screen.blit(option2_surf, option2_pos)
        top_score_text = f"TOP- {self.top_score:06d}"
        top_score_surf = self.top_score_font.render(top_score_text, True, MENU_TEXT_COLOR)
        top_score_pos = (SCREEN_WIDTH // 2 - top_score_surf.get_width() // 2, option2_y + 70)
        self.screen.blit(top_score_surf, top_score_pos)
        cursor_y = option1_pos[1] if self.selected_option == 0 else option2_pos[1]
        cursor_x = option1_pos[0] - 40
        pygame.draw.circle(self.screen, RED, (cursor_x, cursor_y + 10), 10)
        pygame.draw.rect(self.screen, WHITE, (cursor_x - 5, cursor_y + 15, 10, 8))
        pygame.draw.circle(self.screen, BLACK, (cursor_x - 4, cursor_y + 16), 2)
        pygame.draw.circle(self.screen, BLACK, (cursor_x + 4, cursor_y + 16), 2)

        # --- NEW: Retro footer ---
        footer_text = "[C] 1985 - Nintendo"
        footer_surf = self.copyright_font.render(footer_text, True, MENU_TEXT_COLOR)
        footer_pos = (SCREEN_WIDTH // 2 - footer_surf.get_width() // 2,
                      SCREEN_HEIGHT - footer_surf.get_height() - 10)
        self.screen.blit(footer_surf, footer_pos)

        pygame.display.flip()

    def draw(self):
        self.screen.fill(SKY_BLUE)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, (sprite.rect.x - self.scroll, sprite.rect.y))
        if self.flag_rect:
            pole_rect = pygame.Rect(self.flag_rect.x - self.scroll + TILE_SIZE // 2 - 5, self.flag_rect.y, 10, self.flag_rect.height)
            pygame.draw.rect(self.screen, GREEN, pole_rect)
            pygame.draw.circle(self.screen, BLACK, (pole_rect.centerx, pole_rect.top), 8)
            flag_y = self.flag_rect.y + 20
            pygame.draw.polygon(
                self.screen, RED,
                [(pole_rect.right, flag_y),
                 (pole_rect.right + TILE_SIZE - 5, flag_y + 15),
                 (pole_rect.right, flag_y + 30)]
            )
        font = pygame.font.Font(None, 36)
        self.screen.blit(font.render(f"Level: {self.current_level_index + 1}", True, BLACK), (10, 10))
        pygame.display.flip()

    def run(self):
        while self.running:
            if self.game_state == "MENU":
                self.handle_menu_events()
                self.draw_menu()
            else:
                self.handle_events()
                self.update()
                self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
