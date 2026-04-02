class Machine:
    """Represents a placed machine on the map.

    - `key` is the tile key (e.g., 'spawner')
    - `data` is the machineData dict from tiles.json
    - `pos` is tile coords (x,y)
    - `rotation` is 0..3
    - `components` is a list of MachineComponent instances attached to this machine
    """

    def __init__(self, key, data=None, pos=(0, 0), rotation=0, machineManager=None, sprite=None):
        self.key = key
        self.data = data or {}
        # tile coordinates
        self.pos = type('P', (), {'x': pos[0], 'y': pos[1]})()
        try:
            self.rotation = int(rotation) % 4
        except Exception:
            self.rotation = 0
        self.components = []
        self.machineManager = machineManager
        self.sprite = sprite
        self.state = 'idle'

    def register_component(self, comp):
        if comp not in self.components:
            self.components.append(comp)
            return comp

    def unregister_component(self, comp):
        try:
            self.components.remove(comp)
        except ValueError:
            pass

    def update(self, dt):
        for c in list(self.components):
            try:
                c.update(dt)
            except Exception:
                pass

    def on_tick(self):
        """Called by the global timer once per tick. Default behavior: delegate
        to components' on_tick or perform the action defined in `self.data`.
        """
        # let components handle ticks first
        handled = False
        for c in list(self.components):
            try:
                if hasattr(c, 'on_tick'):
                    c.on_tick()
                    handled = True
            except Exception:
                pass

        if handled:
            return

        # fallback: simple action from data
        action = self.data.get('action')
        if action == 'spawn':
            item_key = self.data.get('spawn_item') or self.data.get('properties', {}).get('item') or 'water'
            if self.machineManager is not None:
                try:
                    self.machineManager.spawnItem(item_key, self, rotation=self.rotation)
                except Exception:
                    pass
        # other actions (move, transform, etc.) should be implemented in components


__all__ = ['Machine']
