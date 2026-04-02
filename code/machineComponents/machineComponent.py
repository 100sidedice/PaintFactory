class MachineComponent:
    """Base class for machine components.
    Provides functionality to a sprite and defines the basic structure for machine components.
    """
    def __init__(self, sprite, machine, machineData, machineManager):
        self.sprite = sprite
        self.machine = machine
        self.data = machineData
        self.type = machineData.get("type")
        self.state = "idle"
        self.machineManager = machineManager

    def update(self, dt):
        pass

    def on_tick(self):
        """Called by the global machine tick. Default behavior: perform
        configured action (e.g. spawn).
        """
        action = self.data.get('action')
        if action:
            self.doAction(action)

    def doAction(self, actionType, **kwargs):
        if actionType == "spawn":
            # allow machineData to define spawn item key via 'spawn_item' or properties.item
            item_key = self.data.get('spawn_item') or self.data.get('properties', {}).get('item') or kwargs.get('itemKey') or 'bucket'
            rotation = kwargs.get('rotation', getattr(self.sprite, 'rotation', getattr(self.machine, 'rotation', 0)))
            if self.machineManager is not None:
                self.machineManager.spawnItem(item_key, self.machine, rotation=rotation)
