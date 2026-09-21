import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Split Control")
clock = pygame.time.Clock()

# Colors
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
player1_frame_index = 0
player2_frame_index = 0
animation_timer = 0
font = pygame.font.SysFont(None, 36)

# Load images
player1_img = pygame.transform.scale(
    pygame.image.load("assets/player1.png").convert_alpha(), (40, 40)
)
player2_img = pygame.transform.scale(
    pygame.image.load("assets/player2.png").convert_alpha(), (40, 40)
)


def get_content_bounds(surface):
    """Union of all opaque regions in a surface - the true visible bounding box."""
    mask = pygame.mask.from_surface(surface)
    rects = mask.get_bounding_rects()
    if not rects:
        return surface.get_rect()
    union = rects[0]
    for r in rects[1:]:
        union = union.union(r)
    return union


def slice_sprite_sheet(path, frame_size):
    sheet = pygame.image.load(path).convert_alpha()
    width, height = sheet.get_size()

    col_has_content = []
    for x in range(width):
        has_content = False
        for y in range(0, height, 4):
            if sheet.get_at((x, y))[3] > 10:
                has_content = True
                break
        col_has_content.append(has_content)

    ranges = []
    in_content = False
    start = 0
    for x, has in enumerate(col_has_content):
        if has and not in_content:
            start = x
            in_content = True
        elif not has and in_content:
            ranges.append((start, x))
            in_content = False
    if in_content:
        ranges.append((start, width))

    frames = []
    for start, end in ranges:
        loose_slice = sheet.subsurface((start, 0, end - start, height))
        bounds = get_content_bounds(loose_slice)
        tight_frame = loose_slice.subsurface(bounds)
        tight_frame = pygame.transform.scale(tight_frame, frame_size)
        frames.append(tight_frame)
    return frames


def load_image_cropped(path, size):
    img = pygame.image.load(path).convert_alpha()
    bounds = get_content_bounds(img)
    cropped = img.subsurface(bounds)
    return pygame.transform.scale(cropped, size)


player1_frames = slice_sprite_sheet("assets/player1_sheet.png", (50, 50))
player2_frames = slice_sprite_sheet("assets/player2_sheet.png", (50, 50))
ANIMATION_SPEED = 8  # lower = faster animation

obstacle_images = [
    load_image_cropped("assets/obstacle1.png", (60, 40)),
    load_image_cropped("assets/obstacle2.png", (60, 40)),
    load_image_cropped("assets/obstacle3.png", (60, 40)),
]
background_img = pygame.transform.scale(
    pygame.image.load("assets/background.png").convert(), (WIDTH, HEIGHT)
)

