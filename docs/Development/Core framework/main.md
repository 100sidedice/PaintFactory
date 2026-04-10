# Core Framework

This section documents the game bootstrap/runtime loop and shared architecture pieces.

## Core runtime flow

Primary file: `src/main.py`

1. `Game.__init__()` initializes pygame, display, and clock.
2. `preloadAssets()` loads images/json/text/modules into `self.data`.
3. `start()` constructs managers (`UI`, `World`, camera, game state).
4. `run()` executes frame loop:
   - `Input.update(dt)`
   - `update(dt)`
   - `draw()`

## Key modules

- `src/main.py` - app entry + orchestration
- `src/World/gameState.py` - state container with path get/set
- `src/utils/path_dict.py` - nested path read/write helpers
- `src/UI/input.py` - unified input + lock/passcode system

## Asset preloading contract

Assets are declared in `preloadAssets()` as entries with:

- `type`: `image` | `json` | `text` | `module` | `folder`
- `path`: project-relative path
- `name`: alias key into `self.data`

The loader also stores both alias and path as keys in `self.data`.

---

## Mini tutorial: Add a new preloaded config file

### Step 1: Add preload entry in `src/main.py`

```python
{"type": "json", "path": "data/my_rules.json", "name": "rules"}
```

### Step 2: Read from manager/component

```python
rules = self.manager.callData("rules")
```

---

## Mini tutorial: Add a new runtime manager

### Step 1: Create manager file

`src/MySystem/my_manager.py`

```python
class MyManager:
    def __init__(self, data):
        self.data = data

    def update(self, dt):
        pass

    def draw(self, surface):
        pass
```

### Step 2: Initialize in `Game.start()`

```python
self.my_manager = MyManager(self.data)
```

### Step 3: Hook into frame loop

```python
self.my_manager.update(dt)
self.my_manager.draw(self.screen)
```

---

## Input lock/passcode notes

`src/UI/input.py` supports lock ownership to prevent input bleed.

- `Input.lock(passcode, {"type": "unlock"})`
- `Input.unlock(passcode)`
- getters accept optional passcode(s)

Use passcodes when multiple systems overlap input regions.

---

## Troubleshooting

- Import errors from script execution:
  - Use `python3 -m src` from project root.
- Missing data keys:
  - verify preloaded `name` and path aliases in `self.data`.
- Event/timing jitter:
  - ensure systems use frame `dt` from main loop.
