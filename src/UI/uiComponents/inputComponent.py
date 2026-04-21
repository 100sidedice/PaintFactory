from src.UI.uiComponents.UIcomponent import UIComponent
import pygame


class InputComponent(UIComponent):
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self._last_trigger_time = {}

    def _condition_ok(self, condition):
        data_scope = condition.get("data-scope") or [self.element.path]
        var_name = condition.get("var")
        op = condition.get("condition", "==")
        expected = condition.get("value")

        if var_name is None:
            return True

        target_path = data_scope[0] if data_scope else self.element.path
        target = self.manager.getElement(target_path)
        if target is None:
            return False

        current = target.get_data(var_name)
        if op == "==":
            return current == expected
        if op == "!=":
            return current != expected
        if op == ">":
            return current > expected
        if op == ">=":
            return current >= expected
        if op == "<":
            return current < expected
        if op == "<=":
            return current <= expected
        return False

    def _all_conditions_ok(self, rule):
        conditions = rule.get("conditions", [])
        return all(self._condition_ok(cond) for cond in conditions)

    def _is_inside(self):
        rect = self.get_rect()
        if rect is None:
            return True
        mx, my = self.input.get_mouse_position()
        return rect.collidepoint((mx, my))

    def _triggered(self, trigger_name):
        if trigger_name.startswith("mouseup."):
            btn = trigger_name.split(".", 1)[1]
            if btn == "left":
                return self.input.get_mouse_button_up(1)
            if btn == "middle":
                return self.input.get_mouse_button_up(2)
            if btn == "right":
                return self.input.get_mouse_button_up(3)

        if trigger_name.startswith("mousedown."):
            btn = trigger_name.split(".", 1)[1]
            if btn == "left":
                return self.input.get_mouse_button_down(1)
            if btn == "middle":
                return self.input.get_mouse_button_down(2)
            if btn == "right":
                return self.input.get_mouse_button_down(3)

        return False

    def update(self, delta):
        if not self.element.is_visible():
            return

        if not self._is_inside():
            return

        now = pygame.time.get_ticks() / 1000.0
        consumed_triggers = set()
        try:
            mx, my = self.input.get_mouse_position()
            mouse_pos_key = (int(mx), int(my))
        except Exception:
            mouse_pos_key = None

        for trigger_key, rule in self.config.items():
            trigger_name = trigger_key.split("-", 1)[0]
            if trigger_name in consumed_triggers:
                continue
            # Skip if another element already consumed this trigger at this mouse position
            try:
                if mouse_pos_key is not None and self.manager._consumed_input is not None:
                    if (trigger_name, mouse_pos_key) in self.manager._consumed_input:
                        continue
            except Exception:
                pass
            if not self._triggered(trigger_name):
                continue

            if not self._all_conditions_ok(rule):
                continue

            min_duration = float(rule.get("duration", 0.0))
            last = self._last_trigger_time.get(trigger_key, -999999.0)
            if (now - last) < min_duration:
                continue

            emit_name = rule.get("emit")
            if not emit_name:
                continue

            scope = rule.get("scope")
            self.manager.emit_event(
                emit_name,
                {
                    "source": self.element.path,
                    "trigger": trigger_name,
                },
                scope=scope,
                source_element=self.element.path,
                componentName=self.name,
                component=self,
            )
            self._last_trigger_time[trigger_key] = now
            if rule.get("consume", True):
                consumed_triggers.add(trigger_name)
                # Respect `transparent` container keyword: if transparent, do not consume for others
                try:
                    container = self.element.getComponent("container")
                    transparent = False
                    if container is not None and hasattr(container, "has_keyword"):
                        transparent = container.has_keyword("transparent")
                except Exception:
                    transparent = False

                if not transparent and mouse_pos_key is not None:
                    try:
                        self.manager._consumed_input.add((trigger_name, mouse_pos_key))
                    except Exception:
                        pass
