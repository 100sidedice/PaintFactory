# Machines

This section documents the machine/component simulation system.

## Core files

- `src/World/machineManager.py` - machine/item ownership and world-level events
- `src/World/machine.py` - machine instance, component lifecycle, event routing
- `src/World/machineComponents/*.py` - reusable machine behaviors
- `data/tiles.json` - machine definitions and component config
- `data/sprites.json` - item metadata (`itemData.sell_price`, etc.)

## Architecture summary

Machines are data-driven and component-based:

1. `MachineManager.add_machine(machine_key, ...)`
2. Reads component list from `data["machines"][machine_key]["machineData"]["components"]`
3. `Machine.addComponent(...)` instantiates each component module/class
4. Components update by mode:
   - `continuous`
   - `timed`
   - event-driven via `handleEvent(...)`

## Event flow

- Component emits via `machine.pushEvent(...)`
- Machine forwards event to sibling components
- Machine forwards to `MachineManager.handleEvent(...)`
- Manager handles global outcomes (spawn item, sell item, money updates)

---

## Mini tutorial: Add a new machine type

### Step 1: Add definition in `data/tiles.json`

```json
"my-machine": {
  "image": "Assets/conveyor.png",
  "row": 1,
  "frames": 1,
  "size": [16, 16],
  "type": "machine",
  "machineData": {
    "name": "My Machine",
    "description": "Does something",
    "components": [
      {"name": "CollisionComponent", "data": {}},
      {"name": "MyCustomComponent", "data": {"foo": 1}}
    ]
  }
}
```

### Step 2: Add component module

`src/World/machineComponents/MyCustomComponent.py`

```python
from .Component import Component

class MyCustomComponent(Component):
    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)
        self.updateType = "continuous"

    def update(self, items, delta):
        pass
```

### Step 3: Spawn machine in startup or gameplay

```python
self.machine_manager.add_machine("my-machine", pos=(10, 10), rotation=0)
```

---

## Mini tutorial: Create a machine-to-manager event

From component:

```python
self.machine.pushEvent("my_event", {"value": 42}, self.name, self)
```

In `MachineManager.handleEvent(...)`:

```python
if event == "my_event":
    # handle world-level effect
    pass
```

---

## Built-in component examples

- `CollisionComponent` - collision checks + edge percentages
- `ConveyorComponent` - directional item movement on collision
- `SpawnComponent` - timed spawning
- `SellComponent` - converts item to money

## Common pitfalls

- Component naming mismatch:
  - JSON `name` must match module/class mapping used in `Machine.addComponent(...)`
- No sprite shown:
  - ensure machine key exists in machine sprite defs
- No money updates:
  - check `SellComponent` event and `MachineManager.handleEvent("item_sold", ...)`
