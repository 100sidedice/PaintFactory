import pygame
from spritesManager import SpriteManager
from gametimer import Timer
from machine import Machine


class MachineManager:
    def __init__(self, spriteManager, data={}):
        self.machines = []
        self.items = []

        self.timer = Timer()
        self.timer.set(1.0, repeat=True)
        self.timer.add_loop_callback(self.updateState)

        self.runtime = 0
        self.spriteManager = spriteManager
        self.data = data

    def update(self, delta):
        self.timer.update(delta)
        self.runtime += delta
        
        for item in self.items:
            item.update(delta)

        for machine in self.machines:
            machine.update(self.items, delta)

    def updateState(self):
        for machine in self.machines:
            machine.tickUpdate(self.items)

    def add_machine(self, machine_key, pos=(0, 0), rotation=0):
        self.machines.append(Machine(machine_key, pos=pos, rotation=rotation, data=self.data, spriteManager=self.spriteManager, machineManager=self))

__all__ = ["MachineManager"]
