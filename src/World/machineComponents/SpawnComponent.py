from .Component import Component


class SpawnComponent(Component):
    """Component that spawns items at a specified location."""
    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)
        self.lastUpdate = 0
        self.updateInterval = self.machine.machineManager.GAME_STATE.get("machines.spawner_rate")  # Time interval between spawns in seconds
        self.spawnType = self.componentData["itemType"]
        self.offset = self.componentData.get("offset", (0, 0))
        self.updateType = "timed"  # Update type for this component is timed, meaning it updates based on a time interval

    def update(self, items, delta):
        """Spawn new items at the specified interval."""
        self.machine.pushEvent(
            "spawn",
            {
                "itemName": self.spawnType,
                "itemInfo": self.componentData.get("itemInfo", {"type": self.spawnType}),
                "pos": (
                    self.machine.pos[0] + self.offset[0],
                    self.machine.pos[1] + self.offset[1]
                )
            },
            self.name
        )

    def changeSpawnItem(self, newItem):
        """Change the type of item this spawner spawns."""
        self.spawnType = newItem