import os
os.environ["PYGBAG_NO_ARCHIVE"] = "1"  # Skip APK archive for pygbag/web build

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

# Paths
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")

# --- Load Images ---
BRICK_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "brick.png")).convert_alpha()
PIPE_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "pipe.png")).convert_alpha()
GOOMBA_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "goomba.png")).convert_alpha()
MEDHA_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "medha.png")).convert_alpha()
MEDHA_BIG_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "medha_big.png")).convert_alpha()
MUSHROOM_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "mushroom.png")).convert_alpha()
STAR_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "coin.png")).convert_alpha()
FLAG_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "flag.png")).convert_alpha()
CLOUD_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "cloud.png")).convert_alpha()
QUESTIONMARK_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "questionmark.png")).convert_alpha()
PLANT_IMG = pygame.image.load(os.path.join(ASSETS_PATH, "plant.png")).convert_alpha()

# --- Load Sounds (.ogg for web) ---
JUMP_SOUND = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "jump.ogg")) if os.path.exists(os.path.join(ASSETS_PATH, "jump.ogg")) else None
COIN_SOUND = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "coin.ogg")) if os.path.exists(os.path.join(ASSETS_PATH, "coin.ogg")) else None
POWERUP_SOUND = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "powerup.ogg")) if os.path.exists(os.path.join(ASSETS_PATH, "powerup.ogg")) else None
HIT_SOUND = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "hit.ogg")) if os.path.exists(os.path.join(ASSETS_PATH, "hit.ogg")) else None

# --- Physics Settings ---
GRAVITY = 0.8
PLAYER_SPEED = 5
JUMP_FORCE = -16
ENEMY_SPEED = 2

# --- Camera ---
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

# --- Game Entities ---
class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vx = 0
        self.vy = 0

class Player(Entity):
    def __init__(self, x, y, img_small, img_big):
        super().__init__(x, y, img_small)
        self.img_small = img_small
        self.img_big = img_big
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
        if keys[pygame.K_UP] or keys[pygame.K_SPACE]:
            if not self.is_jumping:
                self.vy = JUMP_FORCE
                self.is_jumping = True
                if JUMP_SOUND: JUMP_SOUND.play()

    def power_up(self, type):
        if type == 'mushroom':
            self.is_big = True
            self.image = self.img_big
            self.score += 100
            if POWERUP_SOUND: POWERUP_SOUND.play()
        elif type == 'star':
            self.is_invincible = True
            self.invincible_timer = FPS * 10
            self.score += 500
            if POWERUP_SOUND: POWERUP_SOUND.play()

    def take_damage(self):
        if self.is_big:
            self.is_big = False
            self.image = self.img_small
            self.is_invincible = True
            self.invincible_timer = FPS * 2
            return False
        else:
            return True

    def update(self, platforms):
        self.get_input()
        self.vy += GRAVITY
        self.rect.y += self.vy

        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vy > 0:
                    self.rect.bottom = plat.rect.top
                    self.vy = 0
                    self.is_jumping = False
                elif self.vy < 0:
                    self.rect.top = plat.rect.bottom
                    self.vy = 0

        self.rect.x += self.vx
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.rect.right = plat.rect.left
                elif self.vx < 0:
                    self.rect.left = plat.rect.right

        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.is_invincible = False

class Enemy(Entity):
    def __init__(self, x, y, image):
        super().__init__(x, y, image)
        self.vx = -ENEMY_SPEED

    def update(self, platforms):
        self.vy += GRAVITY
        self.rect.y += self.vy
        for plat in platforms:
            if self.rect.colliderect(plat.rect) and self.vy > 0:
                self.rect.bottom = plat.rect.top
                self.vy = 0
        self.rect.x += self.vx
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                self.vx *= -1
                self.rect.x += self.vx

class Item(Entity):
    def __init__(self, x, y, type, image):
        super().__init__(x, y, image)
        self.type = type

# --- UI ---
def draw_text(surface, text, size, x, y, color):
    font = pygame.font.SysFont('Arial', size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y))
    surface.blit(surf, rect)

