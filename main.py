import pygame
import sys

# --- Initialization ---
pygame.init()

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
SKY_BLUE = (107, 140, 255)
BRICK_RED = (200, 76, 12)
PIPE_GREEN = (0, 168, 0)
GOOMBA_BROWN = (160, 82, 45)
MEDHA_COLOR = (255, 105, 180) # Hot Pink
MUSHROOM_COLOR = (255, 0, 0)  # Red
STAR_COLOR = (255, 215, 0)    # Gold
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Physics Settings
GRAVITY = 0.8
PLAYER_SPEED = 5
JUMP_FORCE = -16
ENEMY_SPEED = 2

# --- Level Design (Map) ---
# W = Ground/Brick, P = Pipe, M = Mushroom, S = Star, E = Enemy, F = Flag
LEVEL_MAP = [
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
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
]

TILE_SIZE = 50

# --- Classes ---

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Center the camera on the player
        x = -target.rect.x + int(SCREEN_WIDTH / 2)
        
        # Stop camera from scrolling past the start or end of the level
        x = min(0, x) 
        x = max(-(self.width - SCREEN_WIDTH), x)
        
        self.camera = pygame.Rect(x, 0, self.width, self.height)

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, color, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = 0
        self.vy = 0

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, MEDHA_COLOR, 30, 40)
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

    def power_up(self, type):
        if type == 'mushroom':
            self.is_big = True
            self.score += 100
            # Grow logic
            self.image = pygame.Surface([30, 60])
            self.image.fill(MEDHA_COLOR)
            # Adjust position so she grows UP, not into the floor
            old_bottom = self.rect.bottom
            self.rect = self.image.get_rect()
            self.rect.x = self.x_pos_temp
            self.rect.bottom = old_bottom
        
        if type == 'star':
            self.is_invincible = True
            self.invincible_timer = 600 # 10 seconds (60fps * 10)
            self.score += 500

    def take_damage(self):
        if self.is_big:
            self.is_big = False
            self.image = pygame.Surface([30, 40])
            self.image.fill(MEDHA_COLOR)
            self.rect = self.image.get_rect()
            self.is_invincible = True # Temporary mercy invincibility
            self.invincible_timer = 120 # 2 seconds
            return False # Still alive
        else:
            return True # Dead

    def update(self, platforms):
        self.get_input()
        
        # Apply Gravity
        self.vy += GRAVITY
        self.rect.y += self.vy
        
        # Y Collision (Floor/Ceiling)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vy > 0: # Falling
                    self.rect.bottom = platform.rect.top
                    self.vy = 0
                    self.is_jumping = False
                elif self.vy < 0: # Hit head
                    self.rect.top = platform.rect.bottom
                    self.vy = 0

        self.rect.x += self.vx
        self.x_pos_temp = self.rect.x 

        # X Collision (Walls)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vx > 0: # Right
                    self.rect.right = platform.rect.left
                elif self.vx < 0: # Left
                    self.rect.left = platform.rect.right

        # Powerup Effects
        if self.is_invincible:
            self.invincible_timer -= 1
            if self.invincible_timer % 10 < 5: # Flashing effect
                self.image.fill(WHITE)
            else:
                self.image.fill(STAR_COLOR if self.type == 'star' else MEDHA_COLOR)
            
            if self.invincible_timer <= 0:
                self.is_invincible = False
                self.image.fill(MEDHA_COLOR)

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, GOOMBA_BROWN, 40, 40)
        self.vx = -ENEMY_SPEED

    def update(self, platforms):
        self.vy += GRAVITY
        self.rect.y += self.vy
        
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vy > 0:
                    self.rect.bottom = platform.rect.top
                    self.vy = 0

        self.rect.x += self.vx
        
        # Bounce off walls
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.vx *= -1
                self.rect.x += self.vx

class Item(Entity):
    def __init__(self, x, y, type):
        color = MUSHROOM_COLOR if type == 'mushroom' else STAR_COLOR
        super().__init__(x, y, color, 30, 30)
        self.type = type

# --- Main Game Functions ---

def draw_text(surface, text, size, x, y, color=WHITE):
    font = pygame.font.SysFont('Arial', size, bold=True)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Run-Medha-Run (Super Mario Style)")
    clock = pygame.time.Clock()

    # Sprite Groups
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    items = pygame.sprite.Group()
    
    player = Player(100, 100)
    all_sprites.add(player)

    # Build Level
    level_width = len(LEVEL_MAP[0]) * TILE_SIZE
    for r, row in enumerate(LEVEL_MAP):
        for c, char in enumerate(row):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            if char == "W":
                p = Entity(x, y, BRICK_RED, TILE_SIZE, TILE_SIZE)
                platforms.add(p)
                all_sprites.add(p)
            elif char == "P":
                p = Entity(x, y, PIPE_GREEN, TILE_SIZE, TILE_SIZE)
                platforms.add(p)
                all_sprites.add(p)
            elif char == "E":
                e = Enemy(x, y)
                enemies.add(e)
                all_sprites.add(e)
            elif char == "M":
                i = Item(x, y, 'mushroom')
                items.add(i)
                all_sprites.add(i)
            elif char == "S":
                i = Item(x, y, 'star')
                items.add(i)
                all_sprites.add(i)
            elif char == "F":
                # Flag pole
                f = Entity(x, y, WHITE, 10, TILE_SIZE)
                platforms.add(f)
                all_sprites.add(f)

    camera = Camera(level_width, SCREEN_HEIGHT)
    running = True

    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Update ---
        player.update(platforms)
        camera.update(player)
        
        for e in enemies:
            e.update(platforms)

        # Item Collision
        hit_item = pygame.sprite.spritecollide(player, items, True)
        for item in hit_item:
            player.power_up(item.type)

        # Enemy Collision
        for enemy in enemies:
            if player.rect.colliderect(enemy.rect):
                # Kill Enemy (Jump on top)
                if player.vy > 0 and player.rect.bottom < enemy.rect.centery + 15:
                    enemy.kill()
                    player.vy = -10 # Bounce
                    player.score += 100
                else:
                    # Player Hit
                    if not player.is_invincible:
                        dead = player.take_damage()
                        if dead:
                            print("GAME OVER")
                            running = False

        # Win Condition (Reached end of map)
        if player.rect.x > level_width - 250:
            draw_text(screen, "LEVEL CLEARED!", 60, SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
            continue

        # --- Draw ---
        screen.fill(SKY_BLUE)
        
        # Draw all sprites adjusted by camera
        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))
            
        # Draw Score (Static UI)
        draw_text(screen, f"Score: {player.score}", 30, 80, 20, BLACK)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
