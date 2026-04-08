class Component:
    """Base class for machine components."""
    def __init__(self, name, machine):
        self.name = name
        self.machine = machine
        self.updateType = "ticks" # Standard update type

    def update(self, items, delta):
        """Update the component's state based on items and time delta."""
        pass

    def handleEvent(self, event, eventData, componentName, component):
        """Handle an event directed at this component."""
        pass