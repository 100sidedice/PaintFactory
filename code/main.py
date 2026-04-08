import pygame # type: ignore
import sys
import os
import importlib.util

# Add parent directory to path to resolve imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.settings import *
from input import Input
from spritesManager import SpriteManager
from tilemapManager import TilemapManager
from machineManager import MachineManager
from camera import Camera
from gameState import GameState

from support import loadJson

import asyncio

# Global game state singleton (initialized in Game.start)
GAME_STATE = None

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("My Pygame Refresher")
        self.clock = pygame.time.Clock()

    async def load_asset(self, asset):
        asset_type = asset.get("type")
        asset_path = asset.get("path")
        asset_name = asset.get("name")

        def _resolve_path(path):
            if os.path.isabs(path):
                return path
            return os.path.join(BASE_DIR, path)

        abs_path = _resolve_path(asset_path)

        if asset_type == "image":
            loaded = await asyncio.to_thread(pygame.image.load, abs_path)
            loaded = loaded.convert_alpha()
        elif asset_type == "json":
            loaded = await asyncio.to_thread(loadJson, abs_path)
        elif asset_type == "text":
            def _read_text(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            loaded = await asyncio.to_thread(_read_text, abs_path)
        elif asset_type == "module":
            def _load_module(path, module_key):
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Module not found: {path}")
                mod_name = f"pf_dynamic_{module_key}".replace("-", "_")
                spec = importlib.util.spec_from_file_location(mod_name, path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not create module spec for: {path}")
                module_dir = os.path.dirname(path)
                inserted = False
                if module_dir and module_dir not in sys.path:
                    sys.path.insert(0, module_dir)
                    inserted = True
                try:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    return mod
                finally:
                    if inserted:
                        try:
                            sys.path.remove(module_dir)
                        except ValueError:
                            pass

            loaded = await asyncio.to_thread(_load_module, abs_path, asset_name or "module")
        elif asset_type == "folder":
            inside_type = asset.get("insideType")

            if inside_type == "module":
                def _load_modules_from_folder(folder_path, module_prefix):
                    if not os.path.isdir(folder_path):
                        raise NotADirectoryError(f"Folder not found: {folder_path}")

                    modules = {}
                    inserted = False
                    if folder_path not in sys.path:
                        sys.path.insert(0, folder_path)
                        inserted = True
                    try:
                        for entry in sorted(os.listdir(folder_path)):
                            full = os.path.join(folder_path, entry)
                            if not os.path.isfile(full):
                                continue
                            if not entry.endswith(".py"):
                                continue
                            if entry.startswith("__"):
                                continue

                            key = entry[:-3]
                            mod_name = f"pf_dynamic_{module_prefix}_{key}".replace("-", "_")
                            spec = importlib.util.spec_from_file_location(mod_name, full)
                            if spec is None or spec.loader is None:
                                continue
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            modules[key] = mod

                        return modules
                    finally:
                        if inserted:
                            try:
                                sys.path.remove(folder_path)
                            except ValueError:
                                pass

                loaded = await asyncio.to_thread(_load_modules_from_folder, abs_path, asset_name or "folder")
            else:
                def _list_folder(folder_path):
                    if not os.path.isdir(folder_path):
                        raise NotADirectoryError(f"Folder not found: {folder_path}")
                    return [os.path.join(folder_path, name) for name in sorted(os.listdir(folder_path))]

                loaded = await asyncio.to_thread(_list_folder, abs_path)
        else:
            raise ValueError(f"Unknown asset type: {asset_type}")

        return asset_name, asset_path, loaded

    async def preloadAssets(self):
        needed_assets = [
            {"type":"image","path":"Assets/conveyor.png", "name":"conveyors"},
            {"type":"image","path":"Assets/paintbuckets.png", "name":"paintbuckets"},
            {"type":"json","path":"data/sprites.json", "name":"sprites"},
            {"type":"json","path":"data/tiles.json", "name":"machines"},
            {"type":"text","path":"Assets/Tilemaps/backgroundmap.tmx", "name":"tilemap.background.tmx"},
            {"type":"text","path":"Assets/Tilemaps/backgroundmap.tsx", "name":"tilemap.background.tsx"},
            {"type":"image","path":"Assets/Tilemaps/backgroundmap.tileset.png", "name":"tilemap.background.image"},
            {"type":"folder", "path": "code/machineComponents", "name": "machineComponents", "insideType": "module"}
        ]
        tasks = [self.load_asset(asset) for asset in needed_assets]
        results = await asyncio.gather(*tasks)
        self.data = {}
        for name, path, loaded in results:
            self.data[name] = loaded
            self.data[path] = loaded



    async def start(self):
        global GAME_STATE
        await self.preloadAssets()
        GAME_STATE = GameState(self.data)
        self.running = True

        self.camera = Camera(WIDTH, HEIGHT)
        self.sprite_manager = SpriteManager(self.camera, preloaded_assets=self.data)
        self.machine_manager = MachineManager(self.sprite_manager, data=self.data, GAME_STATE=GAME_STATE)
        self.tilemap = TilemapManager(self.camera, tile_size=(16, 16), preloaded_assets=self.data)


        self.machine_manager.tilemap = self.tilemap

        # goal
        self.machine_manager.add_machine("4-way-spawner", pos=(5, 5), rotation=0)

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
        self.sprite_manager.update(dt)
        self.machine_manager.update(dt)
        self.camera.update(None)

    def drawBg(self):
        self.screen.fill((30, 30, 30))

    def draw(self):
        self.drawBg()
        # draw tilemap then sprites
        self.tilemap.draw_tmx(self.screen, offset=(0, 0), camera=self.camera)
        self.sprite_manager.draw(self.screen)
            
async def startgame():
    game = Game()
    await game.start()

if __name__ == "__main__":
    asyncio.run(startgame())