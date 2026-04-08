import pygame
import os
from data.settings import TILE_SIZE


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
    def __init__(self, frames, pos=(0, 0), fps=8, loop=True, tile_size=None, rotation=0):
        self.frames = frames
        # `pos` is in tile coordinates (floats allowed)
        self.pos = pygame.Vector2(pos)
        self.fps = fps
        self.loop = loop
        self.current = 0.0
        # rotation: integer 0-3 representing 0,90,180,270 degrees
        try:
            self.rotation = int(rotation) % 4
        except Exception:
            self.rotation = 0
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
        # apply discrete rotation (0..3) where each step = 90 degrees
        if getattr(self, 'rotation', 0) != 0:
            frame = pygame.transform.rotate(frame, self.rotation * 90)
        if zoom != 1.0:
            fw = max(1, int(frame.get_width() * zoom))
            fh = max(1, int(frame.get_height() * zoom))
            frame = pygame.transform.scale(frame, (fw, fh))
        surface.blit(frame, surface_pos)


class SpriteManager:
    """Simple manager for animated and static sprites.

    Sprite positions are interpreted in tile coordinates (floats allowed).
    """
    def __init__(self, camera=None, tile_size=(16, 16), preloaded_assets=None):
        self.camera = camera
        self.tile_size = tile_size
        self.sprites = []
        self.preloaded_assets = preloaded_assets or {}
        self._surface_index = self._build_surface_index()

    def _build_surface_index(self):
        index = {}
        for key, value in self.preloaded_assets.items():
            if isinstance(value, pygame.Surface):
                if isinstance(key, str):
                    index[key] = value
                    base = os.path.basename(key)
                    if base:
                        index[base] = value
        return index

    def _get_defs(self):
        """Return sprite/machine definition dicts from preloaded data."""
        sources = []
        sprites_defs = self.preloaded_assets.get("sprites")
        machines_defs = self.preloaded_assets.get("machines")
        sources.append(machines_defs)
        sources.append(sprites_defs)
        return sources

    def _find_def(self, key):
        for defs in self._get_defs():
            if key in defs:
                return defs[key]
        return None

    def _resolve_image_surface(self, image_ref):
        if not image_ref:
            return None
        if image_ref in self._surface_index:
            return self._surface_index[image_ref]
        # allow refs like "paintbuckets.png" while preloaded key is "Assets/paintbuckets.png"
        assets_path = f"Assets/{image_ref}" if not image_ref.startswith("Assets/") else image_ref
        if assets_path in self._surface_index:
            return self._surface_index[assets_path]
        return self._surface_index.get(os.path.basename(image_ref))

    @staticmethod
    def _extract_frames(sheet_image, row, frames, size, start_col=0):
        imgs = []
        for i in range(frames):
            x = (start_col + i) * size[0]
            y = row * size[1]
            rect = pygame.Rect(x, y, size[0], size[1])
            surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            surf.blit(sheet_image, (0, 0), rect)
            imgs.append(surf)
        return imgs

    def add(self, sprite):
        sprite.tile_size = self.tile_size
        self.sprites.append(sprite)

    def add_sprite(self, key, pos=(0, 0), rotation=0):
        """Create and add a sprite by key using preloaded definitions/data."""
        info = self._find_def(key)
        if not info:
            return None

        size = tuple(info.get("size", [16, 16]))
        frames = int(info.get("frames", 1))
        row = int(info.get("row", 0))
        start_col = int(info.get("frame_offset", 0))
        image_ref = info.get("image")
        sheet_image = self._resolve_image_surface(image_ref)
        if sheet_image is None:
            return None

        imgs = SpriteManager._extract_frames(sheet_image, row, frames, size, start_col=start_col)
        sprite = AnimatedSprite(imgs, pos=pos, tile_size=TILE_SIZE, rotation=rotation)
        if sprite is None:
            return None
        self.add(sprite)
        return sprite
    
    def update(self, dt):
        for s in self.sprites:
            s.update(dt)

    def draw(self, surface):
        cam = self.camera
        for s in self.sprites:
            s.draw(surface, cam)


__all__ = ["SpriteSheet", "AnimatedSprite", "SpriteManager"]
