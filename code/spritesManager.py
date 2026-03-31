import pygame
import os
import json
from data.settings import TILE_SIZE, ASSETS_DIR

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SpriteSheet:
    def __init__(self, path):
        self.image = pygame.image.load(path).convert_alpha()

    def image_at(self, row, col, size):
        x = col * size[0]
        y = row * size[1]
        rect = pygame.Rect(x, y, size[0], size[1])
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        surf.blit(self.image, (0, 0), rect)
        return surf

    def images_at_row(self, row, frames, size, start_col=0):
        return [self.image_at(row, start_col + i, size) for i in range(frames)]


class AnimatedSprite:
    def __init__(self, frames, pos=(0, 0), fps=8, loop=True, tile_size=None):
        self.frames = frames
        # `pos` is in tile coordinates (floats allowed)
        self.pos = pygame.Vector2(pos)
        self.fps = fps
        self.loop = loop
        self.current = 0.0
        # tile pixel size (w,h) used to convert tile coords -> world pixels
        self.tile_size = tile_size or (16, 16)

    def update(self, dt):
        if len(self.frames) <= 1:
            return
        self.current += dt * self.fps
        if self.loop:
            self.current %= len(self.frames)
        else:
            if self.current >= len(self.frames):
                self.current = len(self.frames) - 1

    def draw(self, surface, camera=None):
        idx = int(self.current)
        # convert tile coords to world pixels
        tw, th = self.tile_size if isinstance(self.tile_size, tuple) else (self.tile_size, self.tile_size)
        world_x = self.pos.x * tw
        world_y = self.pos.y * th

        if camera is not None:
            try:
                surface_pos = camera.apply_pos((world_x, world_y))
                zoom = getattr(camera, "zoom", 1.0)
            except Exception:
                surface_pos = (int(world_x - camera.offset.x), int(world_y - camera.offset.y))
                zoom = getattr(camera, "zoom", 1.0)
        else:
            surface_pos = (int(world_x), int(world_y))
            zoom = 1.0

        frame = self.frames[idx]
        if zoom != 1.0:
            fw = max(1, int(frame.get_width() * zoom))
            fh = max(1, int(frame.get_height() * zoom))
            frame = pygame.transform.scale(frame, (fw, fh))
        surface.blit(frame, surface_pos)


class SpriteManager:
    """Simple manager for animated and static sprites.

    Sprite positions are interpreted in tile coordinates (floats allowed).
    """
    def __init__(self, camera=None, tile_size=(16, 16)):
        self.camera = camera
        self.tile_size = tile_size
        self.sprites = []

    def add(self, sprite):
        # ensure sprite has tile_size for converting tile coords -> pixels
        if not hasattr(sprite, "tile_size") or sprite.tile_size is None:
            sprite.tile_size = self.tile_size
        self.sprites.append(sprite)

    def add_from_json(self, key, pos=(0, 0)):
        """Load a sprite by key from data/sprites.json and add it to this manager.

        `pos` is interpreted in tile coordinates.
        """
        sprite = SpriteManager.load_from_json(key, pos=pos)
        if not hasattr(sprite, "tile_size") or sprite.tile_size is None:
            sprite.tile_size = self.tile_size
        self.add(sprite)
        return sprite

    def update(self, dt):
        for s in self.sprites:
            s.update(dt)

    def draw(self, surface, camera=None):
        cam = camera or self.camera
        for s in self.sprites:
            if hasattr(s, 'draw'):
                try:
                    s.draw(surface, cam)
                except TypeError:
                    s.draw(surface)

    @staticmethod
    def load_from_json(key, pos=(0, 0)):
        """Load a sprite definition from data/sprites.json and return an AnimatedSprite.

        JSON structure expects keys like in `data/sprites.json` with fields:
          - size: [w, h]
          - frames: number
          - row: int
          - path: path to image (relative to project root)
        """
        json_path = os.path.join(BASE_DIR, "data", "sprites.json")
        with open(json_path, "r", encoding="utf-8") as f:
            defs = json.load(f)

        if key not in defs:
            raise KeyError(f"Sprite key '{key}' not found in {json_path}")

        info = defs[key]
        size = tuple(info.get("size", [16, 16]))
        frames = int(info.get("frames", 1))
        row = int(info.get("row", 0))
        path = info.get("path")
        img_path = os.path.join(BASE_DIR, path)

        sheet = SpriteSheet(img_path)
        imgs = sheet.images_at_row(row, frames, size, start_col=0)
        sprite = AnimatedSprite(imgs, pos=pos, tile_size=TILE_SIZE)
        return sprite


__all__ = ["SpriteSheet", "AnimatedSprite", "SpriteManager"]
