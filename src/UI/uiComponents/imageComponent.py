import os
import pygame

from src.UI.uiComponents.UIcomponent import UIComponent


class ImageComponent(UIComponent):
    """Draw preloaded images/spritesheets using flexible UI settings.

    Preferred source is a preloaded data path, e.g. "Assets/paintbuckets.png".
    """

    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)

    def _resolve_value(self, value, default=None):
        if isinstance(value, str):
            if value.startswith("__"):
                return self.element.get_data(value, default)
            if value.startswith("$theme."):
                return self.manager.callData(f"themeDefaults.{value[7:]}", default)
            if value.startswith("themeDefaults."):
                return self.manager.callData(value, default)
        return value if value is not None else default

    def _resolve_surface(self):
        ref = self._resolve_value(self.config.get("path") or self.config.get("image") or self.config.get("src"))
        if not ref:
            return None

        surf = self.manager.callData(ref)
        if isinstance(surf, pygame.Surface):
            return surf

        if isinstance(ref, str):
            base = os.path.basename(ref)
            surf = self.manager.callData(base)
            if isinstance(surf, pygame.Surface):
                return surf
            name_no_ext = os.path.splitext(base)[0]
            surf = self.manager.callData(name_no_ext)
            if isinstance(surf, pygame.Surface):
                return surf

        return None

    def _source_rect(self, surface):
        src = self._resolve_value(self.config.get("sourceRect"))
        if isinstance(src, (list, tuple)) and len(src) >= 4:
            return pygame.Rect(int(src[0]), int(src[1]), int(src[2]), int(src[3]))

        frame_size = self._resolve_value(self.config.get("frameSize"))
        if isinstance(frame_size, (list, tuple)) and len(frame_size) >= 2:
            fw = int(frame_size[0])
            fh = int(frame_size[1])
            if fw <= 0 or fh <= 0:
                return surface.get_rect()

            max_cols = max(1, surface.get_width() // fw)
            max_rows = max(1, surface.get_height() // fh)
            total_frames = max(1, max_cols * max_rows)

            col = int(self._resolve_value(self.config.get("col", 0), 0))
            row = int(self._resolve_value(self.config.get("row", 0), 0))

            if "index" in self.config and "columns" in self.config:
                idx = int(self._resolve_value(self.config.get("index", 0), 0))
                idx = idx % total_frames
                columns = max(1, int(self._resolve_value(self.config.get("columns", max_cols), max_cols)))
                columns = min(columns, max_cols)
                col = idx % columns
                row = idx // columns

            col = max(0, min(col, max_cols - 1))
            row = max(0, min(row, max_rows - 1))

            return pygame.Rect(col * fw, row * fh, fw, fh)

        return surface.get_rect()

    def _parse_color(self, value):
        if isinstance(value, str) and value.startswith("#"):
            txt = value[1:]
            if len(txt) == 6:
                try:
                    return (int(txt[0:2], 16), int(txt[2:4], 16), int(txt[4:6], 16))
                except ValueError:
                    return None
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            return (int(value[0]), int(value[1]), int(value[2]))
        return None

    def _apply_tint(self, surface):
        tint = self._resolve_value(self.config.get("tint"))
        color = self._parse_color(tint)
        if color is None:
            return surface

        tinted = surface.copy()
        tint_layer = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        alpha = int(self._resolve_value(self.config.get("tintAlpha", 120), 120))
        tint_layer.fill((color[0], color[1], color[2], max(0, min(255, alpha))))
        tinted.blit(tint_layer, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted

    def _fit_size(self, src_size, target_size, fit):
        sw, sh = src_size
        tw, th = target_size
        if sw <= 0 or sh <= 0:
            return max(1, tw), max(1, th)

        if fit == "fill":
            return max(1, tw), max(1, th)

        if fit == "contain":
            scale = min(tw / sw, th / sh) if tw > 0 and th > 0 else 1.0
            return max(1, int(sw * scale)), max(1, int(sh * scale))

        if fit == "cover":
            scale = max(tw / sw, th / sh) if tw > 0 and th > 0 else 1.0
            return max(1, int(sw * scale)), max(1, int(sh * scale))

        # none
        return sw, sh

    def draw(self, surface):
        if not self.element.is_visible():
            return

        container_rect = self.get_rect()
        if container_rect is None:
            return

        src_surface = self._resolve_surface()
        if src_surface is None:
            return

        source_rect = self._source_rect(src_surface)
        image = src_surface.subsurface(source_rect).copy()

        rotation = float(self._resolve_value(self.config.get("rotation", 0.0), 0.0))
        flip_x = bool(self._resolve_value(self.config.get("flipX", False), False))
        flip_y = bool(self._resolve_value(self.config.get("flipY", False), False))
        if flip_x or flip_y:
            image = pygame.transform.flip(image, flip_x, flip_y)
        if rotation != 0:
            image = pygame.transform.rotate(image, rotation)

        image = self._apply_tint(image)

        alpha = self._resolve_value(self.config.get("alpha"))
        if alpha is not None:
            image.set_alpha(max(0, min(255, int(alpha))))

        offset = self._resolve_value(self.config.get("offset", [0, 0]), [0, 0])
        ox = int(offset[0]) if isinstance(offset, (list, tuple)) and len(offset) > 0 else 0
        oy = int(offset[1]) if isinstance(offset, (list, tuple)) and len(offset) > 1 else 0

        draw_box = pygame.Rect(container_rect.x + ox, container_rect.y + oy, container_rect.w, container_rect.h)
        explicit_size = self._resolve_value(self.config.get("size"))
        if isinstance(explicit_size, (list, tuple)) and len(explicit_size) >= 2:
            draw_box.w = int(explicit_size[0])
            draw_box.h = int(explicit_size[1])

        fit = str(self._resolve_value(self.config.get("fit", "contain"), "contain")).lower()
        target_w, target_h = self._fit_size((image.get_width(), image.get_height()), (draw_box.w, draw_box.h), fit)

        smooth = bool(self._resolve_value(self.config.get("smooth", True), True))
        scaler = pygame.transform.smoothscale if smooth else pygame.transform.scale
        if (target_w, target_h) != (image.get_width(), image.get_height()):
            image = scaler(image, (target_w, target_h))

        anchor = str(self._resolve_value(self.config.get("anchor", "center"), "center")).lower()
        if anchor == "topleft":
            dx, dy = draw_box.x, draw_box.y
        elif anchor == "topright":
            dx, dy = draw_box.right - target_w, draw_box.y
        elif anchor == "bottomleft":
            dx, dy = draw_box.x, draw_box.bottom - target_h
        elif anchor == "bottomright":
            dx, dy = draw_box.right - target_w, draw_box.bottom - target_h
        else:
            dx = draw_box.x + (draw_box.w - target_w) // 2
            dy = draw_box.y + (draw_box.h - target_h) // 2

        surface.blit(image, (dx, dy))
