class UIComponent:
    """Base class for UI components. Can be extended to create custom components."""

    def __init__(self, name, element, config=None):
        self.name = name
        self.element = element
        self.manager = element.manager
        self.config = config or {}
        self.updateType = "continuous"  # Standard update type

    @property
    def priority(self):
        """Numeric draw priority for the component. Higher values draw later (on top).
        Components can set a `priority` key in their config to control ordering.

        If no explicit `priority` is provided in the component config, return
        a sensible default based on the component base name so common components
        render in a predictable order.
        """
        # explicit config value wins
        try:
            val = self.config.get("priority", None)
            if val is not None:
                return int(val)
        except Exception:
            pass

        # map base component name -> default priority (higher renders later)
        base = str(self.name or "").split("-", 1)[0]
        defaults = {
            "colorRect": 10,
            "particle": 20,
            "image": 30,
            "polygon": 40,
            "text": 50,
            "outline": 60,
            "container": 70,
        }
        return defaults.get(base, 0)

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
