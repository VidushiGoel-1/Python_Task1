import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Split Control")
clock = pygame.time.Clock()

# Colors
BG_COLOR = (20, 20, 30)
PLAYER1_COLOR = (80, 200, 255)     # left room character
PLAYER2_COLOR = (255, 150, 80)     # right room character
OBSTACLE_COLOR = (200, 60, 60)
EXIT_COLOR = (80, 255, 120)
DIVIDER_COLOR = (60, 60, 70)

SPEED = 4

# Two separate "rooms" side by side on the same screen
# Left half = room 1, right half = room 2
ROOM1_X_RANGE = (0, WIDTH // 2 - 5)
ROOM2_X_RANGE = (WIDTH // 2 + 5, WIDTH)

player1 = pygame.Rect(50, 50, 40, 40)
player2 = pygame.Rect(WIDTH // 2 + 50, 50, 40, 40)

# Obstacle are DIFFERENT in each room -> forces a path that works for both
# Each entry is [rect, dx, dy] so obstacles can move and bounce off walls
obstacles1 = [
    [pygame.Rect(150, 150, 120, 20), 3, 0],
    [pygame.Rect(100, 300, 20, 120), 0, 2],
]

obstacles2 = [
    [pygame.Rect(WIDTH // 2 + 200, 100, 20, 150), 0, -2],
    [pygame.Rect(WIDTH // 2 + 300, 350, 150, 20), -3, 0],
]

# Exit rects - both players must reach their exit at the same time (same move)
exit1 = pygame.Rect(ROOM1_X_RANGE[1] - 60, HEIGHT - 70, 40, 40)
exit2 = pygame.Rect(ROOM2_X_RANGE[1] - 60, HEIGHT - 70, 40, 40)


def move_player(rect, dx, dy, obstacles, x_bounds):
    new_rect = rect.move(dx, dy)

    # Clamp to this player's room (so they can't wander into the other room)
    new_rect.left = max(x_bounds[0], new_rect.left)
    new_rect.right = min(x_bounds[1], new_rect.right)
    new_rect.top = max(0, new_rect.top)
    new_rect.bottom = min(HEIGHT, new_rect.bottom)

    # Block on obstacles - if colliding, cancel this move
    # obstacles is a list of [rect, dx, dy] - only the rect (index 0) matters here
    for obs_data in obstacles:
        if new_rect.colliderect(obs_data[0]):
            return rect  # movement rejected, stay in place

    return new_rect


def update_obstacles(obstacles, x_bounds):
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


def draw_everything(win):
    screen.fill(BG_COLOR)
    draw_room_divider()

    for obs_data in obstacles1:
        pygame.draw.rect(screen, OBSTACLE_COLOR, obs_data[0])
    for obs_data in obstacles2:
        pygame.draw.rect(screen, OBSTACLE_COLOR, obs_data[0])

    pygame.draw.rect(screen, EXIT_COLOR, exit1)
    pygame.draw.rect(screen, EXIT_COLOR, exit2)

    pygame.draw.rect(screen, PLAYER1_COLOR, player1)
    pygame.draw.rect(screen, PLAYER2_COLOR, player2)

    if win:
        font = pygame.font.SysFont(None, 60)
        text = font.render("BOTH REACHED THE EXIT!", True, (255, 255, 255))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 30))

    pygame.display.update()


def main():
    global player1, player2
    running = True
    won = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not won:
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

            # SAME input applied to BOTH players - this is the core mechanic
            player1 = move_player(player1, dx, dy, obstacles1, ROOM1_X_RANGE)
            player2 = move_player(player2, dx, dy, obstacles2, ROOM2_X_RANGE)

            if player1.colliderect(exit1) and player2.colliderect(exit2):
                won = True

        draw_everything(won)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
