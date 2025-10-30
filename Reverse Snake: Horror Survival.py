import pygame
import random
import sys
import os
import time
import math

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
TILE = 20
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reverse Snake: Horror Survival")

clock = pygame.time.Clock()
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 28)

BLACK = (0, 0, 0)
RED = (220, 0, 0)
BLOOD = (150, 0, 0)
GREEN = (0, 180, 0)
DARK_GREEN = (0, 100, 0)
DARK_RED = (90, 0, 0)
SNAKE_HEAD = (255, 60, 60)
WHITE = (255, 255, 255)

def play_bite():
    os.system("aplay /usr/share/sounds/freedesktop/stereo/dialog-warning.oga >/dev/null 2>&1 &")

def play_victory():
    os.system("aplay /usr/share/sounds/freedesktop/stereo/complete.oga >/dev/null 2>&1 &")

def play_gameover():
    os.system("aplay /usr/share/sounds/freedesktop/stereo/dialog-error.oga >/dev/null 2>&1 &")

particles = []
def spawn_blood(x, y, color=BLOOD):
    for _ in range(10):
        particles.append({
            "x": x + TILE//2,
            "y": y + TILE//2,
            "vx": random.uniform(-2, 2),
            "vy": random.uniform(-2, 2),
            "life": random.randint(20, 40),
            "color": color
        })

def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)
        else:
            alpha = max(0, min(255, int(255 * (p["life"] / 40))))
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            s.fill((*p["color"], alpha))
            screen.blit(s, (p["x"], p["y"]))

class Snake:
    def __init__(self):
        self.body = [(WIDTH//2, HEIGHT//2)]
        self.length = 5
        self.speed = TILE
        self.dir = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])

    def move(self):
        head_x, head_y = self.body[0]
        if self.dir == "UP": head_y -= self.speed
        if self.dir == "DOWN": head_y += self.speed
        if self.dir == "LEFT": head_x -= self.speed
        if self.dir == "RIGHT": head_x += self.speed

        if head_x < 0 or head_x >= WIDTH or head_y < 0 or head_y >= HEIGHT:
            return

        new_head = (head_x, head_y)
        self.body.insert(0, new_head)
        if len(self.body) > self.length:
            self.body.pop()

    def draw(self):
        for i, (x, y) in enumerate(self.body):
            if i == 0:
                pygame.draw.circle(screen, SNAKE_HEAD, (x + TILE//2, y + TILE//2), TILE//2)
                pygame.draw.circle(screen, (255, 50, 50, 20), (x + TILE//2, y + TILE//2), TILE, 1)
            else:
                pygame.draw.rect(screen, DARK_RED, (x, y, TILE, TILE))

    def chase(self, target):
        head_x, head_y = self.body[0]
        tx, ty = target
        if abs(tx - head_x) > abs(ty - head_y):
            self.dir = "RIGHT" if tx > head_x else "LEFT"
        else:
            self.dir = "DOWN" if ty > head_y else "UP"

    def collides_with(self, rect):
        for (x, y) in self.body:
            if rect.colliderect(pygame.Rect(x, y, TILE, TILE)):
                return True
        return False

class Apple:
    def __init__(self, color, player=False):
        self.x = random.randrange(0, WIDTH // TILE) * TILE
        self.y = random.randrange(0, HEIGHT // TILE) * TILE
        self.color = color
        self.alive = True
        self.move_timer = 0
        self.is_player = player

    def rect(self):
        return pygame.Rect(self.x, self.y, TILE, TILE)

    def draw(self):
        if not self.alive:
            return
        pygame.draw.circle(screen, self.color, (self.x + TILE//2, self.y + TILE//2), TILE//2)
        pygame.draw.rect(screen, (90, 40, 0), (self.x + TILE//2 - 2, self.y - 5, 4, 6))

    def move(self, keys=None):
        if not self.alive:
            return

        dx, dy = 0, 0
        if self.is_player and keys:
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -TILE
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = TILE
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -TILE
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = TILE
        else:
            self.move_timer += 1
            if self.move_timer > 25:
                self.move_timer = 0
                dx, dy = random.choice([(TILE, 0), (-TILE, 0), (0, TILE), (0, -TILE), (0, 0)])

        new_x = self.x + dx
        new_y = self.y + dy

        if 0 <= new_x < WIDTH and 0 <= new_y < HEIGHT:
            self.x, self.y = new_x, new_y

snake = Snake()
player = Apple(RED, player=True)
ai_apples = [Apple(GREEN) for _ in range(5)]

START_TIME = time.time()
SURVIVE_TIME = 100

game_over = False
victory = False

while True:
    screen.fill(BLACK)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    if not game_over:
        old_x, old_y = player.x, player.y
        player.move(keys)
        if snake.collides_with(player.rect()):
            player.x, player.y = old_x, old_y

        for a in ai_apples:
            a.move()

        targets = [a for a in ai_apples if a.alive] + ([player] if player.alive else [])
        if targets:
            target = min(targets, key=lambda t: abs(t.x - snake.body[0][0]) + abs(t.y - snake.body[0][1]))
            snake.chase((target.x, target.y))

        snake.move()

        for a in ai_apples:
            if a.alive and (snake.body[0][0] == a.x and snake.body[0][1] == a.y):
                a.alive = False
                spawn_blood(a.x, a.y)
                snake.length += 2
                play_bite()
                ai_apples.append(Apple(GREEN))

        if player.alive and (snake.body[0][0] == player.x and snake.body[0][1] == player.y):
            spawn_blood(player.x, player.y)
            player.alive = False
            play_gameover()
            game_over = True
            victory = False

        elapsed = time.time() - START_TIME
        if elapsed >= SURVIVE_TIME and player.alive:
            play_victory()
            victory = True
            game_over = True

    snake.draw()
    for a in ai_apples:
        a.draw()
    player.draw()
    update_particles()

    elapsed = time.time() - START_TIME
    remaining = max(0, SURVIVE_TIME - elapsed)
    timer_text = small_font.render(f"Survive: {int(remaining)}s", True, WHITE)
    screen.blit(timer_text, (10, 10))

    if game_over:
        msg = "You Survived!" if victory else "You Were Eaten!"
        text = font.render(msg, True, WHITE)
        sub = small_font.render("Press R to Restart or ESC to Quit", True, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 40))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))

        if keys[pygame.K_r]:
            snake = Snake()
            player = Apple(RED, player=True)
            ai_apples = [Apple(GREEN) for _ in range(5)]
            particles.clear()
            START_TIME = time.time()
            game_over = False
            victory = False
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            sys.exit()

    pygame.display.flip()
    clock.tick(10)
