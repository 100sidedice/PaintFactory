from .UIcomponent import UIComponent

class HoverComponent(UIComponent):
    """
    A component that fires events when the user starts and stops hovering over the UI element.
    Events:
        - on_hover_start: Fired when the mouse enters the element.
        - on_hover_end: Fired when the mouse leaves the element.
    """
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self.updateType = "continuous"
        self._hovering = False
        # Rules: may be a string (event name) or a dict with keys `name`/`eventData`/`scope`.
        self._start_rule = (config.get("on_hover_start") if isinstance(config, dict) else None)
        self._end_rule = (config.get("on_hover_end") if isinstance(config, dict) else None)

    def update(self, delta, *args, **kwargs):
        # Use element/component API to determine rect and mouse position.
        if not hasattr(self, "element") or self.element is None:
            return
        if not self.element.is_visible():
            return
        rect = self.get_rect()
        if rect is None:
            return
        mx, my = self.input.get_mouse_position()
        inside = rect.collidepoint((mx, my))
        if inside and not self._hovering:
            self._hovering = True
            self._emit_rule(self._start_rule, "hover.start")
        elif not inside and self._hovering:
            self._hovering = False
            self._emit_rule(self._end_rule, "hover.end")

    def reset(self):
        self._hovering = False

    def _emit_rule(self, rule, trigger_name):
        """Emit an event based on a rule which may be a string (event name)
        or a dict with `name`/`eventData`/`scope` keys. The emitted payload
        will include `source` and `trigger` by default.
        """
        if not rule:
            return
        # Normalize rule
        event_name = None
        scope = None
        payload = {"source": self.element.path, "trigger": trigger_name}

        if isinstance(rule, str):
            event_name = rule.strip()
        elif isinstance(rule, dict):
            # Accept either `name` or `emit` as the event key for compatibility
            event_name = str(rule.get("name") or rule.get("emit") or "").strip()
            scope = rule.get("scope")
            extra = rule.get("eventData") or rule.get("payload") or {}
            if isinstance(extra, dict):
                payload.update(extra)
        # If no scope provided, default to __self so hover events target the emitter by default.
        if scope is None:
            scope = "__self"
        else:
            return

        if not event_name:
            return

        try:
            # Use manager.emit_event so scope resolution and manager-level handling
            # (including __self support) are applied.
            self.manager.emit_event(
                event_name,
                payload,
                scope=scope,
                source_element=self.element.path,
                componentName=self.name,
                component=self,
            )
        except Exception:
            # Fail silently to avoid crashing the update loop.
            return
