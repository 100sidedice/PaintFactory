import pygame # type: ignore
import sys
import os

# Add parent directory to path to resolve imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.settings import *
from input import Input

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("My Pygame Refresher")
        self.clock = pygame.time.Clock()

    def start(self):
        self.running = True
        self.run()

    def run(self):
        while self.running:
            Input.update()  # Update input states
            if Input.get_key_down(pygame.K_ESCAPE):
                self.running = False
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def update(self):
        pass

    def drawBg(self):
        self.screen.fill((30, 30, 30))

    def draw(self):
        self.drawBg()

if __name__ == "__main__":
    game = Game()
    game.start()