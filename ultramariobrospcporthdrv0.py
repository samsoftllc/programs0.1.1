import pygame
import sys

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

# Level Layout Legend
# ' ' : Empty Space
# 'X' : Solid Ground Block
# '-' : Brick Block
# '?' : Question Block
# 'G' : Goomba (Enemy)
# 'P' : Player Start
# 'F' : Flag/Level End

LEVELS = [
    [
        "                                          F",
        "                                          ",
        "                                          ",
        "                                          ",
        "                                          ",
        "                     ?                    ",
        "               - - - - - - -              ",
        "                                          ",
        "P   X           G           G             X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    [
        "                                            F",
        "                                            ",
        "                                            ",
        "      ?          ?                          ",
        " - - - - - - - - - - - - - - - - - - - - - ",
        "                                            ",
        "P       G           G       G              X",
        "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    ],
    [
        "                                              F",
        "                                              ",
        "                                              ",
        "      ?                   ?                   ",
        " - - - - - - - - - - - - - - - - - - - - - -  ",
        "                                              ",
        "P   G       G           G       G       G     X",
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
        # Horizontal physics (SMB1-like acceleration and friction)
        if self.on_ground:
            if self.input_dir != 0:
                if sign(self.input_dir) == sign(self.vel_x) or abs(self.vel_x) < 1:
                    accel = PLAYER_ACCEL
                else:
                    accel = PLAYER_SKID_ACCEL
                self.vel_x += self.input_dir * accel
            else:
                self.vel_x -= sign(self.vel_x) * PLAYER_FRICTION
        else:
            # Air control (reduced accel)
            if self.input_dir != 0:
                self.vel_x += self.input_dir * PLAYER_ACCEL * 0.5

        if abs(self.vel_x) > PLAYER_MAX_SPEED:
            self.vel_x = sign(self.vel_x) * PLAYER_MAX_SPEED

        # Gravity
        self.vel_y += GRAVITY
        if self.vel_y > 20:
            self.vel_y = 20

        # Horizontal movement
        self.pos_x += self.vel_x
        self.rect.x = int(self.pos_x)
        self.check_collisions(platforms, "horizontal")
        self.pos_x = self.rect.x  # Sync pos after adjustment

        # Vertical movement
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        self.on_ground = False
        self.check_collisions(platforms, "vertical")
        self.pos_y = self.rect.y  # Sync pos after adjustment

        # Fall death check
        if self.pos_y > SCREEN_HEIGHT + TILE_SIZE * 2:
            return True  # Signal death
        return False

    def check_collisions(self, platforms, direction):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if direction == "horizontal":
                    if self.vel_x > 0:
                        self.rect.right = platform.rect.left
                    elif self.vel_x < 0:
                        self.rect.left = platform.rect.right
                elif direction == "vertical":
                    if self.vel_y > 0:
                        self.rect.bottom = platform.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                    elif self.vel_y < 0:
                        self.rect.top = platform.rect.bottom
                        self.vel_y = 0
                        # Hit block from below
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
        self.pos_x = self.rect.x

        self.vel_y += GRAVITY
        self.pos_y += self.vel_y
        self.rect.y = int(self.pos_y)
        self.check_collisions(platforms, "vertical")
        self.pos_y = self.rect.y

    def check_collisions(self, platforms, direction):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if direction == "horizontal":
                    if self.vel_x > 0:
                        self.rect.right = platform.rect.left
                    elif self.vel_x < 0:
                        self.rect.left = platform.rect.right
                    self.vel_x *= -1  # Reverse direction like SMB1 Goombas
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
        pygame.display.set_caption("Super Mario Bros – Python Edition (Optimized with SMB1 Engine)")
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

        self.load_level(self.current_level_index)

    def load_level(self, level_index):
        self.all_sprites.empty()
        self.platforms.empty()
        self.enemies.empty()

        self.scroll = 0
        layout = LEVELS[level_index]
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
                    self.flag_rect = pygame.Rect(world_x, world_y - TILE_SIZE, TILE_SIZE, TILE_SIZE * 2)

        # Default player if not found (fallback, though now unnecessary)
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
                    if self.player.vel_y < -8:  # SMB1-like jump cut for variable height
                        self.player.vel_y = -8

        keys = pygame.key.get_pressed()
        self.player.input_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.input_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.input_dir += 1

    def update(self):
        died = self.player.update(self.platforms)
        if died:
            self.load_level(self.current_level_index)
            return

        for enemy in self.enemies:
            enemy.update(self.platforms)
            if self.player.rect.colliderect(enemy.rect):
                if self.player.vel_y > 0 and self.player.rect.bottom < enemy.rect.centery:
                    enemy.kill()
                    self.player.vel_y = PLAYER_JUMP_STRENGTH / 2
                else:
                    self.load_level(self.current_level_index)
                    return

        # Scroll camera
        if self.player.rect.right > SCREEN_WIDTH / 2 and self.scroll + SCREEN_WIDTH < self.level_width:
            diff = self.player.rect.right - SCREEN_WIDTH / 2
            self.player.rect.right = SCREEN_WIDTH / 2
            self.scroll += diff

        if self.flag_rect and self.player.rect.colliderect(self.flag_rect):
            self.current_level_index += 1
            if self.current_level_index < len(LEVELS):
                self.load_level(self.current_level_index)
            else:
                print("YOU WIN!")
                self.running = False

    def draw(self):
        self.screen.fill(SKY_BLUE)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, (sprite.rect.x - self.scroll, sprite.rect.y))
        if self.flag_rect:
            flag_pos = (self.flag_rect.x - self.scroll, self.flag_rect.y)
            pygame.draw.rect(self.screen, GREEN, (*flag_pos, TILE_SIZE, TILE_SIZE * 2))
            pygame.draw.polygon(
                self.screen, RED,
                [(flag_pos[0] + 5, flag_pos[1]), (flag_pos[0] + TILE_SIZE - 5, flag_pos[1] + 15),
                 (flag_pos[0] + 5, flag_pos[1] + 30)]
            )

        font = pygame.font.Font(None, 36)
        level_text = font.render(f"Level: {self.current_level_index + 1}", True, BLACK)
        self.screen.blit(level_text, (10, 10))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
