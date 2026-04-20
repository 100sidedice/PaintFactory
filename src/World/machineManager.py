from ..utils.gametimer import Timer
from .machine import Machine
from .item import Item

class MachineManager:
    def __init__(self, spriteManager, data={}, GAME_STATE=None, Input=None):
        self.machines = []
        self.items = []

        self.timer = Timer()
        self.timer.set(1.0, repeat=True)
        self.timer.add_loop_callback(self.updateState)

        self.runtime = 0
        self.spriteManager = spriteManager
        self.data = data
        self.GAME_STATE = GAME_STATE
        self.input = Input

    def update(self, delta):
        self.timer.update(delta)
        self.runtime += delta
        
        for item in self.items:
            item.update(delta)

        for machine in self.machines:
            machine.update(self.items, delta)

    def updateState(self):
        for machine in self.machines:
            machine.tickUpdate(self.items)

    def add_machine(self, machine_key, pos=(0, 0), rotation=0):
        machine_defs = self.data.get("machines", {}) if isinstance(self.data, dict) else {}
        if machine_key not in machine_defs:
            return None
        MACHINE = Machine(machine_key, pos=pos, rotation=rotation, data=self.data, spriteManager=self.spriteManager, machineManager=self)
        # Combine global default components (ALL) with machine-specific components
        # Combine global default components (ALL) with machine-specific components
        global_all = self.data["machines"]["ALL"]
        all_components = list(global_all["components"]) + list(self.data["machines"][machine_key]["machineData"]["components"])

        # Add components while allowing explicit duplicate instances via
        # a `component-id` (or `id`) field. If no explicit id is present,
        # avoid adding multiple components with the same base name.
        seen_bases = set()
        has_select = False
        for component in all_components:
            name_field = component["name"]
            explicit_id = component.get("component-id") or component.get("id")

            if explicit_id is not None:
                base_name = str(name_field)
                if "-" in base_name or str(explicit_id) in base_name:
                    component_name = base_name
                else:
                    component_name = f"{base_name}-{explicit_id}"
            else:
                component_name = name_field
                base_name = str(component_name).split("-", 1)[0]

            if explicit_id is None and base_name in seen_bases:
                continue

            component_data = dict(component["data"])
            if "offset" in component:
                component_data["offset"] = component["offset"]

            MACHINE.addComponent(component_name, self.data, componentData=component_data)

            seen_bases.add(base_name)
            if base_name == "SelectComponent":
                has_select = True

        # Ensure every machine gets a SelectComponent so right-clicks are handled
        if not has_select:
            MACHINE.addComponent("SelectComponent", self.data, componentData={})
        
        self.machines.append(MACHINE)
        return MACHINE

    def _tile_close(self, a, b, eps=0.001):
        try:
            return abs(float(a) - float(b)) <= float(eps)
        except Exception:
            return False

    def _machine_matches(self, machine, machine_key=None, pos=None, rotation=None):
        if machine is None:
            return False

        if machine_key is not None and str(machine.name) != str(machine_key):
            return False

        if rotation is not None:
            try:
                if int(machine.rotation) % 4 != int(rotation) % 4:
                    return False
            except Exception:
                return False

        if pos is not None:
            if not isinstance(pos, (list, tuple)) or len(pos) < 2:
                return False
            mx, my = machine.pos[0], machine.pos[1]
            px, py = pos[0], pos[1]
            if (not self._tile_close(mx, px)) or (not self._tile_close(my, py)):
                return False

        return True

    def remove_machine(self, machine=None, index=None, machine_key=None, pos=None, rotation=None):
        target = None
        if machine is not None:
            target = machine
        elif index is not None:
            try:
                idx = int(index)
                if 0 <= idx < len(self.machines):
                    target = self.machines[idx]
            except Exception:
                target = None
        else:
            for current in reversed(self.machines):
                if self._machine_matches(current, machine_key=machine_key, pos=pos, rotation=rotation):
                    target = current
                    break

        if target is None:
            return False

        sprite = getattr(target, "sprite", None)
        if sprite is not None and sprite in self.spriteManager.sprites:
            self.spriteManager.sprites.remove(sprite)

        if target in self.machines:
            self.machines.remove(target)
            return True
        return False


    def spawn_item(self, item_key, pos=(0, 0), info=None, base_item = True):
        if (len(self.items) < self.GAME_STATE.get("settings.max_items")) or not base_item:
            self.items.append(Item(item_key, pos=pos, spriteManager=self.spriteManager, info=info, id=len(self.items)))

    def remove_item(self, item = None):
        if item is None:
            return

        # Remove sprite so sold/removed items are no longer rendered.
        sprite = getattr(item, "sprite", None)
        if sprite is not None and sprite in self.spriteManager.sprites:
            self.spriteManager.sprites.remove(sprite)

        self.items.remove(item)
        
    def handleEvent(self, event, eventData, machineName=None, componentName=None, component=None):
        """Handle events pushed from machines and their components. This allows for communication between machines without them needing direct references to each other, enabling more modular and flexible machine designs."""
        if event == "spawn":
            self.spawn_item(eventData["itemName"], eventData["pos"], base_item=False)

        if event == "item_sold":
            item = eventData["item"]
            price = eventData["price"]
            self.GAME_STATE.set("inventory.money", self.GAME_STATE.get("inventory.money") + price)
            self.remove_item(item)

__all__ = ["MachineManager"]
