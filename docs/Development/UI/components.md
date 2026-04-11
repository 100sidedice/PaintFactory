# UI Components Reference

This file documents the current built-in components and common options.

## 1) `container`
Controls position, size, layout behavior, and scrolling.

Common fields:

```json
"container": {
  "pos": [20, 20],
  "size": [240, 120],
  "keywords": ["crop"],
  "opts": {}
}
```

### `keywords`

- `static` - ignores parent layout transforms
- `globalParent` - bypasses parent-relative positioning
- `crop` - clips drawing to this container rect
- `grid` - grid layout for direct children
- `stretch`, `stretchX`, `stretchY` - size children to container content
- `flex`, `flexX`, `flexY` - auto-size this container from children
- `scroll`, `scrollable`, `scrollX`, `scrollY` - scrolling container

### `opts`

Layout/spacing:
- `padding` or per-mode fallback keys:
  - `flexPadding`, `stretchPadding`, `gridPadding`

Grid:
- `columns`
- `gap` (`[x,y]` or number)
- `cellSize` (`[w,h]`)

Scroll:
- `limits`: `element` | `values` | `infinite`
- `scrollSpeed`
- `scrollImpulse`
- `scrollDamping`
- `scrollX`, `scrollY` (optional explicit toggles)
- `minX`, `maxX`, `minY`, `maxY` for `limits: "values"`

Transform:
- `overrideTransform` (default true)
  - true: layout can shrink/grow below base size
  - false: keeps at least base size

---

## 2) `colorRect`
Draws a rectangle in the element bounds.

```json
"colorRect": {
  "color": "#2A2A2A",
  "alpha": 255
}
```

`color` supports:
- hex string (`#RRGGBB`)
- hex string with alpha (`#RRGGBBAA`)
- RGB array (`[r,g,b]`)
- RGBA array (`[r,g,b,a]`)
- local variable (`"__color"`)
- theme variable (`"$theme.text.color"`)

`alpha` is optional and overrides color alpha when present (`0..255`).

---

## 3) `outline`
Draws rectangular border.

```json
"outline": {
  "width": 2,
  "color": "#4A4A4A"
}
```

---

## 4) `polygon`
Draws a polygon from custom vertex points.

```json
"polygon": {
  "vertices": [[0, 0], [90, 10], [50, 70]],
  "color": "#55AAFF",
  "alpha": 255,
  "width": 0
}
```

Notes:
- `vertices` are local points `[x, y]`.
- `width = 0` fills the polygon.
- `width > 0` draws outline-only polygon stroke.
- The element `container.size` is auto-updated to the polygon bounding box.
- In the runtime editor, add `polygon`, then use component value/path editing to edit `vertices`.

---

## 5) `text`
Renders text and supports editable mode with caret/focus.

```json
"text": {
  "bind": "__text",
  "editable": true,
  "placeholder": "Type...",
  "fontSize": 20,
  "padding": [8, 8],
  "align": "left",
  "verticalAlign": "top",
  "color": "$theme.text.color",
  "placeholderColor": "$theme.text.placeholder_color",
  "caretColor": "$theme.caret.color",
  "caretBlinkRate": "$theme.caret.blink_rate",
  "maxLength": 24,
  "blurOnEnter": true,
  "editingFlag": "__editingText"
}
```

Binding supports external state:
- `"__GAME_STATE.inventory.money"`

Alignment options:
- `align`: `left` | `center` | `right`
- `verticalAlign`: `top` | `middle` | `bottom`

---

## 6) `input`
Input-triggered event emitter.

```json
"input": {
  "mouseup.left": {
    "duration": 0,
    "emit": "button.clicked",
    "scope": ["screen.button"]
  }
}
```

Triggers currently supported:
- `mouseup.left|middle|right`
- `mousedown.left|middle|right`

Optional rule fields:
- `duration` (cooldown)
- `consume` (default true)
- `conditions` array
- `scope` array

---

## 7) `valueReader`
Checks local variable values each frame and applies actions.

```json
"valueReader": {
  "__editingText": {
    "value": true,
    "condition": "==",
    "action": {"setValue": "__outlineColor", "value": "$theme.focus.outline_color"}
  }
}
```

---

## 8) `eventReader`
Consumes emitted events and runs actions.

```json
"eventReader": {
  "dropdown.option.*": {
    "actions": [
      {"setValue": {"var": "__selectedText", "value": "$source.__label"}}
    ]
  }
}
```

Features:
- exact event keys
- wildcard suffix keys (`prefix*`)
- actions:
  - `setValue`
  - `toggleValue`
  - `emitEvent`
- dynamic values:
  - `$source.someVar`
  - `$event.somePayloadKey`

See manager/game event names and payload params in:
- `docs/Development/UI/special_events.md`

---

## 9) `image`
Draws preloaded image/spritesheet data.

```json
"image": {
  "path": "Assets/paintbuckets.png",
  "frameSize": [16, 16],
  "row": 2,
  "index": "__frame",
  "columns": 4,
  "fit": "contain",
  "size": [120, 120],
  "anchor": "center",
  "offset": [0, 0],
  "smooth": false,
  "rotation": 0,
  "flipX": false,
  "flipY": false,
  "alpha": 255,
  "tint": "#FFFFFF",
  "tintAlpha": 120
}
```

`path` should reference preloaded assets for best performance.

---

## 10) `dynamicValue`
Animates local variables over time.

```json
"dynamicValue": {
  "__frame": {"type": "loop", "min": 0, "max": 3, "speed": 8, "round": true},
  "__pulse": {"type": "sine", "min": 0, "max": 1, "speed": 1.2}
}
```

Types:
- `loop`
- `pingpong`
- `sine`

Use animated variables anywhere a component supports variable bindings.

---

## 11) `hover`
Fires events when the pointer enters or leaves the element's rect. Useful for hover-driven menus, tooltips, and state toggles.

Configuration:

```json
"hover": {
  "on_hover_start": "event.name"  // or an object (see below)
  "on_hover_end": "event.name"
}
```

Fields:
- `on_hover_start`: String or Object — event to emit when pointer enters.
- `on_hover_end`: String or Object — event to emit when pointer leaves.

String form:
- Provide an event name string to emit a simple event.

Object form:
- Use an object to supply `name` (or `emit`), optional `eventData` (object), and optional `scope` (string or array). Example:

```json
"hover": {
  "on_hover_start": {
    "name": "menu.open",
    "scope": "__self",
    "eventData": { "from": "hover" }
  }
}
```

Notes:
- The component computes hover using the element's `container` rect — ensure the element has a `container` component so it has bounds.
- Emitted payloads automatically include `source` (the emitting element path) and `trigger` (e.g., `hover.start` / `hover.end`). If you provide `eventData`, its keys are merged into the payload.
- `scope` supports the usual values including the special token `__self` (see `docs/Development/UI/special_events.md`) to target the emitter itself or `__self.<subpath>` to target a child path of the emitter.

