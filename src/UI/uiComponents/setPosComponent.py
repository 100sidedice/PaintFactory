from src.UI.uiComponents.ui_component import UIComponent


class SetPosComponent(UIComponent):
    """UI component that sets the element container `pos` when a matching event is received.

    Config options:
    - `event`: string or list of event names to listen for (default: "ui.open_right_click_menu").
    """

    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)

    def handleEvent(self, event, eventData, componentName, component):
        cfg_event = self.config.get("event", "ui.open_right_click_menu")
        if isinstance(cfg_event, str):
            if event != cfg_event:
                return
        else:
            try:
                if event not in list(cfg_event):
                    return
            except Exception:
                return

        # Resolve position from event payload
        pos = None
        if isinstance(eventData, dict):
            p = eventData.get("pos")
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                try:
                    pos = [float(p[0]), float(p[1])]
                except Exception:
                    pos = None
            else:
                x = eventData.get("x")
                y = eventData.get("y")
                if x is not None and y is not None:
                    try:
                        pos = [float(x), float(y)]
                    except Exception:
                        pos = None

        if pos is None:
            return

        container = self.element.getComponent("container")
        if container is None:
            return

        # Set configured pos and clear any layout overrides so the change takes effect
        container.config["pos"] = [pos[0], pos[1]]
        try:
            container.clear_layout()
        except Exception:
            pass
