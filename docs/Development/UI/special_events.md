# UI Special Events & Variable Params

This page documents built-in game-level events you can trigger from UI JSON.

## Where this plugs in

Typical flow:

1. `input` emits a UI event (for example: `btn.spawn.click`)
2. `eventReader` listens for that event
3. `eventReader` action emits a manager event (for example: `game.machine.spawn`)

---

## Built-in manager events

These are handled by `UIManager.handleEvent(...)`.

### 1) Exit game

Event name:
- `game.exit`

Effect:
- Sets `game.running = False`
- Main loop exits cleanly

Example:

```json
"eventReader": {
  "btn.exit.click": {
    "actions": [
      {"emitEvent": {"name": "game.exit"}}
    ]
  }
}
```

---

### 2) Save game

Event name:
- `game.save`

Payload params:
- `path` (optional string)
  - relative paths are resolved from project base dir
  - default: `save.json`

Example:

```json
"eventReader": {
  "btn.save.click": {
    "actions": [
      {"emitEvent": {"name": "game.save", "eventData": {"path": "save_slot_1.json"}}}
    ]
  }
}
```

---

### 3) Spawn machine

Event name:
- `game.machine.spawn`

Payload params:
- `machine` (or `machine_key` / `key`) **required**
- `pos`: `[x, y]` (optional) or `x` + `y` (optional)
- `rotation` (optional, int; default `0`)

Example:

```json
"eventReader": {
  "btn.spawn.click": {
    "actions": [
      {
        "emitEvent": {
          "name": "game.machine.spawn",
          "eventData": {
            "machine": "conveyor",
            "x": 8,
            "y": 6,
            "rotation": 1
          }
        }
      }
    ]
  }
}
```

---

### 4) Remove machine

Event name:
- `game.machine.remove`

Payload match params (best effort):
- `index` (optional)
- `machine` (or `machine_key` / `key`) (optional)
- `pos`: `[x, y]` or `x` + `y` (optional)
- `rotation` (optional)

If multiple machines match, the most recently added matching machine is removed.

Example:

```json
"eventReader": {
  "btn.remove.click": {
    "actions": [
      {
        "emitEvent": {
          "name": "game.machine.remove",
          "eventData": {
            "machine": "conveyor",
            "x": 8,
            "y": 6
          }
        }
      }
    ]
  }
}
```

---

### Debug print

Event name:
- `debug.print` (alias: `print`)

Effect:
- Prints the event payload to the console (stdout) so you can inspect data emitted by UI actions or rules. This is intended for quick debugging of button connections and event payloads.

Example:

```json
"eventReader": {
  "btn.debug.click": {
    "actions": [
      {"emitEvent": {"name": "debug.print", "eventData": {"info": "button clicked", "source": "$source"}}}
    ]
  }
}
```

Notes:
- The printed payload uses Python's `repr()` so structures will be readable in the running process logs.
- Use this for quick inspection; remove or disable in production if console noise is a concern.

---

## `eventReader` action params

Supported action types:
- `setValue`
- `toggleValue`
- `emitEvent`

### `emitEvent` forms

String form:

```json
{"emitEvent": "game.exit"}
```

Object form:

```json
{
  "emitEvent": {
    "name": "game.save",
    "eventData": {"path": "save.json"},
    "scope": ["screen.hud"]
  }
}
```

Scope notes:
- The optional `scope` parameter controls which UI elements receive the emitted event. It accepts element paths or arrays of paths.
- You can use the special token `__self` inside `scope` to mean the emitting element itself. This is useful when an action should target only the element that triggered it.
- You may also use `__self.<suffix>` to target a descendant path relative to the emitter (for example `__self.settings` resolves to `<emitter_path>.settings`).

Example — emit to the emitter only:

```json
{
  "emitEvent": {
    "name": "some.event",
    "eventData": {"foo": "bar"},
    "scope": "__self"
  }
}
```

Example — emit to a child path under the emitter:

```json
{
  "emitEvent": {
    "name": "some.event",
    "eventData": {"foo": "bar"},
    "scope": ["__self.childGroup", "screen.hud"]
  }
}
```

`scope` is optional and applies to the emitted UI event broadcast.

---

## Variable/reference params

Inside `eventReader` values/payloads, these references are supported:

- `$self` -> current element path
- `$self.someVar` -> current element local data
- `$source` -> source element path from triggering event
- `$source.someVar` -> source element local data
- `$event.key` -> key from triggering event payload
- `$event.some.deep.key` -> nested payload key path

These references work recursively inside `eventData` objects/lists.

Example:

```json
"eventReader": {
  "btn.spawn.click": {
    "actions": [
      {
        "emitEvent": {
          "name": "game.machine.spawn",
          "eventData": {
            "machine": "$self.__machineKey",
            "x": "$self.__spawnX",
            "y": "$self.__spawnY",
            "rotation": "$self.__spawnRotation",
            "sourcePath": "$source",
            "triggerType": "$event.trigger"
          }
        }
      }
    ]
  }
}
```
