from Component import Component
from main import GAME_STATE


class SpawnComponent(Component):
    """Component that spawns items at a specified location."""
    def __init__(self, name, machine):
        super().__init__(name, machine)
        self.lastUpdate = 0
        self.updateInterval = GAME_STATE.get("machines.spawner_rate")  # Time interval between spawns in seconds
        self.spawnType = "water"  # Type of item to spawn, can be extended to support different item types
        self.updateType = "timed"  # Update type for this component is timed, meaning it updates based on a time interval

    def update(self, items, delta):
        """Spawn new items at the specified interval."""
        self.machine.pushEvent("spawn", {"itemName": self.spawnType, "pos": self.machine.pos}, self.name)