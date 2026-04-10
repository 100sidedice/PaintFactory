# Machine Components Reference

This page documents built-in machine components in `src/World/machineComponents`.

## Base: `Component`

File: `src/World/machineComponents/Component.py`

```python
class Component:
    def __init__(self, name, machine, componentData=None):
        self.name = name
        self.machine = machine
        self.componentData = componentData or {}
        self.updateType = "ticks"
```

Common hooks:

- `update(items, delta)`
- `handleEvent(event, eventData, componentName, component)`

`updateType` controls scheduling:

- `continuous` - every frame
- `timed` - interval-based (uses `lastUpdate` + `updateInterval`)
- `event`/`static` - acts through events

---

## `CollisionComponent`

File: `src/World/machineComponents/CollisionComponent.py`

Purpose:

- Detect item overlap with machine rect
- Emit `collision` event with edge-distance percentages

Event payload emitted:

```python
{
  "item": item,
  "edges": {
    "left": ..., "right": ..., "top": ..., "bottom": ...
  },
  "delta": delta
}
```

Typical JSON use:

```json
{"name":"CollisionComponent", "data":{}}
```

---

## `ConveyorComponent`

File: `src/World/machineComponents/ConveyorComponent.py`

Purpose:

- Listen for `collision`
- Move item in configured direction if collision edge thresholds pass

Reads from:

- `machines.conveyor_speed` in game state
- component `data.direction`
- component `data.collision`

Example JSON:

```json
{
  "name":"ConveyorComponent",
  "data":{
    "direction":[1,0],
    "collision":{"left":0.49,"right":0,"top":0.49,"bottom":0.49}
  }
}
```

Rotation-aware:

- direction/collision map rotates by machine rotation

### Collision flow (end-to-end)

This is the runtime sequence for conveyor movement:

1. `CollisionComponent.update(...)` runs every frame (`updateType = "continuous"`).
2. It checks each item against the machine collision rect.
3. On hit, it calls `self.machine.pushEvent("collision", payload, self.name)`.
4. `Machine.pushEvent(...)` forwards that event to sibling components on the same machine.
5. `ConveyorComponent.handleEvent("collision", ...)` receives it.
6. Conveyor validates collision edge thresholds from its config.
7. If valid, it updates the item position using:
   - `direction`
   - conveyor speed from game state
   - frame `delta`

Pseudo-sequence:

```python
# CollisionComponent
if collision_rect.collidepoint(item_center):
  machine.pushEvent("collision", {"item": item, "edges": edges, "delta": delta}, "CollisionComponent")

# Machine.pushEvent forwards to other components...

# ConveyorComponent
def handleEvent(event, eventData, ...):
  if event != "collision":
    return
  if not passes_edge_thresholds(eventData["edges"]):
    return
  item = eventData["item"]
  dt = eventData["delta"]
  item.pos = (
    item.pos[0] + direction_x * speed * dt,
    item.pos[1] + direction_y * speed * dt,
  )
```

---

## `SpawnComponent`

File: `src/World/machineComponents/SpawnComponent.py`

Purpose:

- Timed item spawning
- Emits `spawn` event with item info

Key fields:

- `itemType`
- optional `itemInfo`
- optional `offset`

Uses state value:

- `machines.spawner_rate`

Example JSON:

```json
{
  "name":"SpawnerComponent",
  "data":{"itemType":"water"},
  "offset":[0,0]
}
```

Emitted payload:

```python
{
  "itemName": self.spawnType,
  "itemInfo": {...},
  "pos": (machine_x + ox, machine_y + oy)
}
```

---

## `SellComponent`

File: `src/World/machineComponents/SellComponent.py`

Purpose:

- Listen for `collision`
- Resolve item sell price from sprite/item data
- Emit `item_sold`

Example JSON:

```json
{"name":"SellComponent", "data":{}}
```

Sell event payload:

```python
{"item": item, "price": price}
```

Manager then:

- adds money to `inventory.money`
- removes item

### Collision -> sell flow

`SellComponent` uses the same collision event chain:

1. `CollisionComponent` emits `collision`.
2. `SellComponent.handleEvent("collision", ...)` receives item.
3. It resolves price from sprite/item data.
4. It emits `item_sold`.
5. `MachineManager.handleEvent("item_sold", ...)` updates money and removes the item.

---

## `InventoryComponent`

File: `src/World/machineComponents/InventoryComponent.py`

Status:

- Placeholder/incomplete in current codebase.

Use this for future logic like:

- buffering items
- machine internal storage
- transfer rules

---

## Practical composition examples

### Conveyor machine

```json
"components":[
  {"name":"CollisionComponent", "data":{}},
  {"name":"ConveyorComponent", "data":{"direction":[0,-1], "collision":{"left":0.125,"right":0.125,"top":0,"bottom":0}}}
]
```

### Spawner machine

```json
"components":[
  {"name":"SpawnerComponent", "data":{"itemType":"water"}, "offset":[0,0]},
  {"name":"CollisionComponent", "data":{}},
  {"name":"ConveyorComponent", "data":{"direction":[1,0], "collision":{"left":0.49,"right":0,"top":0.49,"bottom":0.49}}}
]
```

### Seller machine

```json
"components":[
  {"name":"CollisionComponent", "data":{}},
  {"name":"SellComponent", "data":{}}
]
```

---

## Notes

- Component names in JSON can include suffixes (`-1`, `-2`) for duplicates.
- Machine loader maps base name to module/class.
- Events are the main communication channel between components and manager.
