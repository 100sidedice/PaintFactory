from src.UI.uiComponents.ui_component import UIComponent
import pygame

class ColorRectComponent(UIComponent):
    """A simple UI component that displays a colored rectangle."""
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)

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

        if isinstance(value, (list, tuple)) and len(value) >= 3:
            return (int(value[0]), int(value[1]), int(value[2]))

        return (255, 255, 255)

    def draw(self, surface):
        if not self.element.is_visible():
            return

        rect = self.get_rect()
        if rect is None:
            return

        color_value = self.config.get("color", (255, 255, 255))
        color = self._parse_color(color_value)
        pygame.draw.rect(surface, color, rect)