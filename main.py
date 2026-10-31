# Jewel Shuffle - A cute match-3 game for my daughter
import pygame
import random
import sys
import logging
from pygame import mixer

# Set up logging to file - only user actions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('jewel_shuffle.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("=== Jewel Shuffle started ===")

# Initialize Pygame
pygame.init()
mixer.init()

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
GRID_SIZE = 8
CELL_SIZE = 60
MARGIN = 50
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND_COLOR = (240, 230, 255)

# Jewel colors
JEWEL_COLORS = [
    (255, 105, 180),  # Pink
    (255, 165, 0),     # Orange
    (135, 206, 235),   # Sky Blue
    (152, 251, 152),   # Light Green
    (255, 255, 102),   # Yellow
    (204, 153, 255),   # Lavender
]

# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jewel Shuffle")
clock = pygame.time.Clock()

# Load sounds (optional)
try:
    swap_sound = mixer.Sound("sounds/swap.wav")
    match_sound = mixer.Sound("sounds/match.wav")
except:
    swap_sound = None
    match_sound = None

# Jewel class
class Jewel:
    def __init__(self, x, y, color, row, col):
        self.x = x
        self.y = y
        self.color = color
        self.row = row
        self.col = col
        self.size = CELL_SIZE - 10
        self.selected = False
        self.matched = False
        self.target_y = y
        self.velocity = 0

    def draw(self, surface):
        # Draw a cute jewel (circle with a smaller circle on top)
        pygame.draw.circle(surface, self.color, (self.x + CELL_SIZE // 2, self.y + CELL_SIZE // 2), self.size // 2)
        pygame.draw.circle(surface, WHITE, (self.x + CELL_SIZE // 2, self.y + CELL_SIZE // 2), self.size // 4)
        if self.selected:
            pygame.draw.circle(surface, WHITE, (self.x + CELL_SIZE // 2, self.y + CELL_SIZE // 2), self.size // 2 + 5, 3)

    def update(self):
        # Simple gravity for falling jewels
        if self.y < self.target_y:
            self.velocity += 0.5
            self.y += self.velocity
            if self.y >= self.target_y:
                self.y = self.target_y
                self.velocity = 0

# Game class
class Game:
    def __init__(self):
        self.grid = []
        self.selected_jewel = None
        self.score = 0
        self.game_over = False
        self.log = ["Welcome to Jewel Shuffle!"]
        self.create_grid()

    def add_log(self, message):
        self.log.append(message)
        if len(self.log) > 10:
            self.log.pop(0)
        logger.info(message)

    def create_grid(self):
        self.grid = []
        for row in range(GRID_SIZE):
            self.grid.append([])
            for col in range(GRID_SIZE):
                x = MARGIN + col * CELL_SIZE
                y = MARGIN + row * CELL_SIZE
                color = random.choice(JEWEL_COLORS)
                self.grid[row].append(Jewel(x, y, color, row, col))
        
        # Ensure no initial matches
        while self.find_matches():
            self.remove_matches()
            self.fill_grid()

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)
        
        # Draw grid background
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                rect = pygame.Rect(
                    MARGIN + col * CELL_SIZE,
                    MARGIN + row * CELL_SIZE,
                    CELL_SIZE, CELL_SIZE
                )
                pygame.draw.rect(surface, WHITE, rect, 2)
        
        # Draw jewels (skip None cells)
        for row in self.grid:
            for jewel in row:
                if jewel is not None:
                    jewel.draw(surface)
        
        # Draw score
        font = pygame.font.SysFont("Comic Sans MS", 30)
        score_text = font.render(f"Score: {self.score}", True, BLACK)
        surface.blit(score_text, (20, 10))
        
        # Draw action log on the right side
        log_x = MARGIN + GRID_SIZE * CELL_SIZE + 20
        log_y = 50
        log_title = font.render("Actions:", True, BLACK)
        surface.blit(log_title, (log_x, log_y))
        
        font_small = pygame.font.SysFont("Comic Sans MS", 16)
        for i, msg in enumerate(self.log[-8:]):
            text = font_small.render(msg, True, (80, 80, 80))
            surface.blit(text, (log_x, log_y + 40 + i * 25))

    def update(self):
        for row in self.grid:
            for jewel in row:
                if jewel is not None:
                    jewel.update()

    def handle_click(self, pos):
        if self.game_over:
            self.add_log("Game over - click ignored")
            return
            
        if not self.are_jewels_settled():
            self.add_log("Please wait for jewels to settle...")
            return
        
        col = (pos[0] - MARGIN) // CELL_SIZE
        row = (pos[1] - MARGIN) // CELL_SIZE
        
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            self.add_log("Clicked outside the grid")
            return
            
        jewel = self.grid[row][col]
        
        if jewel is None:
            self.add_log("Clicked on empty space")
            return
        
        if self.selected_jewel is None:
            self.selected_jewel = jewel
            jewel.selected = True
            self.add_log(f"Selected jewel at ({row},{col})")
        else:
            if self.selected_jewel == jewel:
                self.selected_jewel.selected = False
                self.selected_jewel = None
                self.add_log("Deselected jewel")
            elif self.is_adjacent(self.selected_jewel, jewel):
                self.swap_jewels(self.selected_jewel, jewel)
                self.add_log(f"Swapped ({self.selected_jewel.row},{self.selected_jewel.col}) with ({row},{col})")
                
                if not self.find_matches():
                    self.swap_jewels(self.selected_jewel, jewel)
                    self.add_log("No match - swap undone")
                else:
                    if swap_sound:
                        swap_sound.play()
                    self.process_matches()
                self.selected_jewel.selected = False
                self.selected_jewel = None
            else:
                self.selected_jewel.selected = False
                self.selected_jewel = jewel
                jewel.selected = True
                self.add_log(f"Selected new jewel at ({row},{col})")

    def is_adjacent(self, jewel1, jewel2):
        return (abs(jewel1.row - jewel2.row) == 1 and jewel1.col == jewel2.col) or \
               (abs(jewel1.col - jewel2.col) == 1 and jewel1.row == jewel2.row)

    def swap_jewels(self, jewel1, jewel2):
        # Swap positions in grid
        self.grid[jewel1.row][jewel1.col], self.grid[jewel2.row][jewel2.col] = \
            self.grid[jewel2.row][jewel2.col], self.grid[jewel1.row][jewel1.col]
        
        # Update row and col attributes
        jewel1.row, jewel2.row = jewel2.row, jewel1.row
        jewel1.col, jewel2.col = jewel2.col, jewel1.col
        
        # Update x, y, and target_y coordinates
        jewel1.x = MARGIN + jewel1.col * CELL_SIZE
        jewel1.y = MARGIN + jewel1.row * CELL_SIZE
        jewel1.target_y = jewel1.y
        jewel1.velocity = 0
        jewel2.x = MARGIN + jewel2.col * CELL_SIZE
        jewel2.y = MARGIN + jewel2.row * CELL_SIZE
        jewel2.target_y = jewel2.y
        jewel2.velocity = 0

    def find_matches(self):
        matches = []
        
        # Check horizontal matches (skip None cells)
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE - 2):
                j1 = self.grid[row][col]
                j2 = self.grid[row][col + 1]
                j3 = self.grid[row][col + 2]
                if j1 is not None and j2 is not None and j3 is not None:
                    if j1.color == j2.color == j3.color:
                        match = [j1, j2, j3]
                        if col + 3 < GRID_SIZE and self.grid[row][col + 3] is not None and j1.color == self.grid[row][col + 3].color:
                            match.append(self.grid[row][col + 3])
                        if col + 4 < GRID_SIZE and self.grid[row][col + 4] is not None and j1.color == self.grid[row][col + 4].color:
                            match.append(self.grid[row][col + 4])
                        matches.append(match)
        
        # Check vertical matches (skip None cells)
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE - 2):
                j1 = self.grid[row][col]
                j2 = self.grid[row + 1][col]
                j3 = self.grid[row + 2][col]
                if j1 is not None and j2 is not None and j3 is not None:
                    if j1.color == j2.color == j3.color:
                        match = [j1, j2, j3]
                        if row + 3 < GRID_SIZE and self.grid[row + 3][col] is not None and j1.color == self.grid[row + 3][col].color:
                            match.append(self.grid[row + 3][col])
                        if row + 4 < GRID_SIZE and self.grid[row + 4][col] is not None and j1.color == self.grid[row + 4][col].color:
                            match.append(self.grid[row + 4][col])
                        matches.append(match)
        
        # Remove duplicates and overlapping matches - return set of jewels to remove
        jewels_to_remove = set()
        for match in matches:
            for jewel in match:
                jewels_to_remove.add(jewel)
        
        # Group by connected matches for scoring
        if not jewels_to_remove:
            return []
        
        return [list(jewels_to_remove)]

    def remove_matches(self):
        matches = self.find_matches()
        if not matches:
            return False
        
        for match in matches:
            for jewel in match:
                jewel.matched = True
                self.grid[jewel.row][jewel.col] = None
            self.score += len(match) * 10
            if match_sound:
                match_sound.play()
        
        return True

    def are_jewels_settled(self):
        for row in self.grid:
            for jewel in row:
                if jewel is None:
                    return False
                if jewel.y != jewel.target_y:
                    return False
        return True

    def process_matches(self):
        """Remove matches and fill grid. Returns True if matches were found."""
        matches = self.find_matches()
        if not matches:
            return False
        
        total = 0
        for match in matches:
            for jewel in match:
                if jewel is not None:
                    self.grid[jewel.row][jewel.col] = None
            total += len(match)
        
        self.score += total * 10
        self.add_log(f"MATCH! +{total * 10} points (total: {self.score})")
        if match_sound:
            match_sound.play()
        
        self.fill_grid()
        return True

    def fill_grid(self):
        # Move jewels down
        for col in range(GRID_SIZE):
            empty_rows = []
            for row in range(GRID_SIZE - 1, -1, -1):
                if self.grid[row][col] is None:
                    empty_rows.append(row)
                elif empty_rows:
                    empty_row = empty_rows.pop(0)
                    self.grid[empty_row][col] = self.grid[row][col]
                    self.grid[empty_row][col].row = empty_row
                    self.grid[empty_row][col].target_y = MARGIN + empty_row * CELL_SIZE
                    self.grid[row][col] = None
                    empty_rows.append(row)
            
            # Fill empty rows with new jewels
            for row in empty_rows:
                x = MARGIN + col * CELL_SIZE
                y = MARGIN - CELL_SIZE  # Start above the grid
                color = random.choice(JEWEL_COLORS)
                self.grid[row][col] = Jewel(x, y, color, row, col)
                self.grid[row][col].target_y = MARGIN + row * CELL_SIZE
        self.add_log("New jewels fell into place")

    def run(self):
        while not self.game_over:
            self.update()
            
            if self.are_jewels_settled():
                if not self.find_matches():
                    self.game_over = True
                    print("Game Over! Final Score:", self.score)
                else:
                    self.remove_matches()
                    self.fill_grid()

# Main game loop
def main():
    game = Game()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("=== Game closed ===")
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    game.handle_click(event.pos)
        
        game.update()
        
        # Check for cascading matches after jewels settle
        if game.are_jewels_settled() and not game.game_over:
            if game.find_matches():
                game.process_matches()
        
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    
    logger.info(f"Final score: {game.score}")
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()