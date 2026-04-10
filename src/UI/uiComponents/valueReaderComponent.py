from src.UI.uiComponents.ui_component import UIComponent


class ValueReaderComponent(UIComponent):
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)

    def _condition_ok(self, current, op, expected):
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

    def _apply_action(self, action):
        if "setValue" in action:
            target_var = action.get("setValue")
            self.element.set_data(target_var, action.get("value"))

    def update(self, delta):
        if not self.element.is_visible():
            return

        for key, rule in self.config.items():
            var_name = rule.get("var")
            if var_name is None:
                var_name = key.split("-", 1)[0]

            current = self.element.get_data(var_name)
            expected = rule.get("value")
            op = rule.get("condition", "==")
            if self._condition_ok(current, op, expected):
                action = rule.get("action", {})
                self._apply_action(action)
