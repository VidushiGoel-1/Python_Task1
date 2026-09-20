import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Split Control")
clock = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
BG_COLOR = (20, 20, 30)
PLAYER1_COLOR = (80, 200, 255)     # left room character
PLAYER2_COLOR = (255, 150, 80)     # right room character
OBSTACLE_COLOR = (200, 60, 60)
DIVIDER_COLOR = (60, 60, 70)

SPEED = 4
score = 0
lives = 5
INVINCIBLE_FRAMES = 90
invincible_timer = 0
DIFFICULTY_STEP = 50
next_difficulty_score = DIFFICULTY_STEP
MAX_OBSTACLES = 6
SAFE_SPAWN_DISTANCE = 100
font = pygame.font.SysFont(None, 36)

# ---------------------------------------------------------------------------
# Two separate "rooms" side by side on the same screen
# Left half = room 1, right half = room 2
# ---------------------------------------------------------------------------
ROOM1_X_RANGE = (0, WIDTH // 2 - 5)
ROOM2_X_RANGE = (WIDTH // 2 + 5, WIDTH)

player1 = pygame.Rect(50, 50, 40, 40)
player2 = pygame.Rect(WIDTH // 2 + 50, 50, 40, 40)

# Obstacles are DIFFERENT in each room -> forces a path that works for both
# Each entry is [rect, dx, dy] so obstacles can move and bounce off walls
obstacles1 = [
    [pygame.Rect(150, 150, 120, 20), 3, 0],
    [pygame.Rect(100, 300, 20, 120), 0, 2],
]

obstacles2 = [
    [pygame.Rect(WIDTH // 2 + 200, 100, 20, 150), 0, -2],
    [pygame.Rect(WIDTH // 2 + 300, 350, 150, 20), -3, 0],
]


def move_player(rect, dx, dy, x_bounds):
    """Move a player rect by (dx, dy), clamped to its room bounds."""
    new_rect = rect.move(dx, dy)

    new_rect.left = max(x_bounds[0], new_rect.left)
    new_rect.right = min(x_bounds[1], new_rect.right)
    new_rect.top = max(0, new_rect.top)
    new_rect.bottom = min(HEIGHT, new_rect.bottom)

    return new_rect


def check_collision(rect, obstacles):
    for obs_data in obstacles:
        if rect.colliderect(obs_data[0]):
            return True
    return False


def add_obstacle(obstacles, x_bounds, player_rect):
    """Add one new obstacle, capped at MAX_OBSTACLES, spawned away from the player."""
    if len(obstacles) >= MAX_OBSTACLES:
        return

    for _ in range(10):  # try a few times to find a safe spot
        x = random.randint(x_bounds[0] + 20, x_bounds[1] - 40)
        y = random.randint(20, HEIGHT - 40)
        candidate = pygame.Rect(x, y, 60, 20)
        if candidate.colliderect(player_rect.inflate(SAFE_SPAWN_DISTANCE, SAFE_SPAWN_DISTANCE)):
            continue  # too close to player, try again
        dx = random.choice([-3, -2, 2, 3])
        dy = random.choice([-3, -2, 2, 3])
        obstacles.append([candidate, dx, dy])
        return


def update_obstacles(obstacles, x_bounds):
    """Move each obstacle by its own (dx, dy) and bounce it off room edges."""
    for obs_data in obstacles:
        rect, dx, dy = obs_data
        rect.x += dx
        rect.y += dy

        # bounce off the room's horizontal edges
        if rect.left <= x_bounds[0] or rect.right >= x_bounds[1]:
            obs_data[1] *= -1
        # bounce off the top/bottom edges
        if rect.top <= 0 or rect.bottom >= HEIGHT:
            obs_data[2] *= -1


def draw_room_divider():
    pygame.draw.line(screen, DIVIDER_COLOR, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 3)


def draw_everything(game_over, score, lives):
    screen.fill(BG_COLOR)
    draw_room_divider()

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    lives_text = font.render(f"Lives: {lives}", True, (255, 255, 255))
    screen.blit(lives_text, (10, 45))

    for obs_data in obstacles1:
        pygame.draw.rect(screen, OBSTACLE_COLOR, obs_data[0])
    for obs_data in obstacles2:
        pygame.draw.rect(screen, OBSTACLE_COLOR, obs_data[0])

    pygame.draw.rect(screen, PLAYER1_COLOR, player1)
    pygame.draw.rect(screen, PLAYER2_COLOR, player2)

    if game_over:
        over_font = pygame.font.SysFont(None, 60)
        text = over_font.render("GAME OVER", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 60))

        sub_font = pygame.font.SysFont(None, 36)
        sub_text = sub_font.render(f"Score: {score}  -  Press R to Restart", True, (255, 255, 255))
        screen.blit(sub_text, (WIDTH // 2 - sub_text.get_width() // 2, HEIGHT // 2))

    pygame.display.update()


def reset_game():
    global player1, player2, obstacles1, obstacles2, score, lives, invincible_timer, next_difficulty_score
    player1 = pygame.Rect(50, 50, 40, 40)
    player2 = pygame.Rect(WIDTH // 2 + 50, 50, 40, 40)
    obstacles1 = [
        [pygame.Rect(150, 150, 120, 20), 3, 0],
        [pygame.Rect(100, 300, 20, 120), 0, 2],
    ]
    obstacles2 = [
        [pygame.Rect(WIDTH // 2 + 200, 100, 20, 150), 0, -2],
        [pygame.Rect(WIDTH // 2 + 300, 350, 150, 20), -3, 0],
    ]
    score = 0
    lives = 5
    invincible_timer = 0
    next_difficulty_score = DIFFICULTY_STEP


def reset_positions():
    global player1, player2, invincible_timer
    player1 = pygame.Rect(50, 50, 40, 40)
    player2 = pygame.Rect(WIDTH // 2 + 50, 50, 40, 40)
    invincible_timer = INVINCIBLE_FRAMES


def main():
    global player1, player2, score, lives, invincible_timer, next_difficulty_score
    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    reset_game()
                    game_over = False

        if not game_over:
            if invincible_timer > 0:
                invincible_timer -= 1

            # Obstacles drift and bounce on their own, every frame
            update_obstacles(obstacles1, ROOM1_X_RANGE)
            update_obstacles(obstacles2, ROOM2_X_RANGE)

            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT]:
                dx = -SPEED
            if keys[pygame.K_RIGHT]:
                dx = SPEED
            if keys[pygame.K_UP]:
                dy = -SPEED
            if keys[pygame.K_DOWN]:
                dy = SPEED

            if dx != 0 or dy != 0:
                score += 1

            if score >= next_difficulty_score:
                add_obstacle(obstacles1, ROOM1_X_RANGE, player1)
                add_obstacle(obstacles2, ROOM2_X_RANGE, player2)
                next_difficulty_score += DIFFICULTY_STEP

            # SAME input applied to BOTH players - this is the core mechanic
            player1 = move_player(player1, dx, dy, ROOM1_X_RANGE)
            player2 = move_player(player2, dx, dy, ROOM2_X_RANGE)

            if invincible_timer == 0 and (
                check_collision(player1, obstacles1) or check_collision(player2, obstacles2)
            ):
                lives -= 1
                if lives <= 0:
                    game_over = True
                else:
                    reset_positions()

        draw_everything(game_over, score, lives)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()