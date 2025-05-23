import pygame
import random
import os
import json
from pathlib import Path
import asyncio

# Inicialização
pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Steve Bird")
clock = pygame.time.Clock()
FPS = 60

# Configurações de jogo
BASE_GAP = 200
MIN_GAP = 120
PIPE_SPEED = 3
SPEED_INCREASE = 0.005
MAX_SPEED = 6
GRAVITY = 0.5
JUMP_FORCE = -8

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 235)
GREEN = (34, 139, 34)
RED = (255, 0, 0)
GOLD = (255, 215, 0)

# Carregamento de assets
def load_image(name, scale=1):
    try:
        path = os.path.join(os.path.dirname(__file__), name)
        image = pygame.image.load(path).convert_alpha()
        if scale != 1:
            size = image.get_size()
            image = pygame.transform.scale(image, (int(size[0]*scale), int(size[1]*scale)))
        return image
    except:
        print(f"Imagem '{name}' não encontrada. Criando substituto.")
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        if "steve" in name:
            pygame.draw.rect(surf, RED, (0, 0, 50, 50))
        elif "pipe" in name:
            surf = pygame.Surface((80, 300), pygame.SRCALPHA)
            pygame.draw.rect(surf, GREEN, (0, 0, 80, 300))
        elif "background" in name:
            surf = pygame.Surface((WIDTH, HEIGHT))
            surf.fill(BLUE)
        return surf

def load_sound(name):
    try:
        path = os.path.join(os.path.dirname(__file__), name)
        return pygame.mixer.Sound(path)
    except:
        print(f"Som '{name}' não encontrado. Continuando sem som.")
        return None

# Carrega assets
bg = load_image("background.png")
steve_img = load_image("steve.png", 0.8)
pipe_img = load_image("pipe.png", 1.0)
jump_sound = load_sound("jump.wav")
score_sound = load_sound("score.wav")
game_over_sound = load_sound("game_over.wav")

