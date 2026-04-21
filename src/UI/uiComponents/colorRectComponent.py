from src.UI.uiComponents.UIcomponent import UIComponent
import pygame

class ColorRectComponent(UIComponent):
    """A simple UI component that displays a colored rectangle."""
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

    def draw(self, surface):
        if not self.element.is_visible():
            return

        rect = self.get_rect()
        if rect is None:
            return

        color_value = self.config.get("color", (255, 255, 255))
        color = self._parse_color(color_value)
        alpha = self.config.get("alpha")
        if alpha is not None:
            color = (color[0], color[1], color[2], self._clamp_byte(alpha, color[3]))

        if color[3] >= 255:
            pygame.draw.rect(surface, color[:3], rect)
            return

        fill = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        fill.fill(color)
        surface.blit(fill, rect.topleft)