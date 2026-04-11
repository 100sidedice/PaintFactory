# UI Tutorials

This page gives short practical workflows.

## Runtime UI Editor (Sidebar)

The project includes an in-game UI editor sidebar for authoring `ui_elements` without manual JSON editing.

### Open / close and export

- Toggle editor mode: `Ctrl+E`
- Export current UI JSON: `Ctrl+P`
- Default export target: `data/ui_elements.edited.json`

### Sidebar tabs

#### 1) `elements`

- Select elements from a collapsible hierarchy tree (file explorer style)
- Click the disclosure marker (`v`/`>`) to expand/collapse children
- Double-click an element name to rename it inline (`Enter` apply, `Esc` cancel)
- Create elements by setting `new parent path` + `new element name`
- Reparent selected element using `reparent parent path` (+ optional new name)
- Delete selected subtree

Notes:
- Root `screen` element is protected and cannot be moved/resized/deleted/reparented.
- For array-driven elements, the authored base element stays editable; generated duplicates are locked.
- Locked rows are tinted and tagged with `[locked]`.

#### 2) `components`

- Add component by name (`container`, `text`, `image`, `eventReader`, etc.)
- Remove selected component
- Inspect component config in a collapsible key tree
- Select a config key path, then set/remove that value with the value field
- Double-click a leaf value in the config tree to edit it inline (caret shown in-row)
- Press `Enter` to apply inline edits, `Esc` to cancel inline edits
- Hex color leaf values show a swatch button inline in the tree (color picker)

#### 3) `metadata`

- Set/remove local `data` keys by path
- Apply `container.pos` / `container.size` values
- Load full selected element payload JSON
- Apply full selected element payload JSON
- If a value field contains a hex color (`#RRGGBB`), a color swatch button appears for picker-based editing.

`apply element` accepts full element payloads like:

```json
{
  "data": {"__visible": true},
  "container": {"pos": [10, 10], "size": [200, 60], "keywords": ["crop"], "opts": {}},
  "text": {"bind": "__label", "editable": false},
  "copy": "screen.someBase",
  "array": {"x": 1, "y": 3, "gap": [0, 36]}
}
```

This is the highest-control editing path when you want JSON-level behavior in-editor.

#### 4) `state`

- Browse `GAME_STATE` through a collapsible key-path tree (no manual key typing required).
- Select a key path in the tree, then `get`/`set` using the value JSON field.
- Double-click a leaf value in the tree to edit it inline (caret shown in-row).
- Press `Enter` to apply inline edits, `Esc` to cancel inline edits.
- Double-click a key name to rename it inline (`Enter` apply, `Esc` cancel).
- Hex color leaf values show a swatch button inline in the tree (color picker).

State lock rules:
- Top-level default keys are rename-locked.
- `settings.*` keys/values are locked from editing.
- Locked rows are tinted and tagged with `[locked]`.

### Canvas transform behavior while editor is open

- Click to select elements
- Drag to move selected element
- `Shift + drag` to resize selected element
- Arrow keys move selected element
- `Ctrl + Arrow` resizes selected element
- In Metadata tab, drag numeric transform fields (`pos_x`, `pos_y`, `size_w`, `size_h`) for micro adjustments.
- You can also type directly into those transform fields and press `Enter` to apply.

### Sidebar position toggle

- Use the small top-right arrow button in the sidebar header to move the editor panel left/right.

## Tutorial 1: Create a basic toggleable button

```json
"screen.myButton": {
  "data": {"__visible": true, "__on": false, "__color": "#333333"},
  "container": {"pos": [40, 40], "size": [140, 40], "keywords": ["crop", "input"], "opts": {}},
  "colorRect": {"color": "__color"},
  "outline": {"width": 2, "color": "#777777"},
  "input": {
    "mouseup.left": {"emit": "myButton.toggle", "scope": ["screen.myButton"]}
  },
  "eventReader": {
    "myButton.toggle": {"actions": [{"toggleValue": {"var": "__on"}}]}
  },
  "valueReader": {
    "__on": {"value": true, "condition": "==", "action": {"setValue": "__color", "value": "#118833"}},
    "__on-1": {"value": false, "condition": "==", "action": {"setValue": "__color", "value": "#333333"}}
  }
}
```

---

## Tutorial 2: Build a reusable style with `copy`

```json
"screen.baseCard": {
  "data": {"__visible": true},
  "container": {"pos": [0,0], "size": [180, 50], "keywords": ["crop"], "opts": {}},
  "colorRect": {"color": "#202020"},
  "outline": {"width": 1, "color": "#4A4A4A"}
},

"screen.cardA": {
  "copy": "screen.baseCard",
  "container": {"pos": [20, 20], "size": [180, 50], "keywords": ["crop"], "opts": {}}
},

"screen.cardB": {
  "copy": "screen.baseCard",
  "container": {"pos": [20, 80], "size": [220, 50], "keywords": ["crop"], "opts": {}},
  "colorRect": {"color": "#2A2A40"}
}
```

Only overridden fields need to be written.

---

## Tutorial 3: Generate repeated items with `array`

```json
"screen.list.item0": {
  "copy": "screen.baseItem",
  "array": {"x": 1, "y": 5, "gap": [0, 30]},
  "data": {"__label": "Item 0"},
  "input": {
    "mouseup.left": {"emit": "item.pick.0", "scope": ["screen.list"]}
  }
}
```

`array` now duplicates from the concrete authored element path (here `item0`) instead of using a virtual template node.

Template variables:
- `${index}` (x)
- `${index2}` (y)

If you need the old virtual-template behavior, set `"mode": "template"` in the `array` object.

---

## Tutorial 4: Create a dropdown (no custom code)

Pattern:
1. header element with current selected text
2. options container with `crop` + `scrollY`
3. option base + array-generated options
4. option click emits event
5. header listens and copies `$source.__label`

This pattern is implemented in your current `ui_elements.json` under `screen.dropdown`.

---

## Tutorial 5: Animate an image with `dynamicValue`

```json
"screen.avatar": {
  "data": {"__visible": true, "__frame": 0},
  "container": {"pos": [300, 80], "size": [120, 120], "keywords": ["crop"], "opts": {}},
  "dynamicValue": {
    "__frame": {"type": "loop", "min": 0, "max": 3, "speed": 8, "round": true}
  },
  "image": {
    "path": "Assets/paintbuckets.png",
    "frameSize": [16, 16],
    "row": 2,
    "index": "__frame",
    "columns": 4,
    "fit": "contain",
    "size": [100, 100]
  }
}
```

---

## Tutorial 6: Read external game state in UI

```json
"screen.money": {
  "data": {"__visible": true},
  "container": {"pos": ["__right", "__top"], "size": [180, 24], "keywords": ["crop"], "opts": {}},
  "text": {
    "bind": "__GAME_STATE.inventory.money",
    "editable": false,
    "fontSize": 18,
    "padding": [6, 2],
    "color": "$theme.text.color"
  }
}
```

`__GAME_STATE.<path>` always reads from runtime game state.

---

## Troubleshooting checklist

- Element invisible?
  - Check `__visible` on element and ancestors.
- Clicks not firing?
  - Verify container includes `input` keyword when needed.
  - Check `scope` and event names.
- Scroll not moving?
  - Container must include `scrollY`/`scrollX` keyword.
  - Content must exceed viewport.
- Child positions wrong?
  - Confirm hierarchy path and parent container keywords.
- Text/image clipping issues?
  - Ensure parent uses `crop` keyword.
