from Component import Component
import pygame

from main import GAME_STATE

class ConveyorComponent(Component):
    """Component that moves items along a conveyor belt."""
    def __init__(self, name, machine, direction):
        super().__init__(name, machine)
        self.speed = GAME_STATE.get("machines.conveyor_speed")  # units per second
        self.direction = [0,1]
        for i in range(self.machine.callData("rotation")):
            self.direction = [self.direction[1], -self.direction[0]]  # basic matrix rotation to rotate the direction vector based on the machine's rotation

        self.updateType = "static"  # Only update on events, not every tick

 
    def handleEvent(self, event, eventData, componentName, component):
        """Handle events related to items on the conveyor."""
        if event == "collision" and eventData["item"] in self.machine.items:
            item = eventData["item"]
            # Start moving the item in the conveyor's direction
            item.pos = (
                item.pos[0] + self.direction[0] * self.speed,
                item.pos[1] + self.direction[1] * self.speed
            )