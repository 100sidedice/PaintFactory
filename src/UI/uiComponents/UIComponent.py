class UIComponent:
    """Base class for UI components. Can be extended to create custom components."""
    def __init__(self, name, element, config=None):
        self.name = name
        self.element = element
        self.manager = element.manager
        self.config = config or {}
        self.updateType = "continuous" # Standard update type

    def update(self, delta):
        """Update the component's state based on time delta."""
        pass

    def draw(self, surface):
        """Draw this component if it has a visual representation."""
        pass

    def handleEvent(self, event, eventData, componentName, component):
        """Handle an event directed at this component."""
        pass

    @property
    def input(self):
        return self.element.input

    def get_rect(self):
        container = self.element.getComponent("container")
        if container is None:
            return None
        return container.get_rect()

    