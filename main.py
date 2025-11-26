import pygame
import sys
import random

# --- Initialization ---
pygame.init()
pygame.mixer.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TILE_SIZE = 50

# Physics
GRAVITY = 0.8
PLAYER_SPEED = 5
JUMP_FORCE = -16
ENEMY_SPEED = 2

# Assets Path
ASSET_PATH = "assets/"

# --- Load Images ---
IMAGES = {
    "player_small": pygame.image.load(f"{ASSET_PATH}medha.png").convert_alpha(),
    "player_big": pygame.image.load(f"{ASSET_PATH}medha_big.png").convert_alpha(),
    "enemy": pygame.image.load(f"{ASSET_PATH}goomba.png").convert_alpha(),
    "brick": pygame.image.load(f"{ASSET_PATH}brick.png").convert_alpha(),
    "pipe": pygame.image.load(f"{ASSET_PATH}pipe.png").convert_alpha(),
    "mushroom": pygame.image.load(f"{ASSET_PATH}mushroom.png").convert_alpha(),
    "star": pygame.image.load(f"{ASSET_PATH}star.png").convert_alpha(),
    "flag": pygame.image.load(f"{ASSET_PATH}flag.png").convert_alpha(),
    "coin": pygame.image.load(f"{ASSET_PATH}coin.png").convert_alpha(),
    "plant": pygame.image.load(f"{ASSET_PATH}plant.png").convert_alpha(),
    "question": pygame.image.load(f"{ASSET_PATH}questionmark.png").convert_alpha(),
    "cloud": pygame.image.load(f"{ASSET_PATH}cloud.png").convert_alpha()
}

# --- Load Sounds (placeholder) ---
SOUNDS = {
    "jump": pygame.mixer.Sound(pygame.mixer.Sound(pygame.mixer.get_init())),
    "coin": pygame.mixer.Sound(pygame.mixer.Sound(pygame.mixer.get_init())),
    "powerup": pygame.mixer.Sound(pygame.mixer.Sound(pygame.mixer.get_init())),
    "hit": pygame.mixer.Sound(pygame.mixer.Sound(pygame.mixer.get_init())),
    "level_clear": pygame.mixer.Sound(pygame.mixer.Sound(pygame.mixer.get_init())),
    "bgm": pygame.mixer.Sound(pygame.mixer.Sound(pygame.mixer.get_init()))
}

# --- Base Level Template ---
BASE_LEVEL = [
    "                                                                                ",
    "                                                                                ",
    "                                                                            F   ",
    "                                                                            F   ",
    "                       M                   S                                F   ",
    "                     WWWWW               WWWWW                              F   ",
    "                                                                   E        F   ",
    "         E                     E    P                 P          WWWWW    WWWWW ",
    "      WWWWWWW                WWWWWW P                 P                         ",
    "                  P                 P                 P                         ",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
]

# --- Classes ---
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.x + SCREEN_WIDTH // 2
        x = min(0, x)
        x = max(-(self.width - SCREEN_WIDTH), x)
        self.camera = pygame.Rect(x, 0, self.width, self.height)


class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = 0
        self.vy = 0


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, IMAGES["player_small"])
        self.is_jumping = False
        self.is_big = False
        self.is_invincible = False
        self.invincible_timer = 0
        self.score = 0

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.vx = PLAYER_SPEED
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            if not self.is_jumping:
                self.vy = JUMP_FORCE
                self.is_jumping = True
                SOUNDS["jump"].play()

    def power_up(self, type):
        if type == "mushroom" and not self.is_big:
            self.is_big = True
            self.score += 100
            old_bottom = self.rect.bottom
            self.image = IMAGES["player_big"]
            self.rect = self.image.get_rect()
            self.rect.x = self.x_pos_temp
            self.rect.bottom = old_bottom
            SOUNDS["powerup"].play()
        elif type == "star":
            self.is_invincible = True
            self.invincible_timer = FPS * 10
            self.score += 500
            SOUNDS["powerup"].play()

    def take_damage(self):
        if self.is_big:
            self.is_big = False
            self.image = IMAGES["player_small"]
            self.rect = self.image.get_rect()
            self.is_invincible = True
            self.invincible_timer = FPS * 2
            SOUNDS["hit"].play()
            return False
        else:
            SOUNDS["hit"].play()
            return True

    def update(self, platforms):
        self.get_input()
        self.vy += GRAVITY
        self.rect.y += self.vy

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vy > 0:
                    self.rect.bottom = platform.rect.top
                    self.vy = 0
                    self.is_jumping = False
                elif self.vy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vy = 0

        self.rect.x += self.vx
        self.x_pos_temp = self.rect.x

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vx > 0:
                    self.rect.right = platform.rect.left
                elif self.vx < 0:
                    self.rect.left = platform.rect.right

        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False


class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, IMAGES["enemy"])
        self.vx = -ENEMY_SPEED

    def update(self, platforms):
        self.vy += GRAVITY
        self.rect.y += self.vy
        for platform in platforms:
            if self.rect.colliderect(platform.rect) and self.vy > 0:
                self.rect.bottom = platform.rect.top
                self.vy = 0
        self.rect.x += self.vx
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.vx *= -1
                self.rect.x += self.vx


