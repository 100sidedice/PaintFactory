import math
import pygame

from src.UI.uiComponents.UIcomponent import UIComponent


class PolygonComponent(UIComponent):
    """Draw a polygon from configured vertices.

    The component auto-syncs `container.size` to the polygon's bounding box.
    """

    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self.updateType = "continuous"
        self._last_vertices_signature = None

    def _clamp_byte(self, value, default=255):
        try:
            return max(0, min(255, int(value)))
        except Exception:
            return int(default)

    def _to_number(self, value, default=0.0):
        source = value
        if isinstance(source, str) and source.startswith("__"):
            source = self.element.get_data(source, source)
        try:
            return float(source)
        except Exception:
            return float(default)

    def _parse_color(self, value):
        if isinstance(value, str) and value.startswith("__"):
            value = self.element.get_data(value, value)
        elif isinstance(value, str) and value.startswith("$theme."):
            value = self.manager.callData(f"themeDefaults.{value[7:]}", value)
        elif isinstance(value, str) and value.startswith("themeDefaults."):
            value = self.manager.callData(value, value)

        if isinstance(value, str):
            color_text = value.strip()
            if color_text.startswith("#"):
                color_text = color_text[1:]
            if len(color_text) == 6:
                try:
                    return (
                        int(color_text[0:2], 16),
                        int(color_text[2:4], 16),
                        int(color_text[4:6], 16),
                        255,
                    )
                except ValueError:
                    return (255, 255, 255, 255)
            if len(color_text) == 8:
                try:
                    return (
                        int(color_text[0:2], 16),
                        int(color_text[2:4], 16),
                        int(color_text[4:6], 16),
                        int(color_text[6:8], 16),
                    )
                except ValueError:
                    return (255, 255, 255, 255)

        if isinstance(value, (list, tuple)) and len(value) >= 4:
            return (
                self._clamp_byte(value[0]),
                self._clamp_byte(value[1]),
                self._clamp_byte(value[2]),
                self._clamp_byte(value[3]),
            )

        if isinstance(value, (list, tuple)) and len(value) >= 3:
            return (
                self._clamp_byte(value[0]),
                self._clamp_byte(value[1]),
                self._clamp_byte(value[2]),
                255,
            )

        return (255, 255, 255, 255)

    def _resolved_vertices(self):
        raw = self.config.get("vertices", [])
        if not isinstance(raw, list):
            return []

        out = []
        for pair in raw:
            if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                continue
            x = self._to_number(pair[0], 0.0)
            y = self._to_number(pair[1], 0.0)
            out.append((float(x), float(y)))
        return out

    def _bounds(self, vertices):
        if not vertices:
            return None
        min_x = min(v[0] for v in vertices)
        min_y = min(v[1] for v in vertices)
        max_x = max(v[0] for v in vertices)
        max_y = max(v[1] for v in vertices)
        return (min_x, min_y, max_x, max_y)

    def _sync_container_size(self, bounds):
        if bounds is None:
            return
        container = self.element.getComponent("container")
        if container is None or not isinstance(container.config, dict):
            return

        min_x, min_y, max_x, max_y = bounds
        width = max(1, int(math.ceil(max_x - min_x)))
        height = max(1, int(math.ceil(max_y - min_y)))

        size = container.config.get("size")
        if not isinstance(size, list) or len(size) < 2:
            container.config["size"] = [width, height]
            return

        if int(size[0]) != width or int(size[1]) != height:
            container.config["size"] = [width, height]

    def _polygon_points(self, rect, vertices, bounds):
        min_x, min_y, max_x, max_y = bounds
        bw = max(1e-9, float(max_x - min_x))
        bh = max(1e-9, float(max_y - min_y))
        scale = min(float(max(1, rect.w)) / bw, float(max(1, rect.h)) / bh)
        draw_w = bw * scale
        draw_h = bh * scale
        off_x = float(rect.x) + (float(rect.w) - draw_w) * 0.5 - (float(min_x) * scale)
        off_y = float(rect.y) + (float(rect.h) - draw_h) * 0.5 - (float(min_y) * scale)
        return [
            (
                int(round(off_x + (vx * scale))),
                int(round(off_y + (vy * scale))),
            )
            for (vx, vy) in vertices
        ]

    def _vertices_signature(self, vertices):
        return tuple((round(float(v[0]), 5), round(float(v[1]), 5)) for v in vertices)

    def update(self, delta):
        if not self.element.is_visible():
            return
        vertices = self._resolved_vertices()
        if len(vertices) < 3:
            return
        signature = self._vertices_signature(vertices)
        if signature != self._last_vertices_signature:
            self._sync_container_size(self._bounds(vertices))
            self._last_vertices_signature = signature

    def draw(self, surface):
        if not self.element.is_visible():
            return

        editor = getattr(self.manager, "editor", None)
        if (
            editor is not None
            and getattr(editor, "enabled", False)
            and getattr(editor, "polygon_edit_mode", False)
            and getattr(editor, "polygon_edit_path", None) == self.element.path
        ):
            return

        rect = self.get_rect()
        if rect is None:
            return

        vertices = self._resolved_vertices()
        if len(vertices) < 3:
            return

        bounds = self._bounds(vertices)

        color = self._parse_color(self.config.get("color", "#FFFFFF"))
        alpha = self.config.get("alpha")
        if alpha is not None:
            color = (color[0], color[1], color[2], self._clamp_byte(alpha, color[3]))

        try:
            width = max(0, int(self.config.get("width", 0)))
        except Exception:
            width = 0

        points = self._polygon_points(rect, vertices, bounds)

        if color[3] >= 255:
            pygame.draw.polygon(surface, color[:3], points, width)
            return

        if rect.w <= 0 or rect.h <= 0:
            return

        temp = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        local_points = [(px - rect.x, py - rect.y) for (px, py) in points]
        pygame.draw.polygon(temp, color, local_points, width)
        surface.blit(temp, rect.topleft)
