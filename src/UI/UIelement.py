from ..utils.path_dict import PathDict


class UIelement:
    def __init__(self, path, elmData, data, manager, input):
        self.path = path
        self.name = path
        self.components = {}
        self.component_order = []
        self.runtime = 0
        self.data = data
        self.manager = manager
        self.componentName = "uiComponents" # used for looking up components; ex. data["components"][componentName]
        self.elmData = elmData
        self.input = input
        self.local_data = dict(elmData.get("data", {}))

        self._initialize_components()

    def _initialize_components(self):
        for component_name, component_data in self.elmData.items():
            if component_name == "data":
                continue
            self.addComponent(component_name, self.data, component_data)

    def update(self, delta):
        self.runtime += delta
        for component_name in self.component_order:
            component = self.components[component_name]
            if component.updateType == "continuous":
                component.update(delta)

    def draw(self, surface):
        for component_name in self.component_order:
            component = self.components[component_name]
            if hasattr(component, "draw"):
                component.draw(surface)

    def addComponent(self, componentName, data, componentData=None):
        """Add a component to this element"""
        base_name = componentName.split("-", 1)[0]
        module_name = f"{base_name}Component"
        class_name = f"{base_name[0].upper()}{base_name[1:]}Component"
        component_module = data[self.componentName][module_name]
        component_class = getattr(component_module, class_name)
        component = component_class(componentName, self, componentData or {})
        self.components[componentName] = component
        self.component_order.append(componentName)

    def removeComponent(self, componentName):
        """Remove a component from this element"""
        if componentName in self.components:
            del self.components[componentName]
        if componentName in self.component_order:
            self.component_order.remove(componentName)

    def getComponent(self, componentName):
        """Get a component from this element by name"""
        return self.components.get(componentName, None)
    
    def pushEvent(self, event, eventData, componentName = None, component = None):
        """Push an event to all components and the manager."""
        for name, current in self.components.items():
            if name == componentName:
                continue
            if hasattr(current, "handleEvent"):
                current.handleEvent(event, eventData, componentName, component)

        self.manager.handleEvent(event, eventData, self.path, componentName, component)

    def handleEvent(self, event, eventData, sourcePath=None, componentName=None, component=None):
        for name, current in self.components.items():
            if sourcePath == self.path and name == componentName:
                continue
            if hasattr(current, "handleEvent"):
                current.handleEvent(event, eventData, componentName, component)

    def get_parent(self):
        if "." not in self.path:
            return None
        parent_path = self.path.rsplit(".", 1)[0]
        return self.manager.getElement(parent_path)

    def get_rect(self):
        container = self.getComponent("container")
        if container is None:
            return None
        return container.get_rect()

    def is_visible(self):
        return bool(self.local_data.get("__visible", True))

    def get_data(self, path, default=None):
        return PathDict.get(self.local_data, path, default)

    def set_data(self, path, value):
        PathDict.set(self.local_data, path, value)


    def callData(self,dataKey):
        """Allows a component to access data from here or the manager"""
        if dataKey.startswith("manager."):
            return self.manager.callData(dataKey[8:])
        if dataKey.startswith("data."):
            return self.get_data(dataKey[5:])
        
        match dataKey: 
            case "componentData": return self.elmData
            case "rect": return self.get_rect()
            case _: return self.data.get(dataKey, None)

    def modifyData(self, dataKey, value):
        """Allows a component to modify data from here"""
        if dataKey.startswith("data."):
            self.set_data(dataKey[5:], value)
            return
        self.data[dataKey] = value