# Two separate "rooms" side by side on the same screen
# Left half = room 1, right half = room 2
ROOM1_X_RANGE = (0, WIDTH // 2 - 5)
ROOM2_X_RANGE = (WIDTH // 2 + 5, WIDTH)

player1 = pygame.Rect(50, 50, 50, 50)
player2 = pygame.Rect(WIDTH // 2 + 50, 50, 50, 50)

# Obstacles are DIFFERENT in each room -> forces a path that works for both
obstacles1 = [
    [pygame.Rect(150, 150, 60, 40), 1, 0, obstacle_images[0]],
    [pygame.Rect(100, 300, 60, 40), 0, 1, obstacle_images[1]],
]

obstacles2 = [
    [pygame.Rect(WIDTH // 2 + 200, 100, 60, 40), 0, -1, obstacle_images[2]],
    [pygame.Rect(WIDTH // 2 + 300, 350, 60, 40), -1, 0, obstacle_images[0]],
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
    if len(obstacles) >= MAX_OBSTACLES:
        return

    for _ in range(10):  # try a few times to find a safe spot
        x = random.randint(x_bounds[0] + 20, x_bounds[1] - 40)
        y = random.randint(20, HEIGHT - 40)
        candidate = pygame.Rect(x, y, 60, 20)
        if candidate.colliderect(player_rect.inflate(SAFE_SPAWN_DISTANCE, SAFE_SPAWN_DISTANCE)):
            continue  # too close to player, try again
        dx = random.choice([-1, 1])
        dy = random.choice([-1, 1])
        image = random.choice(obstacle_images)
        obstacles.append([candidate, dx, dy, image])
        return


def update_obstacles(obstacles, x_bounds):
    for obs_data in obstacles:
        rect, dx, dy = obs_data[0], obs_data[1], obs_data[2]
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


def draw_start_screen():
    screen.blit(background_img, (0, 0))
    draw_room_divider()

    title_font = pygame.font.SysFont(None, 64)
    title_text = title_font.render("SPLIT CONTROL", True, (255, 255, 255))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

    line_font = pygame.font.SysFont(None, 32)
    lines = [
        "Arrow keys move BOTH wizards at once.",
        "Each room has different obstacles - find a path that works for both!",
        "Avoid obstacles, survive as long as you can, score climbs as you move.",
        "",
        "Press any key to start",
    ]
    for i, line in enumerate(lines):
        line_text = line_font.render(line, True, (230, 230, 230))
        screen.blit(line_text, (WIDTH // 2 - line_text.get_width() // 2, 200 + i * 35))

    pygame.display.update()


def draw_everything(game_over, score, lives):
    screen.blit(background_img, (0, 0))
    draw_room_divider()

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    lives_text = font.render(f"Lives: {lives}", True, (255, 255, 255))
    screen.blit(lives_text, (10, 45))

    for obs_data in obstacles1:
        screen.blit(obs_data[3], obs_data[0])
    for obs_data in obstacles2:
        screen.blit(obs_data[3], obs_data[0])

    screen.blit(player1_frames[player1_frame_index], player1)
    screen.blit(player2_frames[player2_frame_index], player2)

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
    global player1_frame_index, player2_frame_index, animation_timer
    player1 = pygame.Rect(50, 50, 50, 50)
    player2 = pygame.Rect(WIDTH // 2 + 50, 50, 50, 50)
    obstacles1 = [
        [pygame.Rect(150, 150, 60, 40), 1, 0, obstacle_images[0]],
        [pygame.Rect(100, 300, 60, 40), 0, 1, obstacle_images[1]],
    ]
    obstacles2 = [
        [pygame.Rect(WIDTH // 2 + 200, 100, 60, 40), 0, -1, obstacle_images[2]],
        [pygame.Rect(WIDTH // 2 + 300, 350, 60, 40), -1, 0, obstacle_images[0]],
    ]
    score = 0
    lives = 5
    invincible_timer = 0
    next_difficulty_score = DIFFICULTY_STEP
    player1_frame_index = 0
    player2_frame_index = 0
    animation_timer = 0


def reset_positions():
    global player1, player2, invincible_timer
    player1 = pygame.Rect(50, 50, 50, 50)
    player2 = pygame.Rect(WIDTH // 2 + 50, 50, 50, 50)
    invincible_timer = INVINCIBLE_FRAMES


def main():
    global player1, player2, score, lives, invincible_timer, next_difficulty_score
    global player1_frame_index, player2_frame_index, animation_timer
    running = True
    game_over = False
    game_started = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and not game_started:
                game_started = True
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    reset_game()
                    game_over = False

        if not game_started:
            draw_start_screen()
            clock.tick(60)
            continue

        if not game_over:
            if invincible_timer > 0:
                invincible_timer -= 1

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
                animation_timer += 1
                if animation_timer >= ANIMATION_SPEED:
                    animation_timer = 0
                    player1_frame_index = (player1_frame_index + 1) % len(player1_frames)
                    player2_frame_index = (player2_frame_index + 1) % len(player2_frames)
            else:
                player1_frame_index = 0
                player2_frame_index = 0
                animation_timer = 0

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