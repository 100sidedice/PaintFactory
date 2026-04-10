from ..utils.gametimer import Timer
from .machine import Machine
from .item import Item

#from main import GAME_STATE


class MachineManager:
    def __init__(self, spriteManager, data={}, GAME_STATE=None):
        self.machines = []
        self.items = []

        self.timer = Timer()
        self.timer.set(1.0, repeat=True)
        self.timer.add_loop_callback(self.updateState)

        self.runtime = 0
        self.spriteManager = spriteManager
        self.data = data
        self.GAME_STATE = GAME_STATE

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
        MACHINE = Machine(machine_key, pos=pos, rotation=rotation, data=self.data, spriteManager=self.spriteManager, machineManager=self)
        for component in self.data["machines"][machine_key]["machineData"]["components"]:
            component_data = dict(component["data"])
            if "offset" in component:
                component_data["offset"] = component["offset"]
            MACHINE.addComponent(component["name"], self.data, componentData=component_data)
        
        self.machines.append(MACHINE)


    def spawn_item(self, item_key, pos=(0, 0), info=None, base_item = True):
        if (len(self.items) < self.GAME_STATE.get("settings.max_items")) or not base_item:
            self.items.append(Item(item_key, pos=pos, spriteManager=self.spriteManager, info=info, id=len(self.items)))

    def remove_item(self, item = None):
        if item is None:
            return

        # Remove sprite so sold/removed items are no longer rendered.
        sprite = getattr(item, "sprite", None)
        if sprite is not None and sprite in self.spriteManager.sprites:
            self.spriteManager.sprites.remove(sprite)

        self.items.remove(item)
        
    def handleEvent(self, event, eventData, machineName=None, componentName=None, component=None):
        """Handle events pushed from machines and their components. This allows for communication between machines without them needing direct references to each other, enabling more modular and flexible machine designs."""
        if event == "spawn":
            self.spawn_item(eventData["itemName"], eventData["pos"], base_item=False)

        if event == "item_sold":
            item = eventData["item"]
            price = eventData["price"]
            self.GAME_STATE.set("inventory.money", self.GAME_STATE.get("inventory.money") + price)
            self.remove_item(item)

__all__ = ["MachineManager"]
