import pygame
import os
import json
from data.settings import BASE_DIR, TILE_SIZE, ASSETS_DIR, TILEMAPS_DIR


class TileSet:
    def __init__(self, path, tile_size=(16, 16)):
        self.path = path
        self.tile_size = tile_size
        self.image = pygame.image.load(path).convert_alpha()

    def tile_at(self, row, col=0):
        w, h = self.tile_size
        rect = pygame.Rect(col * w, row * h, w, h)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.blit(self.image, (0, 0), rect)
        return surf


class TilemapManager:
    """Loads tile definitions from data/tiles.json and draws a simple map.

    Map format loader expects a JSON file with a 2D array of tile keys, e.g.:
      [["conveyor-basic","conveyor-basic"], [null, "conveyor-corner-left"]]
    """

    def __init__(self, camera=None, tile_size=None):
        self.camera = camera
        self.tile_size = tile_size or TILE_SIZE
        self.tile_defs = {}
        self.tilesets = {}
        self._load_defs()
        self.map_data = None
        self.map_layers = []
        self.map_width = 0
        self.map_height = 0

        self.center_map()

    def _load_defs(self):
        defs_path = os.path.join(BASE_DIR, "data", "tiles.json")
        with open(defs_path, "r", encoding="utf-8") as f:
            self.tile_defs = json.load(f)

        # preload tileset images referenced by defs (image assumed under Assets/)
        for key, info in self.tile_defs.items():
            img_name = info.get("image")
            if not img_name:
                continue
            asset_path = os.path.join(ASSETS_DIR, img_name)
            if asset_path not in self.tilesets:
                if os.path.exists(asset_path):
                    self.tilesets[asset_path] = TileSet(asset_path, tile_size=self.tile_size)

        

    def center_map(self):
        """Center the loaded map in the camera viewport by adjusting camera offset."""
        self.load_from_assets("backgroundmap.tmx")
        # set camera world size from tilemap and fit the world into viewport
        tw, th = self.tile_size
        world_w = self.map_width * tw
        world_h = self.map_height * th
        # compute zoom so the whole map fits and center it; allow zoom-in
        self.camera.fit_to_world(world_w, world_h, allow_zoom_in=True, margin=0)

    def get_tile_surface(self, key):
        if key is None:
            return None
        info = self.tile_defs.get(key)
        if not info:
            return None
        img_name = info.get("image")
        row = int(info.get("row", 0))
        asset_path = os.path.join(BASE_DIR, "Assets", img_name)
        tileset = self.tilesets.get(asset_path)
        if not tileset:
            if os.path.exists(asset_path):
                tileset = TileSet(asset_path, tile_size=self.tile_size)
                self.tilesets[asset_path] = tileset
            else:
                return None
        return tileset.tile_at(row, 0)

    def draw_map(self, surface, map_data, offset=(0, 0)):
        """Draw a 2D list of tile keys to the given surface at offset."""
        ox, oy = offset
        w, h = self.tile_size
        for r, row in enumerate(map_data):
            for c, key in enumerate(row):
                tile_surf = self.get_tile_surface(key)
                if tile_surf:
                    surface.blit(tile_surf, (ox + c * w, oy + r * h))

    # --- TMX support (simple) ---
    def load_tmx(self, tmx_path):
        """Load a basic TMX file (with a single tileset and CSV layer).

        Stores parsed map in `self.map_data` as a 2D list of gids (ints), and
        caches the tileset image for rendering.
        """
        import xml.etree.ElementTree as ET

        tree = ET.parse(tmx_path)
        root = tree.getroot()

        tilewidth = int(root.attrib.get("tilewidth", self.tile_size[0]))
        tileheight = int(root.attrib.get("tileheight", self.tile_size[1]))
        self.tile_size = (tilewidth, tileheight)

        # tileset
        ts = root.find("tileset")
        firstgid = int(ts.attrib.get("firstgid", 1))
        source = ts.attrib.get("source")
        tsx_path = os.path.join(os.path.dirname(tmx_path), source)
        # parse tsx to find image and columns
        tsx_tree = ET.parse(tsx_path)
        tsx_root = tsx_tree.getroot()
        image = tsx_root.find("image")
        img_src = image.attrib.get("source")
        img_path = os.path.join(os.path.dirname(tmx_path), img_src)
        columns = int(tsx_root.attrib.get("columns", 1))

        # cache tileset
        self._tmx_tileset = {
            "img_path": img_path,
            "firstgid": firstgid,
            "columns": columns,
            "tilewidth": tilewidth,
            "tileheight": tileheight,
        }

        # parse all layers (CSV) and store them in map_layers in order
        self.map_layers = []
        layers = root.findall("layer")
        for layer in layers:
            layer_name = layer.attrib.get("name")
            data_tag = layer.find("data")
            if data_tag is None or data_tag.text is None:
                continue
            data = data_tag.text.strip()
            rows = [line.strip() for line in data.splitlines() if line.strip()]
            map_rows = []
            for row in rows:
                gids = [int(x) for x in row.split(",") if x != ""]
                map_rows.append(gids)
            self.map_layers.append({"name": layer_name, "data": map_rows})

        # set map dimensions from first layer if present
        if self.map_layers:
            first = self.map_layers[0]["data"]
            self.map_height = len(first)
            self.map_width = len(first[0]) if self.map_height else 0
        else:
            self.map_height = 0
            self.map_width = 0

    def load_from_assets(self, filename: str):
        """Convenience: load a TMX file from Assets/Tilemaps by filename."""
        tmx_path = os.path.join(TILEMAPS_DIR, filename)
        if not os.path.exists(tmx_path):
            raise FileNotFoundError(f"TMX not found: {tmx_path}")
        self.load_tmx(tmx_path)
        return True

    def draw_tmx(self, surface, offset=(0, 0), camera=None):
        """Draw the loaded TMX map using its tileset image.

        If `camera` is provided, tile positions will be transformed by the
        camera's offset so the map is rendered relative to the viewport.
        """
        if not self.map_layers or not hasattr(self, "_tmx_tileset"):
            return
        ox, oy = offset
        tw = self._tmx_tileset["tilewidth"]
        th = self._tmx_tileset["tileheight"]
        cols = self._tmx_tileset["columns"]
        img_path = self._tmx_tileset["img_path"]

        tileset_image = pygame.image.load(img_path).convert_alpha()
        # draw each layer in order
        for layer in self.map_layers:
            for r, row in enumerate(layer["data"]):
                for c, gid in enumerate(row):
                    if gid == 0:
                        continue
                    local_id = gid - self._tmx_tileset["firstgid"]
                    tx = (local_id % cols) * tw
                    ty = (local_id // cols) * th
                    rect = pygame.Rect(tx, ty, tw, th)
                    world_x = ox + c * tw
                    world_y = oy + r * th
                    if camera is not None:
                        try:
                            draw_pos = camera.apply_pos((world_x, world_y))
                            # scale tile surface according to camera.zoom
                            zoom = getattr(camera, "zoom", 1.0)
                        except Exception:
                            draw_pos = (int(world_x - camera.offset.x), int(world_y - camera.offset.y))
                            zoom = getattr(camera, "zoom", 1.0)
                    else:
                        draw_pos = (world_x, world_y)
                        zoom = 1.0

                    # extract tile and scale to zoom
                    tile_surf = tileset_image.subsurface(rect).copy()
                    if zoom != 1.0:
                        sw = max(1, int(tw * zoom))
                        sh = max(1, int(th * zoom))
                        tile_surf = pygame.transform.scale(tile_surf, (sw, sh))
                    surface.blit(tile_surf, draw_pos)


__all__ = ["TilemapManager", "TileSet"]
