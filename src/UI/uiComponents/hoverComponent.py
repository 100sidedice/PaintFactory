from .ui_component import UIComponent

class HoverComponent(UIComponent):
    """
    A component that fires events when the user starts and stops hovering over the UI element.
    Events:
        - on_hover_start: Fired when the mouse enters the element.
        - on_hover_end: Fired when the mouse leaves the element.
    """
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self._hovering = False
        self.on_hover_start = config.get("on_hover_start") if config else None
        self.on_hover_end = config.get("on_hover_end") if config else None

    def update(self, mouse_pos, *args, **kwargs):
        # Assume self.parent is the UI element this component is attached to
        if not hasattr(self, 'parent') or self.parent is None:
            return
        rect = self.parent.get_rect() if hasattr(self.parent, 'get_rect') else None
        if rect is None:
            return
        inside = rect.collidepoint(mouse_pos)
        if inside and not self._hovering:
            self._hovering = True
            if callable(self.on_hover_start):
                self.on_hover_start(self.parent)
            self.parent.fire_event('on_hover_start')
        elif not inside and self._hovering:
            self._hovering = False
            if callable(self.on_hover_end):
                self.on_hover_end(self.parent)
            self.parent.fire_event('on_hover_end')

    def reset(self):
        self._hovering = False
