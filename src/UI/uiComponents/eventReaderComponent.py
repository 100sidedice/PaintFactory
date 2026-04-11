from src.UI.uiComponents.ui_component import UIComponent


class EventReaderComponent(UIComponent):
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)

    def _resolve_value(self, value, eventData):
        if not isinstance(value, str):
            return value

        if value == "$source":
            return eventData.get("source") if isinstance(eventData, dict) else None

        if value == "$self":
            return self.element.path

        # This element data reference: "$self.__label"
        if value.startswith("$self."):
            return self.element.get_data(value[6:])

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
            key_path = value[7:]
            current = eventData
            for part in str(key_path).split("."):
                if not isinstance(current, dict):
                    return None
                current = current.get(part)
            return current

        return value

    def _resolve_payload(self, payload, eventData):
        if isinstance(payload, dict):
            out = {}
            for key, value in payload.items():
                out[key] = self._resolve_payload(value, eventData)
            return out
        if isinstance(payload, list):
            return [self._resolve_payload(item, eventData) for item in payload]
        return self._resolve_value(payload, eventData)

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

        emit_event = action.get("emitEvent")
        if isinstance(emit_event, str):
            event_name = str(emit_event).strip()
            payload = self._resolve_payload(action.get("eventData", {}), eventData)
            if event_name:
                self.manager.emit_event(
                    event_name,
                    payload,
                    source_element=self.element.path,
                    componentName=self.name,
                    component=self,
                )
            return

        if isinstance(emit_event, dict):
            event_name = str(emit_event.get("name") or emit_event.get("event") or "").strip()
            scope = emit_event.get("scope")
            raw_payload = emit_event.get("eventData", emit_event.get("payload", {}))
            payload = self._resolve_payload(raw_payload, eventData)
            if event_name:
                self.manager.emit_event(
                    event_name,
                    payload,
                    scope=scope,
                    source_element=self.element.path,
                    componentName=self.name,
                    component=self,
                )
            return

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
