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
        # SelectComponent no longer polls input directly; it listens for
        # events pushed by the ClickComponent via `handleEvent`.
        return

    def handleEvent(self, event, eventData, componentName, component):
        # Listen for right-click events pushed by ClickComponent
        if event != "i_have_been_clicked_via_a_right_click":
            return

        # Determine position from eventData (support Vector2 or list/tuple)
        pos = eventData["pos"]

        if isinstance(pos, pygame.Vector2):
            x = int(pos.x)
            y = int(pos.y)
        else:
            x = int(pos[0])
            y = int(pos[1])

        out_event = {"pos": [x, y], "source": f"machine.{self.machine.name}"}

        print(f"Right-clicked machine (select via event): {self.machine.name} at {out_event['pos']}")

        # Emit UI event (assume ui_manager exists and has emit_event)
        ui_manager = self.machine.machineManager.ui_manager
        ui_manager.emit_event("ui.open_right_click_menu", out_event, source_element=None, componentName=self.name, component=self)
