from .Component import Component

class ConveyorComponent(Component):
    """Component that moves items along a conveyor belt."""
    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)
        self.speed = self.machine.machineManager.GAME_STATE.get("machines.conveyor_speed")  # units per second
        # Keep base configuration so rotations can be recomputed later
        self.base_direction = list(self.machine.callData(f"componentData.{self.name}.direction"))
        self.base_collision = dict(self.machine.callData(f"componentData.{self.name}.collision"))
        # Current runtime values
        self.direction = list(self.base_direction)
        self.collision = dict(self.base_collision)
        # Apply initial machine rotation
        try:
            rot = int(self.machine.callData("rotation"))
        except Exception:
            rot = 0
        self._apply_rotation(rot)

        self.updateType = "static"  # Only update on events, not every tick

 
    def handleEvent(self, event, eventData, componentName, component):
        """Handle events related to items on the conveyor."""
        if event != "collision": return
        
        edges = eventData["edges"]
        if edges["left"] < self.collision["left"]:
            return
        if edges["right"] < self.collision["right"]:
            return
        if edges["top"] < self.collision["top"]:
            return
        if edges["bottom"] < self.collision["bottom"]:
            return

        item = eventData["item"]
        delta = eventData["delta"]
        # Start moving the item in the conveyor's direction
        item.pos = (
            item.pos[0] + self.direction[0] * self.speed * delta,
            item.pos[1] + self.direction[1] * self.speed * delta
        )

    def _apply_rotation(self, rot):
        try:
            r = int(rot) % 4
        except Exception:
            r = 0
        # rotate direction and collision r times (clockwise 90deg per step)
        d = list(self.base_direction)
        c = dict(self.base_collision)
        for _ in range(r):
            d = [d[1], -d[0]]
            c = {
                "left": c.get("top"),
                "top": c.get("right"),
                "right": c.get("bottom"),
                "bottom": c.get("left"),
            }
        self.direction = d
        self.collision = c

    def rotate(self, new_rotation):
        """Called when the machine's rotation changes."""
        self._apply_rotation(new_rotation)