class Item(Entity):
    def __init__(self, x, y, type):
        image = IMAGES[type]
        super().__init__(x, y, image)
        self.type = type


# --- Menu & UI Functions ---
def draw_text(surface, text, size, x, y, color=(255, 255, 255)):
    font = pygame.font.SysFont("Arial", size, bold=True)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.center = (x, y)
    surface.blit(text_surface, text_rect)


def start_menu(screen):
    colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0),
              (0, 0, 255), (75, 0, 130), (148, 0, 211)]
    menu_options = ["Start Game", "Load Game", "Settings", "Exit"]
    selected = 0
    clock = pygame.time.Clock()
    running = True
    color_index = 0
    while running:
        screen.fill((107, 140, 255))
        color_index = (color_index + 1) % len(colors)
        draw_text(screen, "RUN MEDHA RUN", 80, SCREEN_WIDTH//2, 100, colors[color_index])
        for i, option in enumerate(menu_options):
            color = (255, 255, 0) if i == selected else (255, 255, 255)
            draw_text(screen, option, 50, SCREEN_WIDTH//2, 250 + i*70, color)
        pygame.display.flip()
        clock.tick(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(menu_options)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    if menu_options[selected] == "Start Game":
                        return "start"
                    elif menu_options[selected] == "Load Game":
                        return "load"
                    elif menu_options[selected] == "Settings":
                        return "settings"
                    elif menu_options[selected] == "Exit":
                        pygame.quit()
                        sys.exit()


# --- Level Functions ---
def build_level(level_template, all_sprites, platforms, enemies, items):
    level_width = len(level_template[0]) * TILE_SIZE
    for r, row in enumerate(level_template):
        for c, char in enumerate(row):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            if char == "W":
                p = Entity(x, y, IMAGES["brick"])
                platforms.add(p)
                all_sprites.add(p)
            elif char == "P":
                p = Entity(x, y, IMAGES["pipe"])
                platforms.add(p)
                all_sprites.add(p)
            elif char == "E":
                e = Enemy(x, y)
                enemies.add(e)
                all_sprites.add(e)
            elif char == "M":
                i = Item(x, y, "mushroom")
                items.add(i)
                all_sprites.add(i)
            elif char == "S":
                i = Item(x, y, "star")
                items.add(i)
                all_sprites.add(i)
            elif char == "F":
                f = Entity(x, y, IMAGES["flag"])
                platforms.add(f)
                all_sprites.add(f)
    return level_width


def generate_level():
    new_level = []
    for row in BASE_LEVEL:
        new_row = ""
        for char in row:
            if char == "E" and random.random() < 0.5:
                new_row += "E"
            elif char == "M" and random.random() < 0.5:
                new_row += "M"
            elif char == "S" and random.random() < 0.3:
                new_row += "S"
            else:
                new_row += char
        new_level.append(new_row)
    return new_level


# --- Main Game ---
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("RUN MEDHA RUN")
    player = Player(100, 100)

    # Play BGM
    # SOUNDS["bgm"].play(-1)

    # Start Menu
    start_menu(screen)

    level_number = 1
    while True:
        all_sprites = pygame.sprite.Group()
        platforms = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        items = pygame.sprite.Group()
        all_sprites.add(player)

        level_map = generate_level()
        level_width = build_level(level_map, all_sprites, platforms, enemies, items)
        camera = Camera(level_width, SCREEN_HEIGHT)

        level_running = True
        clock = pygame.time.Clock()
        while level_running:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            player.update(platforms)
            camera.update(player)

            for e in enemies:
                e.update(platforms)

            hit_item = pygame.sprite.spritecollide(player, items, True)
            for item in hit_item:
                player.power_up(item.type)
                SOUNDS["coin"].play()

            for enemy in enemies:
                if player.rect.colliderect(enemy.rect):
                    if player.vy > 0 and player.rect.bottom < enemy.rect.centery + 15:
                        enemy.kill()
                        player.vy = -10
                        player.score += 100
                    elif not player.is_invincible:
                        dead = player.take_damage()
                        if dead:
                            draw_text(screen, "GAME OVER", 60, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, (255, 0, 0))
                            pygame.display.flip()
                            pygame.time.wait(3000)
                            pygame.quit()
                            sys.exit()

            if player.rect.x > level_width - 250:
                draw_text(screen, f"LEVEL {level_number} CLEARED!", 60, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, (0, 255, 0))
                pygame.display.flip()
                pygame.time.wait(2000)
                player.rect.x = 100
                level_number += 1
                level_running = False

            screen.fill((107, 140, 255))
            for sprite in all_sprites:
                screen.blit(sprite.image, camera.apply(sprite))
            draw_text(screen, f"Score: {player.score}", 30, 80, 20, (0, 0, 0))
            draw_text(screen, f"Level: {level_number}", 30, 700, 20, (0, 0, 0))
            pygame.display.flip()


if __name__ == "__main__":
    main()
