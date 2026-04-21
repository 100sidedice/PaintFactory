import pygame

from src.UI.uiComponents.UIcomponent import UIComponent


class OutlineComponent(UIComponent):
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)

    def _clamp_byte(self, value, default=255):
        try:
            return max(0, min(255, int(value)))
        except Exception:
            return int(default)

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
                    )
                except ValueError:
                    return (255, 255, 255)
            if len(color_text) == 8:
                try:
                    return (
                        int(color_text[0:2], 16),
                        int(color_text[2:4], 16),
                        int(color_text[4:6], 16),
                    )
                except ValueError:
                    return (255, 255, 255)

        if isinstance(value, (list, tuple)) and len(value) >= 3:
            return (
                self._clamp_byte(value[0]),
                self._clamp_byte(value[1]),
                self._clamp_byte(value[2]),
            )

        return (255, 255, 255)

    def _polygon_points_from_component(self, rect):
        poly = self.element.getComponent("polygon")
        if poly is None:
            return None
        resolver = getattr(poly, "_resolved_vertices", None)
        bounds_fn = getattr(poly, "_bounds", None)
        if not callable(resolver) or not callable(bounds_fn):
            return None

        vertices = resolver()
        if not isinstance(vertices, list) or len(vertices) < 3:
            return None
        bounds = bounds_fn(vertices)
        if bounds is None:
            return None

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
                int(round(off_x + (float(vx) * scale))),
                int(round(off_y + (float(vy) * scale))),
            )
            for (vx, vy) in vertices
        ]

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

        width = int(self.config.get("width", 1))
        color = self._parse_color(self.config.get("color", "#FFFFFF"))

        poly_points = self._polygon_points_from_component(rect)
        if poly_points is not None:
            stroke = abs(width)
            if stroke <= 0:
                stroke = 1
            n = len(poly_points)
            if n >= 2:
                for i in range(n):
                    a = poly_points[i]
                    b = poly_points[(i + 1) % n]
                    pygame.draw.line(surface, color, a, b, stroke)
                corner_r = max(1, int(round(stroke * 0.5)))
                for p in poly_points:
                    pygame.draw.circle(surface, color, p, corner_r)
            return

        if width < 0:
            stroke = abs(width)
            draw_rect = pygame.Rect(rect.x - stroke, rect.y - stroke, rect.w + (stroke * 2), rect.h + (stroke * 2))
            pygame.draw.rect(surface, color, draw_rect, stroke)
            return

        pygame.draw.rect(surface, color, rect, width)
