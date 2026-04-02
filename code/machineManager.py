import pygame
from spritesManager import SpriteManager
from machineComponents.item import Item
from gametimer import Timer
from machine import Machine


class MachineManager:
    """Central manager for machines and items.

    Responsibilities:
      - Track registered machines
      - Track spawned items
      - Provide `spawnItem(itemKey, machine, rotation=0)` for machine components
      - Update and draw items and machines
    """

    def __init__(self, tilemap=None, sprite_manager=None):
        self.tilemap = tilemap
        self.sprite_manager = sprite_manager
        self.machines = []
        self.items = []
        # global tick timer for machines (default 1s interval)
        self.global_timer = Timer(duration=1.0, repeat=True)
        # call on_tick on all machines each tick
        self.global_timer.add_loop_callback(self._on_global_tick)

    def register_machine(self, machine):
        if machine not in self.machines:
            self.machines.append(machine)
        return machine

    def unregister_machine(self, machine):
        try:
            self.machines.remove(machine)
        except ValueError:
            pass

    def spawnItem(self, itemKey, machine, rotation=0):
        """Spawn an item by key produced by a machine.

        `itemKey` corresponds to entries in `data/sprites.json`.
        `machine` is expected to be a sprite-like object with a `pos` (tile coords)
        or a dict with `x`/`y`. Rotation is 0..3.
        Returns the created Item.
        """
        # try to load an item sprite from sprite defs
        sprite = SpriteManager.load_from_json(itemKey, pos=(0, 0))
        texture = None
        if sprite and getattr(sprite, 'frames', None):
            texture = sprite.frames[0]
        # fallback: create a simple surface
        if texture is None:
            if self.tilemap is not None:
                tw, th = self.tilemap.tile_size
            else:
                tw, th = (16, 16)
            texture = pygame.Surface((tw, th), pygame.SRCALPHA)
            texture.fill((255, 0, 255))

        itm = Item(itemKey, texture, self.items, rotation=rotation)

        # set position (convert from tile coords to world pixels if tilemap available)
        tw, th = (1, 1)
        if self.tilemap is not None:
            tw, th = self.tilemap.tile_size
        try:
            itm.pos = pygame.Vector2(machine.pos.x * tw, machine.pos.y * th)
        except Exception:
            try:
                itm.pos = pygame.Vector2(machine.get('x', 0) * tw, machine.get('y', 0) * th)
            except Exception:
                itm.pos = pygame.Vector2(0, 0)

        self.items.append(itm)
        return itm

    def update(self, dt):
        # advance global timer (triggers machine ticks)
        try:
            self.global_timer.update(dt)
        except Exception:
            pass

        # update machines (per-frame) and items
        for m in list(self.machines):
            try:
                m.update(dt)
            except Exception:
                pass

        for it in list(self.items):
            try:
                it.update(dt)
            except Exception:
                pass

    def _on_global_tick(self):
        for m in list(self.machines):
            try:
                m.on_tick()
            except Exception:
                pass

    def draw(self, surface, camera=None):
        for it in list(self.items):
            it.draw(surface, camera=camera)


    # convenience helpers
    def clear_items(self):
        self.items.clear()

    def create_machine(self, key, machineData, pos=(0,0), rotation=0, sprite=None):
        m = Machine(key, data=machineData, pos=pos, rotation=rotation, machineManager=self, sprite=sprite)
        self.register_machine(m)
        # create a visual sprite for the machine (guarantee via sprite_manager when available)
        if sprite is None and getattr(self, 'sprite_manager', None) is not None:
            try:
                sprite = self.sprite_manager.add_from_json(key, pos=pos, rotation=rotation)
            except Exception:
                sprite = None

        # attach default components based on machineData.action
        action = machineData.get('action') if machineData else None
        if action == 'move':
            try:
                from machineComponents.conveyor import ConveyorComponent
                ConveyorComponent(sprite, m, machineData, self)
            except Exception:
                pass
        return m


__all__ = ["MachineManager"]
