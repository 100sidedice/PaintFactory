from .Component import Component
import pygame


class SelectComponent(Component):
    """Machine component that opens a UI right-click menu for this machine.

    Emits a manager/UI event `ui.open_right_click_menu` with payload `{"pos": [x,y], "source": "machine.<name>"}`
    when the machine is right-clicked.
    """

    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)
        self.input = machine.callData("input")
        self.updateType = "continuous"

    def update(self, items, delta):
        if getattr(self.input, "is_locked", lambda k: False)("click"):
            return

        if self.input.get_mouse_up(3):
            tileSize = 16
            tw, th = tileSize, tileSize
            x = int(self.machine.pos[0] * tw)
            y = int(self.machine.pos[1] * th)
            eventData = {"pos": [x, y], "source": f"machine.{self.machine.name}"}

            # If the machine manager has a UI manager attached, emit the UI event
            ui_manager = getattr(self.machine.machineManager, "ui_manager", None)
            if ui_manager is not None:
                try:
                    ui_manager.emit_event("ui.open_right_click_menu", eventData, source_element=None, componentName=self.name, component=self)
                    return
                except Exception:
                    # fallback to machine event if UI emit fails
                    pass

            # fallback: push event through machines/managers
            self.machine.pushEvent("ui.open_right_click_menu", eventData, componentName=self.name, component=self)
