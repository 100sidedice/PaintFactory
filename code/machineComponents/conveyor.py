import pygame
from machineComponents.machineComponent import MachineComponent


class ConveyorComponent(MachineComponent):
    """Simple conveyor component: on global tick, move items from this
    machine's tile to its output neighbor (teleport for simplicity).
    """
    DIR_ORDER = ['up', 'right', 'down', 'left']
    DIR_VECTORS = {'up': (0, -1), 'right': (1, 0), 'down': (0, 1), 'left': (-1, 0)}

    def __init__(self, sprite, machine, machineData, machineManager):
        super().__init__(sprite, machine, machineData, machineManager)
        # register to the machine
        try:
            machine.register_component(self)
        except Exception:
            pass

    def on_tick(self):
        # find items on the machine's tile
        if self.machineManager is None or self.machineManager.tilemap is None:
            return
        tw, th = self.machineManager.tilemap.tile_size
        mx = int(self.machine.pos.x)
        my = int(self.machine.pos.y)

        # determine output direction from machine data inputs
        inputs = self.data.get('inputs', {}) or {}
        out_dir = None
        for d, info in inputs.items():
            if info.get('type') == 'output':
                out_dir = d
                break
        if out_dir is None:
            return

        # rotate direction by machine.rotation (0..3)
        try:
            rot = int(getattr(self.machine, 'rotation', 0)) % 4
        except Exception:
            rot = 0
        idx = self.DIR_ORDER.index(out_dir) if out_dir in self.DIR_ORDER else 0
        out_idx = (idx + rot) % 4
        final_dir = self.DIR_ORDER[out_idx]
        dx, dy = self.DIR_VECTORS[final_dir]

        # move any items sitting on this tile to the neighbor tile
        for it in list(self.machineManager.items):
            try:
                ix = int(round(it.pos.x / tw))
                iy = int(round(it.pos.y / th))
            except Exception:
                continue
            if ix == mx and iy == my:
                # teleport item to target tile
                target_x = (mx + dx) * tw
                target_y = (my + dy) * th
                it.pos = pygame.Vector2(target_x, target_y)


__all__ = ["ConveyorComponent"]
