import asyncio

import pygame
import random

# Initialize Pygame
pygame.init()

pygame.key.set_repeat(300, 75)

# ---------------------------------------------------------
# 1. CONSTANTS & CONFIGURATION
# ---------------------------------------------------------
GRID_WIDTH = 10
GRID_HEIGHT = 20
BLOCK_SIZE = 30  # pixels per grid square

SCREEN_WIDTH = GRID_WIDTH * BLOCK_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * BLOCK_SIZE

# Color Definitions (RGB)
BLACK = (10, 10, 15)
GRAY = (140, 140, 140)
WHITE = (255, 255, 255)

CYAN    = (0, 240, 240)   # I piece
YELLOW  = (240, 240, 0)   # O piece
PURPLE  = (160, 0, 240)   # T piece
GREEN   = (0, 240, 0)     # S piece
RED     = (240, 0, 0)     # Z piece
BLUE    = (0, 0, 240)     # J piece
ORANGE  = (240, 160, 0)   # L piece

COLORS = [CYAN, YELLOW, PURPLE, GREEN, RED, BLUE, ORANGE]

# Tetrimino Shapes represented in 4x4 coordinate grids
SHAPES = [
    # I
    [[0, 1, 0, 0],
     [0, 1, 0, 0],
     [0, 1, 0, 0],
     [0, 1, 0, 0]],
    # O
    [[1, 1],
     [1, 1]],
    # T
    [[0, 1, 0],
     [1, 1, 1],
     [0, 0, 0]],
    # S
    [[0, 1, 1],
     [1, 1, 0],
     [0, 0, 0]],
    # Z
    [[1, 1, 0],
     [0, 1, 1],
     [0, 0, 0]],
    # J
    [[1, 0, 0],
     [1, 1, 1],
     [0, 0, 0]],
    # L
    [[0, 0, 1],
     [1, 1, 1],
     [0, 0, 0]]
]

# ---------------------------------------------------------
# 2. PIECE CLASS
# ---------------------------------------------------------
class Piece:
    def __init__(self, x, y, shape_idx):
        self.x = x
        self.y = y
        self.shape = SHAPES[shape_idx]
        self.color = COLORS[shape_idx]

    def rotate(self):
        """Rotate the piece matrix 90 degrees clockwise."""
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

