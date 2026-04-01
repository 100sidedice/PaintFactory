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
DATA_DIR = os.path.join(BASE_DIR, "data")
TILEMAPS_DIR = os.path.join(ASSETS_DIR, "Tilemaps")

spritePaths = {
    "sprites" : os.path.join(DATA_DIR, "sprites.json"),
    "tiles" : os.path.join(DATA_DIR, "tiles.json")
}
