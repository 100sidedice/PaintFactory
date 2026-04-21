import math

from src.UI.uiComponents.UIcomponent import UIComponent


class DynamicValueComponent(UIComponent):
    """Animate element data variables over time.

    Example config:
    {
      "__frame": {"type": "pingpong", "min": 0, "max": 3, "speed": 8, "round": true},
      "__alpha": {"type": "sine", "min": 120, "max": 255, "speed": 2}
    }
    """

    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self._state = {}

    def _get_rule(self, key, rule):
        if not isinstance(rule, dict):
            return None
        r = dict(rule)
        r.setdefault("type", "loop")
        r.setdefault("min", 0.0)
        r.setdefault("max", 1.0)
        r.setdefault("speed", 1.0)
        r.setdefault("round", False)
        r.setdefault("start", r.get("min", 0.0))
        return r

    def _ensure_state(self, key, rule):
        if key in self._state:
            return
        self._state[key] = {
            "value": float(rule.get("start", rule.get("min", 0.0))),
            "dir": 1.0,
            "time": 0.0,
        }

    def _write_value(self, key, rule, value):
        if rule.get("round", False):
            value = int(round(value))
        self.element.set_data(key, value)

    def update(self, delta):
        if not self.element.is_visible():
            return

        for key, raw_rule in self.config.items():
            rule = self._get_rule(key, raw_rule)
            if rule is None:
                continue

            self._ensure_state(key, rule)
            state = self._state[key]

            min_v = float(rule.get("min", 0.0))
            max_v = float(rule.get("max", 1.0))
            speed = float(rule.get("speed", 1.0))
            mode = str(rule.get("type", "loop")).lower()

            if max_v < min_v:
                min_v, max_v = max_v, min_v

            value = float(state["value"])
            direction = float(state["dir"])
            state["time"] += float(delta)

            if mode == "pingpong":
                value += direction * speed * float(delta)
                if value > max_v:
                    overflow = value - max_v
                    value = max_v - overflow
                    direction = -1.0
                elif value < min_v:
                    overflow = min_v - value
                    value = min_v + overflow
                    direction = 1.0

            elif mode == "sine":
                center = (min_v + max_v) * 0.5
                amp = (max_v - min_v) * 0.5
                value = center + amp * math.sin(state["time"] * speed * math.tau)

            else:  # loop
                value += speed * float(delta)
                span = max(1e-9, max_v - min_v)
                while value > max_v:
                    value -= span
                while value < min_v:
                    value += span

            state["value"] = value
            state["dir"] = direction
            self._write_value(key, rule, value)
