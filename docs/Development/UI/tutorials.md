# UI Tutorials

This page gives short practical workflows.

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
"screen.list.itemTemplate": {
  "copy": "screen.baseItem",
  "array": {"x": 1, "y": 5, "gap": [0, 30], "path": "item${index2}"},
  "data": {"__label": "Item ${index2}"},
  "input": {
    "mouseup.left": {"emit": "item.pick.${index2}", "scope": ["screen.list"]}
  }
}
```

Template variables:
- `${index}` (x)
- `${index2}` (y)

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
