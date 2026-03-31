import os

# Project layout
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Window / timing
FPS = 60
WIDTH = 1920
HEIGHT = 1080

# Tile / assets
TILE_SIZE = (16, 16)
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")
TILEMAPS_DIR = os.path.join(ASSETS_DIR, "Tilemaps")