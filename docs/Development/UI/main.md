# UI System Overview

This project uses a JSON-driven, component-based UI system.

- UI definitions live in `data/ui_elements.json`
- Components live in `src/UI/uiComponents`
- UI runtime is managed by `src/UI/UIManager.py`

The system supports:

- Element composition (`container`, `text`, `image`, `input`, etc.)
- Parent/child hierarchy by path (`screen.panel.button`)
- Component events (`emit` + `eventReader`)
- Data bindings (local variables like `__text`)
- External reads (`__GAME_STATE.some.path`)
- Copy inheritance (`"copy": "other.path"`)
- Array expansion (`"array": { ... }`)
- Dynamic values/animation (`dynamicValue` component)
- Layout keywords (`grid`, `stretchX`, `flexY`, `scrollY`, etc.)

---

## Quick Mental Model

1. Every JSON entry is a UI element, keyed by path.
2. Everything except `data` is treated as a component config.
3. Components are loaded by naming convention:
   - JSON key `text` -> `textComponent.py` -> `TextComponent`
4. Parent-child relationship comes from path segments.
5. Rendering and update order are depth-aware.

---

## Minimal Element Example

```json
"screen.hello": {
  "data": {"__visible": true, "__label": "Hello"},
  "container": {"pos": [20, 20], "size": [180, 30], "keywords": ["crop"], "opts": {}},
  "text": {
    "bind": "__label",
    "editable": false,
    "fontSize": 18,
    "padding": [8, 6],
    "color": "$theme.text.color"
  }
}
```

---

## Path/Hierarchy Example

```json
"screen.panel": { ... },
"screen.panel.title": { ... },
"screen.panel.button": { ... }
```

- `screen.panel` is parent of `screen.panel.title` and `screen.panel.button`
- Child positions are resolved relative to parent container content

---

## Anchors for Position (`container.pos`)

Special tokens (per axis):

- X axis: `__left`, `__middle`, `__right`
- Y axis: `__top`, `__middle`, `__bottom`

These align to parent **content bounds** using the child element box.

Example:

```json
"container": {
  "pos": ["__middle", "__bottom"],
  "size": [200, 28],
  "keywords": ["crop"],
  "opts": {}
}
```

---

## Where to go next
#### UI guides
#### Other interesting places

### UI guides

- Component reference: `docs/Development/UI/components.md`
- Tutorials: `docs/Development/UI/tutorials.md`
- Runtime editor guide: `docs/Development/UI/tutorials.md#runtime-ui-editor-sidebar`

### Other sections

- Core Framework: `docs/Development/Core framework/main.md`
- Machines: `docs/Development/Machines/main.md`
- Docs index: `docs/main.md`
