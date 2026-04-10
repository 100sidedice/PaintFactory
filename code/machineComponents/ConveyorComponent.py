from Component import Component
import pygame

class ConveyorComponent(Component):
    """Component that moves items along a conveyor belt."""
    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)
        self.speed = self.machine.machineManager.GAME_STATE.get("machines.conveyor_speed")  # units per second
        self.direction = list(self.machine.callData(f"componentData.{self.name}.direction"))
        self.collision = dict(self.machine.callData(f"componentData.{self.name}.collision"))
        for i in range(self.machine.callData("rotation")):
            self.direction = [self.direction[1], -self.direction[0]]
            self.collision = {
                "left": self.collision["top"],
                "top": self.collision["right"],
                "right": self.collision["bottom"],
                "bottom": self.collision["left"],
            }

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