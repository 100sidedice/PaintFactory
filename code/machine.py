import pygame

class Machine:
    def __init__(self, name, pos, rotation, data, spriteManager, machineManager):
        self.name = name
        self.components = {}
        self.runtime = 0
        self.rotation = rotation
        self.data = data

        self.pos = pos
        self.machineManager = machineManager
        
        # not setting self.spriteManager as we just need them to add the sprite, no need to keep a reference to it after that
        self.sprite = spriteManager.add_sprite(self.name, pos, self.rotation)


    def update(self, items, delta):
        self.runtime += delta   
        for component in self.components:
            # Update continuous components every frame [ex. collision detection]
            if self.components[component].updateType == "continuous":
                self.components[component].update(items, delta)

            # Update timed components based on their interval [ex. spawners spawning items every 2 seconds]
            if self.components[self.component].updateType == "timed":
                if self.components[component].lastUpdate + self.components[component].updateInterval <= self.runtime:
                    self.components[component].update(items, delta)
                    self.components[component].lastUpdate = self.runtime

    def tickUpdate(self, items):
        for component in self.components:
            # Update component data every tick [ex. upgrading conveyor speed]
            if hasattr(self.components[component], "updateData"):
                self.components[component].updateData(items, 0)

    def addComponent(self, componentName, data, cached=None):
        if cached is None:
            cached = {}

        base_name = componentName.split("-", 1)[0]

        component = cached.get(componentName)
        if component is None:
            component = cached.get(base_name)
        if component is None:
            component = data.machineComponents.get(base_name)

        self.components[componentName] = component

    def removeComponent(self, componentName):
        if componentName in self.components: del self.components[componentName]

    def getComponent(self, componentName):
        return self.components.get(componentName, None)
    
    def pushEvent(self, event, eventData, componentName = None, component = None):
        if componentName in self.components:
            if hasattr(self.components[componentName], "handleEvent"):
                self.components[componentName].handleEvent(event, eventData, componentName, component)

        self.machineManager.pushEvent(event, eventData, self.name, componentName, component)


    def callData(self,dataKey):
        """Call data related to this machine, such as the sprite or position. Used for components to get data from the machine without needing to know about the machine's internal structure."""
        match dataKey:
            case "pos": return self.pos
            case "rotation": return self.rotation
            case "rect" :return self.sprite.rect
            case "sprite": return self.sprite
            case _: return self.data.get(dataKey, None)