class Steve:
    def __init__(self):
        self.image = steve_img
        self.rect = self.image.get_rect(center=(100, HEIGHT//2))
        self.velocity = 0
        self.gravity = GRAVITY
        self.jump_power = JUMP_FORCE
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.velocity += self.gravity
        self.rect.y += self.velocity
        self.mask = pygame.mask.from_surface(self.image)

    def jump(self):
        self.velocity = self.jump_power
        if jump_sound:
            jump_sound.play()

    def draw(self):
        screen.blit(self.image, self.rect)

class Pipe:
    def __init__(self, score):
        self.gap = max(BASE_GAP - (score//10), MIN_GAP)
        self.speed = min(PIPE_SPEED + score*SPEED_INCREASE, MAX_SPEED)
        
        min_height = int(HEIGHT * 0.2)
        max_height = int(HEIGHT * 0.65)
        self.height = random.randint(min_height, max_height)
        
        self.top_img = pygame.transform.flip(pipe_img, False, True)
        self.top = self.top_img.get_rect(midbottom=(WIDTH, self.height - self.gap//2))
        
        bottom_y = self.height + self.gap//2
        if bottom_y < HEIGHT:
            self.bottom = pipe_img.get_rect(midtop=(WIDTH, bottom_y))
        else:
            self.bottom = pipe_img.get_rect(
                left=WIDTH,
                top=bottom_y,
                width=pipe_img.get_width(),
                height=HEIGHT - bottom_y
            )
        
        self.passed = False
        self.scored = False
        self.top_mask = pygame.mask.from_surface(self.top_img)
        self.bottom_mask = pygame.mask.from_surface(pipe_img)

    def move(self):
        self.top.x -= self.speed
        self.bottom.x -= self.speed

    def draw(self):
        screen.blit(self.top_img, self.top)
        if self.bottom.height != pipe_img.get_height():
            stretched_pipe = pygame.transform.scale(pipe_img, (self.bottom.width, self.bottom.height))
            screen.blit(stretched_pipe, self.bottom)
        else:
            screen.blit(pipe_img, self.bottom)

    def collide(self, player):
        offset_top = (self.top.x - player.rect.x, self.top.y - player.rect.y)
        offset_bottom = (self.bottom.x - player.rect.x, self.bottom.y - player.rect.y)
        return (player.mask.overlap(self.top_mask, offset_top) or 
                player.mask.overlap(self.bottom_mask, offset_bottom))

def draw_text(text, size, y, color=WHITE):
    font = pygame.font.SysFont("Arial", size, bold=True)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(WIDTH//2, y))
    screen.blit(text_surface, text_rect)

def draw_credits():
    font = pygame.font.SysFont("Arial", 14)
    credit_text = font.render("Feito por Rodrigo D. Barbaceli e Alana O. Barbaceli", True, WHITE)
    screen.blit(credit_text, (WIDTH - credit_text.get_width() - 10, HEIGHT - 20))

def show_screen(title, score=0, highscores=[]):
    if "Game Over" in title and game_over_sound:
        game_over_sound.play()
    
    while True:
        screen.blit(bg, (0, 0))
        draw_text(title, 48, 100, GOLD if "Flappy" in title else RED)
        
        if score > 0:
            draw_text(f"Pontuação: {score}", 36, 180)
        
        if highscores:
            draw_text("Melhores Pontuações:", 30, 260)
            for i, hs in enumerate(highscores[:3]):
                draw_text(f"{i+1}. {hs}", 28, 310 + i*40, 
                         GOLD if hs == score and score > 0 else WHITE)
        
        draw_text("Pressione ESPAÇO para jogar", 24, 500)
        draw_text("ESC para sair", 24, 540)
        draw_credits()
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False

def main_game():
    steve = Steve()
    pipes = []
    pipe_timer = 0
    score = 0
    running = True
    
    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return -1
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    steve.jump()
                if event.key == pygame.K_ESCAPE:
                    return -1
        
        steve.update()
        
        pipe_timer += 1
        if pipe_timer > max(60, 90 - score//5):
            pipes.append(Pipe(score))
            pipe_timer = 0
        
        for pipe in pipes[:]:
            pipe.move()
            
            if pipe.collide(steve):
                if game_over_sound:
                    game_over_sound.play()
                return score
            
            if not pipe.scored and pipe.top.right < steve.rect.left:
                pipe.scored = True
                score += 1
                if score_sound:
                    score_sound.play()
            
            if pipe.top.right < -100:
                pipes.remove(pipe)
        
        if steve.rect.top <= -50 or steve.rect.bottom >= HEIGHT + 50:
            if game_over_sound:
                game_over_sound.play()
            return score
        
        screen.blit(bg, (0, 0))
        for pipe in pipes:
            pipe.draw()
        steve.draw()
        
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        draw_credits()
        
        pygame.display.update()
    
    return score

def load_highscores():
    try:
        with open('highscores.json', 'r') as f:
            return json.load(f)
    except:
        return [0, 0, 0]

def save_highscores(scores):
    with open('highscores.json', 'w') as f:
        json.dump(sorted(scores, reverse=True)[:3], f)

def main():
    try:
        pygame.mixer.music.load(os.path.join(os.path.dirname(__file__), "background_music.mp3"))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
    except:
        print("Música de fundo não encontrada. Continuando sem música.")

    highscores = load_highscores()
    
    running = True
    while running:
        if not show_screen("Steve Bird", highscores=highscores):
            running = False
            continue
        
        score = main_game()
        
        if score == -1:
            running = False
            continue
        
        highscores.append(score)
        highscores = sorted(list(set(highscores)), reverse=True)[:3]
        save_highscores(highscores)
        
        if not show_screen("Game Over", score, highscores):
            running = False
    
    pygame.mixer.music.stop()
    pygame.quit()

if __name__ == "__main__":
    main()

async def main():
    # Inicializações
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Atualizações e renderizações
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)