def start_menu(screen):
    colors = [(255,0,0),(0,255,0),(0,0,255),(255,255,0)]
    selected = 0
    menu_items = ["Start Game","Load Game","Settings","Exit"]
    clock = pygame.time.Clock()
    running = True
    while running:
        screen.fill((0,0,0))
        draw_text(screen, "RUN MEDHA RUN", 60, SCREEN_WIDTH//2, 80, colors[random.randint(0,3)])
        for i, item in enumerate(menu_items):
            color = (255,255,255) if i != selected else (255,215,0)
            draw_text(screen, item, 40, SCREEN_WIDTH//2, 200 + i*60, color)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(menu_items)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(menu_items)
                elif event.key == pygame.K_RETURN:
                    if menu_items[selected] == "Start Game": return
                    elif menu_items[selected] == "Exit": pygame.quit(); sys.exit()
        clock.tick(15)

# --- Infinite Level Generator ---
def generate_level(width=20, height=12):
    tiles = []
    for r in range(height):
        row = []
        for c in range(width):
            if r == height-1: row.append("W")
            elif random.random() < 0.02: row.append("P")
            elif random.random() < 0.03: row.append("E")
            elif random.random() < 0.03: row.append("M")
            elif random.random() < 0.02: row.append("S")
            else: row.append(" ")
        tiles.append("".join(row))
    # Add flag at end
    for r in range(height-3, height):
        tiles[r] = tiles[r][:-1] + "F"
    return tiles

# --- Main Game ---
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Run Medha Run")
    clock = pygame.time.Clock()

    start_menu(screen)

    level_count = 1
    running = True

    while running:
        LEVEL_MAP = generate_level(width=30 + level_count*5, height=12)
        level_width = len(LEVEL_MAP[0])*TILE_SIZE

        all_sprites = pygame.sprite.Group()
        platforms = pygame.sprite.Group()
        enemies = pygame.sprite.Group()
        items = pygame.sprite.Group()

        player = Player(100, 100, MEDHA_IMG, MEDHA_BIG_IMG)
        all_sprites.add(player)

        for r, row in enumerate(LEVEL_MAP):
            for c, char in enumerate(row):
                x, y = c*TILE_SIZE, r*TILE_SIZE
                if char=="W": p=Entity(x,y,BRICK_IMG); platforms.add(p); all_sprites.add(p)
                elif char=="P": p=Entity(x,y,PIPE_IMG); platforms.add(p); all_sprites.add(p)
                elif char=="E": e=Enemy(x,y,GOOMBA_IMG); enemies.add(e); all_sprites.add(e)
                elif char=="M": i=Item(x,y,'mushroom',MUSHROOM_IMG); items.add(i); all_sprites.add(i)
                elif char=="S": i=Item(x,y,'star',STAR_IMG); items.add(i); all_sprites.add(i)
                elif char=="F": f=Entity(x,y,FLAG_IMG); platforms.add(f); all_sprites.add(f)

        camera = Camera(level_width, SCREEN_HEIGHT)
        level_running = True

        while level_running:
            clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

            player.update(platforms)
            camera.update(player)

            for e in enemies:
                e.update(platforms)

            hit_item = pygame.sprite.spritecollide(player, items, True)
            for item in hit_item: player.power_up(item.type)

            for enemy in enemies:
                if player.rect.colliderect(enemy.rect):
                    if player.vy > 0 and player.rect.bottom < enemy.rect.centery:
                        enemy.kill()
                        player.vy = -10
                        player.score += 100
                        if COIN_SOUND: COIN_SOUND.play()
                    else:
                        if not player.is_invincible:
                            dead = player.take_damage()
                            if dead:
                                draw_text(screen,"GAME OVER",80,SCREEN_WIDTH//2,SCREEN_HEIGHT//2,(255,0,0))
                                pygame.display.flip()
                                pygame.time.wait(3000)
                                pygame.quit()
                                sys.exit()

            if player.rect.x > level_width - 250:
                draw_text(screen, f"LEVEL {level_count} CLEARED!", 60, SCREEN_WIDTH//2, SCREEN_HEIGHT//2,(0,255,0))
                pygame.display.flip()
                pygame.time.wait(2000)
                level_running = False
                level_count += 1

            screen.fill((107,140,255))  # Sky Blue
            for sprite in all_sprites:
                screen.blit(sprite.image, camera.apply(sprite))
            draw_text(screen,f"Score: {player.score}",30,80,20,(255,255,255))

            pygame.display.flip()

if __name__=="__main__":
    main()
