class MachineComponent:
    """Base class for machine components.
    Provides functionality to a sprite and defines the basic structure for machine components.
    """
    def __init__(self, sprite, machine, machineData):
        self.sprite = sprite
        self.machine = machine
        self.data = machineData
        self.type = machineData.get("type")
        self.state = "idle"

    def update(self, dt):
        pass

    def onItemGained(self, item):
        pass

    def defineAction(self, action):
        pass