# ---------------------------------------------------------
# 3. GAME HELPER FUNCTIONS
# ---------------------------------------------------------
def create_grid(locked_positions={}):
    """Create a 2D grid array representing locked blocks."""
    grid = [[GRAY for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    for (x, y), color in locked_positions.items():
        if y >= 0:
            grid[y][x] = color
    return grid

def convert_shape_format(piece):
    """Returns the absolute (x, y) coordinates of piece blocks."""
    positions = []
    for r_idx, row in enumerate(piece.shape):
        for c_idx, val in enumerate(row):
            if val:
                positions.append((piece.x + c_idx, piece.y + r_idx))
    return positions

def valid_space(piece, grid):
    """Check if the current piece position is valid (not out of bounds or overlapping locked blocks)."""
    accepted_positions = [[(j, i) for j in range(GRID_WIDTH) if grid[i][j] == GRAY] for i in range(GRID_HEIGHT)]
    accepted_positions = [pos for sub in accepted_positions for pos in sub]

    formatted = convert_shape_format(piece)

    for pos in formatted:
        if pos not in accepted_positions:
            if pos[1] >= 0:  # Allow pieces to spawn above top of screen
                return False
    return True

def clear_rows(grid, locked):
    """Clear full rows and shift upper blocks down correctly."""
    # 1. Find all full rows
    full_rows = []
    for i in range(GRID_HEIGHT):
        if all(grid[i][j] != GRAY for j in range(GRID_WIDTH)):
            full_rows.append(i)
    
    if not full_rows:
        return 0

    # 2. Remove all blocks in the full rows
    for i in full_rows:
        for j in range(GRID_WIDTH):
            locked.pop((j, i), None)

    # 3. Shift remaining blocks down by counting how many cleared rows are below them
    new_locked = {}
    for (x, y), color in locked.items():
        shift = sum(1 for r in full_rows if r > y)
        new_locked[(x, y + shift)] = color
    
    locked.clear()
    locked.update(new_locked)
    
    return len(full_rows)

def get_shape():
    """Return a new random Piece."""
    return Piece(GRID_WIDTH // 2 - 2, 0, random.randint(0, len(SHAPES) - 1))

def draw_window(surface, grid):
    """Draw the game board grid and locked blocks."""
    surface.fill(GRAY)
    
    # Draw blocks
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            pygame.draw.rect(surface, grid[y][x], (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
    
    # Draw grid lines
    for i in range(GRID_HEIGHT):
        pygame.draw.line(surface, BLACK, (0, i * BLOCK_SIZE), (SCREEN_WIDTH, i * BLOCK_SIZE), width=2)
    for j in range(GRID_WIDTH):
        pygame.draw.line(surface, BLACK, (j * BLOCK_SIZE, 0), (j * BLOCK_SIZE, SCREEN_HEIGHT,), width=2)
    pygame.draw.line(surface, RED, (0, 4 * BLOCK_SIZE), (SCREEN_WIDTH, 4 * BLOCK_SIZE), 2)

# ---------------------------------------------------------
# 4. MAIN GAME LOOP
# ---------------------------------------------------------
async def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris Clone | Score: {score}")
    clock = pygame.time.Clock()

    locked_positions = {}
    current_piece = get_shape()

    score = 0
    
    fall_time = 0
    fall_speed = 0.5  # Seconds per fall step
    game_over = False

    while not game_over:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        clock.tick()

        # Handle automatic gravity / fall down
        if fall_time / 1000 >= fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not valid_space(current_piece, grid) and current_piece.y > 0:
                current_piece.y -= 1
                # Lock piece in place
                for pos in convert_shape_format(current_piece):
                    locked_positions[pos] = current_piece.color
                grid = create_grid(locked_positions)
                lines_cleared = clear_rows(grid, locked_positions)
                score += lines_cleared * 10  # Example scoring: 10 points per line
                if any(y < 4 for (x, y) in locked_positions):
                    game_over = True
                
                current_piece = get_shape()

                if not valid_space(current_piece, grid):
                    game_over = True

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1

                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    current_piece.x += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1

                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    # Hard drop: keep moving down until it hits something
                    while valid_space(current_piece, grid):
                        current_piece.y += 1
                    # Step back up to the last valid position
                    current_piece.y -= 1
                    
                    # Lock the piece immediately and spawn a new one
                    for pos in convert_shape_format(current_piece):
                        locked_positions[pos] = current_piece.color
                    grid = create_grid(locked_positions)
                    lines_cleared = clear_rows(grid, locked_positions)
                    score += lines_cleared * 10  # Example scoring: 10 points per line

                    if any(y < 4 for (x, y) in locked_positions):
                        game_over = True
                    current_piece = get_shape()
                    if not valid_space(current_piece, grid):
                        game_over = True

                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    current_piece.rotate()
                    if not valid_space(current_piece, grid):
                        # Revert rotation if invalid
                        for _ in range(3):
                            current_piece.rotate()

        # Update Grid with current falling piece
        piece_coords = convert_shape_format(current_piece)
        for x, y in piece_coords:
            if y >= 0:
                grid[y][x] = current_piece.color

        # Check line clears
        

        # Draw Frame
        draw_window(screen, grid)
        pygame.display.set_caption(f"Python Tetris | Score: {score}")
        pygame.display.update()
        await asyncio.sleep(0.01)  # Yield control to allow event loop to process

    print("Game Over! Final Score:", score)
    pygame.quit()

if __name__ == "__main__":
   asyncio.run(main())
