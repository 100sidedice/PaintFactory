from src.UI.uiComponents.ui_component import UIComponent


class EventReaderComponent(UIComponent):
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)

    def _resolve_value(self, value, eventData):
        if not isinstance(value, str):
            return value

        # Source element data reference: "$source.__label"
        if value.startswith("$source."):
            source_path = eventData.get("source") if isinstance(eventData, dict) else None
            if source_path:
                source_element = self.manager.getElement(source_path)
                if source_element is not None:
                    return source_element.get_data(value[8:])
            return None

        # Event payload reference: "$event.key"
        if value.startswith("$event.") and isinstance(eventData, dict):
            return eventData.get(value[7:])

        return value

    def _apply_action(self, action, eventData):
        set_value = action.get("setValue")
        if isinstance(set_value, dict):
            var_name = set_value.get("var")
            value = self._resolve_value(set_value.get("value"), eventData)
            self.element.set_data(var_name, value)
            return

        if isinstance(set_value, str):
            self.element.set_data(set_value, self._resolve_value(action.get("value"), eventData))

        toggle_value = action.get("toggleValue")
        if isinstance(toggle_value, dict):
            var_name = toggle_value.get("var")
            if var_name is not None:
                current = self.element.get_data(var_name, False)
                self.element.set_data(var_name, not bool(current))

    def _get_rule(self, event):
        rule = self.config.get(event)
        if rule is not None:
            return rule

        # wildcard support: "dropdown.option.*"
        for key, value in self.config.items():
            if not isinstance(key, str):
                continue
            if key.endswith("*") and event.startswith(key[:-1]):
                return value
        return None

    def handleEvent(self, event, eventData, componentName, component):
        rule = self._get_rule(event)
        if not rule:
            return

        for action in rule.get("actions", []):
            self._apply_action(action, eventData)
