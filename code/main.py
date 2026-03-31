import pygame # type: ignore
import sys
import os

# Add parent directory to path to resolve imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.settings import *
from input import Input
from spritesManager import SpriteManager
from tilemapManager import TilemapManager
from camera import Camera
import os

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("My Pygame Refresher")
        self.clock = pygame.time.Clock()

    def start(self):
        self.running = True
        # setup managers and test content
        self.camera = Camera(WIDTH, HEIGHT)
        self.sprite_manager = SpriteManager(self.camera)
        self.tilemap =  TilemapManager(self.camera, tile_size=(16, 16))

        # add a test sprite (bucket from data/sprites.json) via manager helper
        try:
            self.sprite_manager.add_from_json("conveyor-basic", pos=(6, 0))
        except Exception:
            pass


        self.run()

    def run(self):
        while self.running:
            dt_ms = self.clock.tick(FPS)
            dt = dt_ms / 1000.0
            Input.update()  # Update input states
            if Input.get_key_down(pygame.K_ESCAPE):
                self.running = False
            self.update(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def update(self, dt):
        # update managers
        if hasattr(self, "sprite_manager"):
            self.sprite_manager.update(dt)
        # camera could follow something in future; ensure it's clamped
        if hasattr(self, "camera"):
            self.camera.update(None)

    def drawBg(self):
        self.screen.fill((30, 30, 30))

    def draw(self):
        self.drawBg()
        # draw tilemap then sprites
        if hasattr(self, "tilemap"):
            self.tilemap.draw_tmx(self.screen, offset=(0, 0), camera=getattr(self, 'camera', None))
        if hasattr(self, "sprite_manager"):
            self.sprite_manager.draw(self.screen, camera=getattr(self, 'camera', None))

if __name__ == "__main__":
    game = Game()
    game.start()