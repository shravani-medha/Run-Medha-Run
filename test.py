import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Test Screen")

# Load a single asset
medha_img = pygame.image.load("assets/medha.png").convert_alpha()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((135, 206, 235))  # sky blue
    screen.blit(medha_img, (100, 400))
    pygame.display.update()

pygame.quit()
sys.exit()
