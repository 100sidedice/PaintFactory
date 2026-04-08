import pygame

class Machine:
    def __init__(self, name, pos, rotation, data, spriteManager, machineManager):
        self.name = name
        self.components = {}
        self.componentData = {}
        self.runtime = 0
        self.rotation = rotation
        self.data = data

        self.pos = pos
        self.machineManager = machineManager
        
        # not setting self.spriteManager as we just need them to add the sprite, no need to keep a reference to it after that
        self.sprite = spriteManager.add_sprite(self.name, pos, self.rotation)


    def update(self, items, delta):
        self.runtime += delta
        for component in self.components.values():
            # Update continuous components every frame [ex. collision detection]
            if component.updateType == "continuous":
                component.update(items, delta)

            # Update timed components based on their interval [ex. spawners spawning items every 2 seconds]
            if component.updateType == "timed":
                if component.lastUpdate + component.updateInterval <= self.runtime:
                    component.update(items, delta)
                    component.lastUpdate = self.runtime

    def tickUpdate(self, items):
        for component in self.components:
            # Update component data every tick [ex. upgrading conveyor speed]
            if hasattr(self.components[component], "updateData"):
                self.components[component].updateData(items, 0)

    def addComponent(self, componentName, data, componentData):
        base_name = componentName.split("-", 1)[0]

        module_name = base_name
        class_name = base_name

        if base_name == "SpawnerComponent":
            module_name = "SpawnComponent"
            class_name = "SpawnComponent"

        component_module = data["machineComponents"][module_name]
        component_class = getattr(component_module, class_name)

        self.componentData[componentName] = componentData
        component = component_class(componentName, self, componentData)

        self.components[componentName] = component

    def removeComponent(self, componentName):
        if componentName in self.components: del self.components[componentName]

    def getComponent(self, componentName):
        return self.components.get(componentName, None)
    
    def pushEvent(self, event, eventData, componentName = None, component = None):
        for name, current in self.components.items():
            if name == componentName:
                continue
            if hasattr(current, "handleEvent"):
                current.handleEvent(event, eventData, componentName, component)

        self.machineManager.handleEvent(event, eventData, self.name, componentName, component)


    def callData(self,dataKey):
        """Call data related to this machine, such as the sprite or position. Used for components to get data from the machine without needing to know about the machine's internal structure."""
        if dataKey == "componentData":
            return self.componentData

        if dataKey.startswith("componentData."):
            segments = dataKey.split(".")
            current = self.componentData
            for key in segments[1:]:
                current = current[key]
            return current

        match dataKey:
            case "pos": return self.pos
            case "rotation": return self.rotation
            case "rect":
                tw, th = self.sprite.tile_size
                x = int(self.pos[0] * tw)
                y = int(self.pos[1] * th)
                return pygame.Rect(x, y, tw, th)
            case "sprite": return self.sprite
            case _: return self.data.get(dataKey, None)