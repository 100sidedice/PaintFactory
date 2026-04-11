import json
import os
import math
import colorsys

import pygame

from data.settings import BASE_DIR
from src.utils.path_dict import PathDict


class UIEditor:
    COMPONENT_OPTION_SCHEMAS = {
        "container": [
            {"key": "pos", "type": "Array[int,int]", "default": [0, 0]},
            {"key": "size", "type": "Array[int,int]", "default": [120, 40]},
            {"key": "keywords", "type": "Array[String]", "default": []},
            {"key": "opts", "type": "Object", "default": {}},
        ],
        "colorRect": [
            {"key": "color", "type": "String[Hex]|Array[int,int,int]|String[var]", "default": "#FFFFFF"},
        ],
        "outline": [
            {"key": "width", "type": "int", "default": 1},
            {"key": "color", "type": "String[Hex]|Array[int,int,int]|String[var]", "default": "#FFFFFF"},
        ],
        "text": [
            {"key": "bind", "type": "String[path]", "default": "__text"},
            {"key": "editable", "type": "bool", "default": False},
            {"key": "placeholder", "type": "String", "default": ""},
            {"key": "font", "type": "String", "default": ""},
            {"key": "fontSize", "type": "int", "default": 20},
            {"key": "padding", "type": "Array[int,int]", "default": [6, 4]},
            {"key": "color", "type": "String[Hex]|String[var]", "default": "$theme.text.color"},
            {"key": "placeholderColor", "type": "String[Hex]|String[var]", "default": "$theme.text.placeholder_color"},
            {"key": "caretColor", "type": "String[Hex]|String[var]", "default": "$theme.caret.color"},
            {"key": "caretBlinkRate", "type": "float", "default": 0.5},
            {"key": "maxLength", "type": "int", "default": 24},
            {"key": "blurOnEnter", "type": "bool", "default": True},
            {"key": "editingFlag", "type": "String[var]", "default": "__editingText"},
            {"key": "submitEvent", "type": "String[event]", "default": ""},
            {"key": "submitScope", "type": "Array[String[path]]", "default": []},
        ],
        "input": [
            {"key": "mouseup.left", "type": "Object[rule]", "default": {"duration": 0, "emit": "", "scope": []}, "allow_multiple": True},
            {"key": "mousedown.left", "type": "Object[rule]", "default": {"duration": 0, "emit": "", "scope": []}, "allow_multiple": True},
        ],
        "valueReader": [
            {"key": "__rule", "type": "Object[rule]", "default": {"var": "__var", "value": True, "condition": "==", "action": {"setValue": "__var", "value": True}}, "allow_multiple": True},
        ],
        "eventReader": [
            {"key": "event.name", "type": "Object[eventRule]", "default": {"actions": [{"setValue": {"var": "__var", "value": True}}]}, "allow_multiple": True},
            {"key": "event.*", "type": "Object[eventRule]", "default": {"actions": [{"toggleValue": {"var": "__flag"}}]}, "allow_multiple": True},
        ],
        "image": [
            {"key": "path", "type": "String[path]", "default": "Assets/paintbuckets.png"},
            {"key": "frameSize", "type": "Array[int,int]", "default": [16, 16]},
            {"key": "row", "type": "int", "default": 0},
            {"key": "col", "type": "int", "default": 0},
            {"key": "index", "type": "int|String[var]", "default": 0},
            {"key": "columns", "type": "int", "default": 1},
            {"key": "fit", "type": "String[contain|cover|stretch|none]", "default": "contain"},
            {"key": "size", "type": "Array[int,int]", "default": [64, 64]},
            {"key": "anchor", "type": "String[center|topleft|topright|bottomleft|bottomright]", "default": "center"},
            {"key": "offset", "type": "Array[int,int]", "default": [0, 0]},
            {"key": "smooth", "type": "bool", "default": True},
            {"key": "rotation", "type": "float", "default": 0.0},
            {"key": "flipX", "type": "bool", "default": False},
            {"key": "flipY", "type": "bool", "default": False},
            {"key": "alpha", "type": "int[0..255]", "default": 255},
            {"key": "tint", "type": "String[Hex]|Array[int,int,int]", "default": "#FFFFFF"},
            {"key": "tintAlpha", "type": "int[0..255]", "default": 120},
        ],
        "dynamicValue": [
            {"key": "__var", "type": "Object[dynamicRule]", "default": {"type": "loop", "min": 0, "max": 1, "speed": 1.0, "round": False}, "allow_multiple": True},
        ],
    }

    def __init__(self, manager, input_api):
        self.manager = manager
        self.input = input_api
        self.passcode = "ui.editor"
        self.enabled = False
        self.selected_path = None
        self.dragging = False
        self.resizing = False
        self.message = ""
        self.message_time = 0.0
        self.export_path = os.path.join(BASE_DIR, "data", "ui_elements.edited.json")
        self.font = pygame.font.SysFont("consolas", 16)
        self.small_font = pygame.font.SysFont("consolas", 14)

        self.sidebar_width = 470
        self.sidebar_side = "right"
        self.tab = "elements"
        self.tabs = ["elements", "components", "metadata", "state"]

        self.collapsed_element_nodes = set()
        self.collapsed_state_nodes = set()
        self.collapsed_component_nodes = set()
        self.selected_state_path = ""
        self.selected_component_path = ""
        self.component_inline_edit_path = None
        self.component_inline_edit_text = ""
        self.component_inline_caret = 0
        self.component_last_click_path = None
        self.component_last_click_ms = 0
        self.state_inline_edit_path = None
        self.state_inline_edit_text = ""
        self.state_inline_caret = 0
        self.state_inline_rename_path = None
        self.state_inline_rename_text = ""
        self.state_inline_rename_caret = 0
        self.state_last_click_path = None
        self.state_last_click_ms = 0
        self.element_inline_rename_path = None
        self.element_inline_rename_text = ""
        self.element_inline_rename_caret = 0
        self.element_last_click_path = None
        self.element_last_click_ms = 0

        self._color_picker_buttons = []
        self.color_picker_open = False
        self.color_picker_target = None
        self.color_picker_mode = None
        self.color_picker_h = 0.0
        self.color_picker_s = 0.0
        self.color_picker_v = 1.0
        self.color_picker_drag_mode = None
        self._color_wheel_cache = {}

        self.field_rect_cache = {}
        self.field_caret = {}
        self.field_scroll = {}
        self.field_sel_anchor = {}
        self.field_sel_active = {}
        self.field_mouse_select_key = None
        self.field_mouse_select_anchor = 0
        self.field_last_click_key = None
        self.field_last_click_ms = 0
        self.field_last_click_caret = 0
        self.field_history = {}
        self.field_future = {}
        self.key_repeat_state = {}
        self._frame_dt = 0.0

        self.active_field = None
        self.numeric_drag_field = None
        self.numeric_drag_start = 0
        self.numeric_drag_accum = 0.0
        self.fields = {
            "new_parent": "screen",
            "new_name": "newElement",
            "reparent_parent": "screen",
            "reparent_name": "",
            "add_component": "",
            "component_value": "",
            "data_key": "",
            "data_value": "",
            "pos_x": "0",
            "pos_y": "0",
            "size_w": "100",
            "size_h": "40",
            "element_json": "{}",
            "state_value": "0",
        }

        self.element_scroll = 0
        self.component_scroll = 0
        self.component_tree_scroll = 0
        self.state_scroll = 0
        self.selected_component = None
        self.component_add_dropdown_open = False
        self.component_add_dropdown_scroll = 0
        self.component_option_dropdown_open = False
        self.component_option_dropdown_scroll = 0
        self.element_template_dropdown_open = False
        self.element_template_scroll = 0
        self.selected_element_template = "rect"

    def _component_add_button_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.x + 10, 502, 180, 30)

    def _element_template_button_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.x + 150, 444, 200, 30)

    def _element_template_options(self):
        return ["rect", "container", "list", "text_input", "toggle_button", "press_button", "dropdown"]

    def _element_template_dropdown_rect(self):
        btn = self._element_template_button_rect()
        opts = self._element_template_options()
        rows = min(8, max(1, len(opts)))
        return pygame.Rect(btn.x, btn.bottom + 4, btn.w, 4 + rows * 22)

    def _resolve_element_template_name(self):
        opts = self._element_template_options()
        if self.selected_element_template in opts:
            return self.selected_element_template
        return opts[0]

    def _build_element_template_bundle(self, template_name, root_path):
        tpl = str(template_name or "rect").strip().lower()
        root = str(root_path)
        if tpl == "container":
            return {
                root: {
                    "data": {"__visible": True},
                    "container": {"pos": [0, 0], "size": [220, 120], "keywords": ["crop"], "opts": {}},
                }
            }

        if tpl == "list":
            return {
                root: {
                    "data": {"__visible": True, "__selectedLabel": "(none)"},
                    "container": {
                        "pos": [0, 0],
                        "size": [220, 168],
                        "keywords": ["crop"],
                        "opts": {},
                    },
                    "colorRect": {"color": "#141414"},
                    "outline": {"width": 2, "color": "#3A3A3A"},
                },
                f"{root}.header": {
                    "data": {"__visible": True, "__title": "List"},
                    "container": {"pos": [0, 0], "size": [220, 32], "keywords": [], "opts": {}},
                    "colorRect": {"color": "#1D1D1D"},
                    "outline": {"width": 1, "color": "#4A4A4A"},
                    "text": {
                        "bind": "__title",
                        "editable": False,
                        "fontSize": 16,
                        "padding": [8, 7],
                        "color": "$theme.text.color",
                    },
                    "eventReader": {
                        f"{root}.item.select.*": {
                            "actions": [
                                {"setValue": {"var": "__title", "value": "$source.__label"}},
                                {"setValue": {"var": "__selectedLabel", "value": "$source.__label"}},
                            ]
                        }
                    },
                },
                f"{root}.items": {
                    "data": {"__visible": True},
                    "container": {
                        "pos": [0, 32],
                        "size": [220, 136],
                        "keywords": ["crop", "scrollY"],
                        "opts": {"scrollSpeed": 22, "scrollDamping": 18, "limits": "element"},
                    },
                    "colorRect": {"color": "#1A1A1A"},
                    "outline": {"width": 1, "color": "#3A3A3A"},
                },
                f"{root}.itemBase": {
                    "data": {"__visible": False, "__label": "Item"},
                    "container": {"pos": [0, 0], "size": [220, 30], "keywords": ["input"], "opts": {}},
                    "colorRect": {"color": "#242424"},
                    "outline": {"width": 1, "color": "#4A4A4A"},
                    "text": {"bind": "__label", "editable": False, "fontSize": 16, "padding": [8, 7], "color": "$theme.text.color"},
                    "eventReader": {
                        f"{root}.item.select.*": {"actions": [{"setValue": {"var": "__visible", "value": False}}]}
                    },
                },
                f"{root}.items.item0": {
                    "copy": f"{root}.itemBase",
                    "array": {"x": 1, "y": 6, "gap": [0, 30]},
                    "data": {"__label": "Item ${index2}"},
                    "input": {
                        "mouseup.left": {
                            "duration": 0,
                            "emit": f"{root}.item.select.${{index2}}",
                            "scope": [f"{root}.header", f"{root}.items"],
                        }
                    },
                },
            }

        if tpl == "toggle_button":
            event_name = f"{root}.toggle"
            return {
                root: {
                    "data": {
                        "__toggled": False,
                        "__color": "#FF0000",
                        "__visible": True,
                    },
                    "container": {"pos": [0, 0], "size": [50, 50], "keywords": ["crop", "input"], "opts": {}},
                    "colorRect": {"pos": [0, 0], "size": [50, 50], "color": "__color"},
                    "outline": {"width": 3},
                    "input": {
                        "mouseup.left": {"duration": 0, "emit": event_name, "scope": [root]}
                    },
                    "valueReader": {
                        "__toggled": {"value": False, "condition": "==", "action": {"setValue": "__color", "value": "#330000"}},
                        "__toggled-1": {"value": True, "condition": "==", "action": {"setValue": "__color", "value": "#FF0000"}},
                    },
                    "eventReader": {
                        event_name: {"actions": [{"toggleValue": {"var": "__toggled"}}]}
                    },
                }
            }

        if tpl == "text_input":
            return {
                root: {
                    "data": {
                        "__visible": True,
                        "__text": "",
                        "__editingText": False,
                        "__outlineColor": "#1E1E1E",
                    },
                    "container": {"pos": [0, 0], "size": [280, 36], "keywords": ["crop", "input"], "opts": {}},
                    "colorRect": {"color": "#1E1E1E"},
                    "outline": {"width": 2, "color": "__outlineColor"},
                    "text": {
                        "bind": "__text",
                        "editingFlag": "__editingText",
                        "editable": True,
                        "placeholder": "Type name...",
                        "fontSize": 20,
                        "padding": [8, 8],
                        "color": "$theme.text.color",
                        "placeholderColor": "$theme.text.placeholder_color",
                        "caretColor": "$theme.caret.color",
                        "caretBlinkRate": "$theme.caret.blink_rate",
                        "maxLength": 24,
                        "blurOnEnter": True,
                    },
                    "valueReader": {
                        "__editingText": {"value": True, "condition": "==", "action": {"setValue": "__outlineColor", "value": "$theme.focus.outline_color"}},
                        "__editingText-1": {"value": False, "condition": "==", "action": {"setValue": "__outlineColor", "value": "#1E1E1E"}},
                    },
                }
            }

        if tpl == "press_button":
            event_name = f"{root}.pressed"
            return {
                root: {
                    "data": {"__visible": True, "__label": "Button"},
                    "container": {"pos": [0, 0], "size": [140, 36], "keywords": ["crop", "input"], "opts": {}},
                    "colorRect": {"color": "#2A2A2A"},
                    "outline": {"width": 2, "color": "#4A4A4A"},
                    "text": {"bind": "__label", "editable": False, "fontSize": 18, "padding": [8, 8], "color": "$theme.text.color"},
                    "input": {
                        "mouseup.left": {"duration": 0, "emit": event_name, "scope": [root]}
                    },
                }
            }

        if tpl == "dropdown":
            return {
                root: {
                    "data": {"__visible": True},
                    "container": {"pos": [0, 0], "size": [220, 132], "keywords": ["crop"], "opts": {}},
                    "colorRect": {"color": "#141414"},
                    "outline": {"width": 2, "color": "#3A3A3A"},
                },
                f"{root}.header": {
                    "data": {"__visible": True, "__selectedText": "Choose option"},
                    "container": {"pos": [0, 0], "size": [220, 34], "keywords": ["input"], "opts": {}},
                    "colorRect": {"color": "#1D1D1D"},
                    "outline": {"width": 2, "color": "#4A4A4A"},
                    "text": {"bind": "__selectedText", "editable": False, "fontSize": 18, "padding": [8, 8], "color": "$theme.text.color"},
                    "input": {
                        "mouseup.left": {"duration": 0, "emit": "dropdown.toggle", "scope": [f"{root}.options"]}
                    },
                    "eventReader": {
                        "dropdown.option.*": {"actions": [{"setValue": {"var": "__selectedText", "value": "$source.__label"}}]}
                    },
                },
                f"{root}.options": {
                    "data": {"__visible": True},
                    "container": {
                        "pos": [0, 34],
                        "size": [220, 98],
                        "keywords": ["crop", "scrollY"],
                        "opts": {"scrollSpeed": 22, "scrollDamping": 18, "limits": "element"},
                    },
                    "colorRect": {"color": "#1A1A1A"},
                    "outline": {"width": 1, "color": "#3A3A3A"},
                },
                f"{root}.optionBase": {
                    "data": {"__visible": False, "__label": "Option"},
                    "container": {"pos": [0, 0], "size": [220, 32], "keywords": ["input"], "opts": {}},
                    "colorRect": {"color": "#242424"},
                    "outline": {"width": 1, "color": "#4A4A4A"},
                    "text": {"bind": "__label", "editable": False, "fontSize": 16, "padding": [8, 7], "color": "$theme.text.color"},
                    "eventReader": {
                        "dropdown.toggle": {"actions": [{"toggleValue": {"var": "__visible"}}]},
                        "dropdown.option.*": {"actions": [{"setValue": {"var": "__visible", "value": False}}]},
                    },
                },
                f"{root}.options.item0": {
                    "copy": f"{root}.optionBase",
                    "array": {"x": 1, "y": 10, "gap": [0, 32]},
                    "data": {"__label": "Option ${index2}"},
                    "input": {
                        "mouseup.left": {
                            "duration": 0,
                            "emit": "dropdown.option.${index2}",
                            "scope": [f"{root}.header", f"{root}.options"],
                        }
                    },
                },
            }

        return {
            root: {
                "data": {"__visible": True},
                "container": {"pos": [0, 0], "size": [120, 40], "keywords": ["crop"], "opts": {}},
                "colorRect": {"color": "#202020"},
                "outline": {"width": 1, "color": "#606060"},
            }
        }

    def _component_add_options(self):
        return self.manager.available_component_names()

    def _component_add_dropdown_rect(self):
        btn = self._component_add_button_rect()
        options = self._component_add_options()
        rows = min(10, max(1, len(options)))
        return pygame.Rect(btn.x, btn.bottom + 4, btn.w, 4 + rows * 22)

    def _component_option_button_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.x + 200, 502, 160, 30)

    def _component_base_name(self, name):
        return str(name or "").split("-", 1)[0]

    def _component_option_entries(self):
        base = self._component_base_name(self.selected_component)
        return self.COMPONENT_OPTION_SCHEMAS.get(base, [])

    def _component_option_dropdown_rect(self):
        btn = self._component_option_button_rect()
        options = self._component_option_entries()
        rows = min(10, max(1, len(options)))
        return pygame.Rect(btn.x, btn.bottom + 4, btn.w + 120, 4 + rows * 22)

    def _unique_dict_key(self, node, key_base):
        key = str(key_base)
        if key not in node:
            return key
        i = 1
        while True:
            candidate = f"{key}-{i}"
            if candidate not in node:
                return candidate
            i += 1

    def _next_component_instance_name(self, selected, base_name):
        base = str(base_name or "").strip()
        if not base:
            return ""
        if selected.getComponent(base) is None:
            return base
        n = 1
        while True:
            candidate = f"{base}-{n}"
            if selected.getComponent(candidate) is None:
                return candidate
            n += 1

    def toggle(self):
        self.enabled = not self.enabled
        self.dragging = False
        self.resizing = False
        self.active_field = None
        if self.enabled:
            self.input.lock(self.passcode, {"type": "unlock"})
            self._set_message("UI editor enabled")
        else:
            self.input.unlock(self.passcode)
            self._set_message("UI editor disabled")

    def update(self, delta):
        if not self.enabled:
            return

        self._frame_dt = max(0.0, float(delta))

        self.message_time = max(0.0, self.message_time - float(delta))

        if self._ctrl_down() and self.input.get_key_down(pygame.K_p, self.passcode):
            path = self.manager.export_ui_json(self.export_path)
            self._set_message(f"Exported UI -> {path}")

        if self.input.get_mouse_button_down(1, self.passcode) and self.active_field is not None:
            active_rect = self.field_rect_cache.get(self.active_field)
            if active_rect is not None:
                mx, my = self.input.get_mouse_position(self.passcode)
                if self._is_in_sidebar(mx, my) and not active_rect.collidepoint((mx, my)):
                    self.active_field = None
                    self.numeric_drag_field = None
                    self.field_mouse_select_key = None

        if self._update_color_picker_input():
            return

        self._update_element_inline_rename()
        self._update_component_inline_edit()
        self._update_state_inline_edit()
        self._update_state_inline_rename()
        self._update_sidebar_input()
        self._update_field_mouse_selection()
        self._update_active_field_typing()
        self._update_numeric_field_drag()
        self._update_selection_and_transform()

    def draw(self, surface):
        if not self.enabled:
            return

        selected = self._selected_element()
        if selected is not None:
            rect = selected.get_rect()
            if rect is not None:
                pygame.draw.rect(surface, (255, 225, 70), rect, 2)
                handle = pygame.Rect(rect.right - 8, rect.bottom - 8, 8, 8)
                pygame.draw.rect(surface, (255, 140, 80), handle)

        self._draw_sidebar(surface)

    def _ctrl_down(self):
        return self.input.get_key(pygame.K_LCTRL, self.passcode) or self.input.get_key(pygame.K_RCTRL, self.passcode)

    def _shift_down(self):
        return self.input.get_key(pygame.K_LSHIFT, self.passcode) or self.input.get_key(pygame.K_RSHIFT, self.passcode)

    def _key_pressed_or_repeat(self, key, initial_delay=0.5, repeat_interval=0.05):
        if self.input.get_key_down(key, self.passcode):
            self.key_repeat_state[key] = {"elapsed": 0.0, "next": float(initial_delay)}
            return True

        if not self.input.get_key(key, self.passcode):
            self.key_repeat_state.pop(key, None)
            return False

        state = self.key_repeat_state.get(key)
        if state is None:
            state = {"elapsed": 0.0, "next": float(initial_delay)}
            self.key_repeat_state[key] = state

        state["elapsed"] += self._frame_dt
        if state["elapsed"] >= state["next"]:
            state["next"] += float(repeat_interval)
            return True
        return False

    def _history_snapshot(self, key, text, caret):
        return {
            "text": str(text),
            "caret": int(caret),
            "anchor": int(self.field_sel_anchor.get(key, caret)),
            "active": int(self.field_sel_active.get(key, caret)),
        }

    def _history_push(self, key, text, caret):
        stack = self.field_history.setdefault(key, [])
        snap = self._history_snapshot(key, text, caret)
        if stack and stack[-1] == snap:
            return
        stack.append(snap)
        if len(stack) > 300:
            del stack[0]
        self.field_future[key] = []

    def _history_restore(self, key, snap):
        self.fields[key] = snap.get("text", "")
        caret = int(snap.get("caret", len(self.fields[key])))
        self.field_caret[key] = max(0, min(len(self.fields[key]), caret))
        self.field_sel_anchor[key] = int(snap.get("anchor", self.field_caret[key]))
        self.field_sel_active[key] = int(snap.get("active", self.field_caret[key]))

    def _history_undo(self, key):
        stack = self.field_history.get(key, [])
        if not stack:
            return False
        current = self._history_snapshot(key, self.fields.get(key, ""), self.field_caret.get(key, 0))
        self.field_future.setdefault(key, []).append(current)
        snap = stack.pop()
        self._history_restore(key, snap)
        return True

    def _history_redo(self, key):
        future = self.field_future.get(key, [])
        if not future:
            return False
        current = self._history_snapshot(key, self.fields.get(key, ""), self.field_caret.get(key, 0))
        self.field_history.setdefault(key, []).append(current)
        snap = future.pop()
        self._history_restore(key, snap)
        return True

    def _set_message(self, msg, ttl=3.0):
        self.message = str(msg)
        self.message_time = float(ttl)

    def _screen_size(self):
        return self.manager.surface.get_size()

    def _sidebar_rect(self):
        w, h = self._screen_size()
        if self.sidebar_side == "left":
            return pygame.Rect(0, 0, self.sidebar_width, h)
        return pygame.Rect(max(0, w - self.sidebar_width), 0, self.sidebar_width, h)

    def _is_in_sidebar(self, x, y):
        return self._sidebar_rect().collidepoint((x, y))

    def _selected_element(self):
        if not self.selected_path:
            return None
        return self.manager.getElement(self.selected_path)

    def _is_locked_element(self, element):
        if element is None:
            return False
        if element.path == "screen":
            return True
        return self.manager.is_array_locked(element.path)

    def _is_state_name_locked(self, path):
        if not path:
            return True
        if "." not in path:
            return True
        root = path.split(".", 1)[0]
        if root == "settings":
            return True
        return False

    def _is_state_value_locked(self, path):
        if not path:
            return True
        root = path.split(".", 1)[0]
        return root == "settings"

    def _pick_element(self, mouse_pos):
        for element in reversed(self.manager.flattenElements()):
            if not element.is_visible():
                continue
            rect = element.get_rect()
            if rect is None:
                continue
            clip_rect = element.get_clip_rect()
            hit_rect = rect if clip_rect is None else rect.clip(clip_rect)
            if hit_rect.w <= 0 or hit_rect.h <= 0:
                continue
            if self._is_in_sidebar(rect.centerx, rect.centery):
                continue
            if hit_rect.collidepoint(mouse_pos):
                return element
        return None

    def _ensure_container(self, element):
        if element is None:
            return None
        return element.getComponent("container")

    def _set_local_position(self, element, x, y):
        if self._is_locked_element(element):
            return
        container = self._ensure_container(element)
        if container is None:
            return

        local_x = float(x)
        local_y = float(y)

        parent = element.get_parent()
        if parent is not None:
            parent_container = parent.getComponent("container")
            if parent_container is not None:
                ox, oy = parent_container.get_child_origin(element)
                local_x -= ox
                local_y -= oy
            else:
                parent_rect = parent.get_rect()
                if parent_rect is not None:
                    local_x -= parent_rect.x
                    local_y -= parent_rect.y

        container.config["pos"] = [int(local_x), int(local_y)]

    def _set_size(self, element, w, h):
        if self._is_locked_element(element):
            return
        container = self._ensure_container(element)
        if container is None:
            return
        container.config["size"] = [max(1, int(w)), max(1, int(h))]

    def _sync_transform_fields(self):
        selected = self._selected_element()
        if selected is None:
            return
        container = selected.getComponent("container")
        if container is None:
            return
        pos = container.config.get("pos", [0, 0])
        size = container.config.get("size", [0, 0])
        self.fields["pos_x"] = str(int(pos[0]) if isinstance(pos, list) and len(pos) > 0 and isinstance(pos[0], (int, float)) else 0)
        self.fields["pos_y"] = str(int(pos[1]) if isinstance(pos, list) and len(pos) > 1 and isinstance(pos[1], (int, float)) else 0)
        self.fields["size_w"] = str(int(size[0]) if isinstance(size, list) and len(size) > 0 and isinstance(size[0], (int, float)) else 0)
        self.fields["size_h"] = str(int(size[1]) if isinstance(size, list) and len(size) > 1 and isinstance(size[1], (int, float)) else 0)

    def _update_selection_and_transform(self):
        mx, my = self.input.get_mouse_position(self.passcode)

        if self._is_in_sidebar(mx, my):
            if self.input.get_mouse_button_up(1, self.passcode):
                self.dragging = False
                self.resizing = False
            return

        if self.input.get_mouse_button_down(1, self.passcode):
            picked = self._pick_element((mx, my))
            self.selected_path = picked.path if picked is not None else None
            self._sync_transform_fields()
            self._load_selected_element_json()
            self.selected_component = None
            if picked is not None:
                if self._is_locked_element(picked):
                    self.dragging = False
                    self.resizing = False
                    return
                if self._shift_down():
                    self.resizing = True
                    self.dragging = False
                else:
                    self.dragging = True
                    self.resizing = False

        if self.input.get_mouse_button_up(1, self.passcode):
            self.dragging = False
            self.resizing = False

        selected = self._selected_element()
        if selected is None:
            return

        if not self.input.get_mouse_button(1, self.passcode):
            return

        dx, dy = self.input.get_mouse_motion(self.passcode)
        if dx == 0 and dy == 0:
            return

        rect = selected.get_rect()
        if rect is None:
            return

        if self.dragging:
            self._set_local_position(selected, rect.x + dx, rect.y + dy)
            self._sync_transform_fields()
        elif self.resizing:
            self._set_size(selected, rect.w + dx, rect.h + dy)
            self._sync_transform_fields()

    def _update_keyboard_transform(self):
        selected = self._selected_element()
        if selected is None:
            return

        rect = selected.get_rect()
        if rect is None:
            return

        step = 10 if self._shift_down() else 1
        if self._ctrl_down():
            if self.input.get_key_down(pygame.K_LEFT, self.passcode):
                self._set_size(selected, rect.w - step, rect.h)
            if self.input.get_key_down(pygame.K_RIGHT, self.passcode):
                self._set_size(selected, rect.w + step, rect.h)
            if self.input.get_key_down(pygame.K_UP, self.passcode):
                self._set_size(selected, rect.w, rect.h - step)
            if self.input.get_key_down(pygame.K_DOWN, self.passcode):
                self._set_size(selected, rect.w, rect.h + step)
            return

        if self.input.get_key_down(pygame.K_LEFT, self.passcode):
            self._set_local_position(selected, rect.x - step, rect.y)
        if self.input.get_key_down(pygame.K_RIGHT, self.passcode):
            self._set_local_position(selected, rect.x + step, rect.y)
        if self.input.get_key_down(pygame.K_UP, self.passcode):
            self._set_local_position(selected, rect.x, rect.y - step)
        if self.input.get_key_down(pygame.K_DOWN, self.passcode):
            self._set_local_position(selected, rect.x, rect.y + step)
        self._sync_transform_fields()

    def _parse_value(self, value_text):
        text = value_text.strip()
        if text == "":
            return ""
        try:
            return json.loads(text)
        except Exception:
            low = text.lower()
            if low == "true":
                return True
            if low == "false":
                return False
            if low == "null":
                return None
            return text

    def _to_int_field(self, key, default=0):
        try:
            return int(float(self.fields.get(key, str(default)).strip()))
        except Exception:
            return int(default)

    def _begin_numeric_drag(self, key):
        self.numeric_drag_field = key
        self.numeric_drag_start = self._to_int_field(key, 0)
        self.numeric_drag_accum = 0.0

    def _update_numeric_field_drag(self):
        if self.numeric_drag_field is None:
            return

        if self.input.get_mouse_button_up(1, self.passcode):
            self.numeric_drag_field = None
            self.numeric_drag_accum = 0.0
            return

        if not self.input.get_mouse_button(1, self.passcode):
            return

        dx, dy = self.input.get_mouse_motion(self.passcode)
        if dx == 0 and dy == 0:
            return

        # Horizontal right / vertical up increase values.
        self.numeric_drag_accum += float(dx) - float(dy)
        step = int(self.numeric_drag_accum)
        if step == 0:
            return

        self.numeric_drag_accum -= float(step)
        current = self._to_int_field(self.numeric_drag_field, self.numeric_drag_start)
        new_val = current + step
        self.fields[self.numeric_drag_field] = str(new_val)
        self._apply_transform_from_fields(silent=True)

    def _apply_transform_from_fields(self, silent=False):
        selected = self._selected_element()
        if selected is None:
            if not silent:
                self._set_message("No selected element")
            return False
        if self._is_locked_element(selected):
            if not silent:
                self._set_message("Selected element is locked")
            return False
        container = selected.getComponent("container")
        if container is None:
            if not silent:
                self._set_message("Element has no container")
            return False

        container.config["pos"] = [self._to_int_field("pos_x", 0), self._to_int_field("pos_y", 0)]
        container.config["size"] = [max(1, self._to_int_field("size_w", 100)), max(1, self._to_int_field("size_h", 40))]
        return True

    def _update_active_field_typing(self):
        if self.component_inline_edit_path is not None or self.state_inline_edit_path is not None or self.element_inline_rename_path is not None:
            return
        if self.active_field is None:
            return

        key = self.active_field
        text = self.fields.get(key, "")
        caret = self._clamp_caret(key)
        self._set_selection(key, self.field_sel_anchor.get(key, caret), self.field_sel_active.get(key, caret))
        sel = self._selection_range(key)
        shift = self._shift_down()
        ctrl = self._ctrl_down()
        indent_size = self._detect_indent_size(text)
        changed = False
        snapshotted = False

        left_pressed = self._key_pressed_or_repeat(pygame.K_LEFT)
        right_pressed = self._key_pressed_or_repeat(pygame.K_RIGHT)
        up_pressed = self._key_pressed_or_repeat(pygame.K_UP)
        down_pressed = self._key_pressed_or_repeat(pygame.K_DOWN)
        home_pressed = self._key_pressed_or_repeat(pygame.K_HOME)
        end_pressed = self._key_pressed_or_repeat(pygame.K_END)
        backspace_pressed = self._key_pressed_or_repeat(pygame.K_BACKSPACE)
        delete_pressed = self._key_pressed_or_repeat(pygame.K_DELETE)
        tab_pressed = self._key_pressed_or_repeat(pygame.K_TAB)
        enter_pressed = self.input.get_key_down(pygame.K_RETURN, self.passcode) or self.input.get_key_down(pygame.K_KP_ENTER, self.passcode)
        backtab_pressed = self.input.get_key_down(pygame.K_TAB, self.passcode) and shift

        def ensure_snapshot():
            nonlocal snapshotted
            if not snapshotted:
                self._history_push(key, text, caret)
                snapshotted = True

        def replace_selection(insert_text):
            nonlocal text, caret, sel, changed
            ensure_snapshot()
            if sel is not None:
                s, e = sel
                text = text[:s] + insert_text + text[e:]
                caret = s + len(insert_text)
            else:
                text = text[:caret] + insert_text + text[caret:]
                caret += len(insert_text)
            self._clear_selection(key, caret)
            sel = None
            changed = True

        def move_caret(new_caret):
            nonlocal caret, sel
            new_caret = max(0, min(len(text), int(new_caret)))
            if shift:
                anchor = caret if sel is None else int(self.field_sel_anchor.get(key, caret))
                self._set_selection(key, anchor, new_caret)
            else:
                self._clear_selection(key, new_caret)
            caret = new_caret
            sel = self._selection_range(key)

        # Undo / redo
        if ctrl and not shift and self.input.get_key_down(pygame.K_z, self.passcode):
            if self._history_undo(key):
                self._clamp_caret(key)
            return
        if ctrl and (self.input.get_key_down(pygame.K_y, self.passcode) or (shift and self.input.get_key_down(pygame.K_z, self.passcode))):
            if self._history_redo(key):
                self._clamp_caret(key)
            return

        # Ctrl+Shift+Up/Down duplicate current/selected line block.
        if ctrl and shift and (up_pressed or down_pressed):
            up = up_pressed
            lines = self._split_lines(text)
            if lines:
                ensure_snapshot()
                sline, eline = self._line_range_from_selection(text, key)
                block = lines[sline:eline + 1]
                if up:
                    lines[sline:sline] = block
                    ns, ne = sline, sline + len(block) - 1
                else:
                    insert_at = eline + 1
                    lines[insert_at:insert_at] = block
                    ns, ne = insert_at, insert_at + len(block) - 1
                text = "\n".join(lines)
                self._select_line_span(key, text, ns, ne)
                caret = int(self.field_sel_active.get(key, 0))
                self.fields[key] = text
                self.field_caret[key] = caret
                changed = True
            return

        if self.input.get_key_down(pygame.K_ESCAPE, self.passcode):
            self.active_field = None
            return

        # Shift+Up/Down line selection expansion with moving caret.
        if shift and not ctrl and (up_pressed or down_pressed):
            lines = self._split_lines(text)
            if lines:
                sline, eline = self._line_range_from_selection(text, key)
                if up_pressed:
                    sline = max(0, sline - 1)
                    self._select_line_span(key, text, sline, eline)
                    caret = self._line_col_to_index(text, sline, 0)
                else:
                    eline = min(len(lines) - 1, eline + 1)
                    self._select_line_span(key, text, sline, eline)
                    caret = int(self.field_sel_active.get(key, 0))
                self.field_caret[key] = caret
            return

        if left_pressed:
            new_caret = self._prev_token_boundary(text, caret) if ctrl else max(0, caret - 1)
            move_caret(new_caret)
        if right_pressed:
            new_caret = self._next_token_boundary(text, caret) if ctrl else min(len(text), caret + 1)
            move_caret(new_caret)
        if home_pressed:
            line, _ = self._index_to_line_col(text, caret)
            new_caret = self._line_col_to_index(text, line, 0)
            move_caret(new_caret)
        if end_pressed:
            lines = self._split_lines(text)
            line, _ = self._index_to_line_col(text, caret)
            line = max(0, min(len(lines) - 1, line))
            new_caret = self._line_col_to_index(text, line, len(lines[line]))
            move_caret(new_caret)
        if up_pressed:
            line, col = self._index_to_line_col(text, caret)
            new_caret = self._line_col_to_index(text, line - 1, col)
            move_caret(new_caret)
        if down_pressed:
            line, col = self._index_to_line_col(text, caret)
            new_caret = self._line_col_to_index(text, line + 1, col)
            move_caret(new_caret)

        if backtab_pressed and self._is_json_editor_field(key):
            suggestions = self._json_comma_suggestions(text)
            if suggestions:
                ensure_snapshot()
                caret_line_now, _ = self._index_to_line_col(text, caret)
                chosen = self._nearest_json_suggestion(suggestions, caret_line_now)
                new_text = self._apply_json_suggestion(text, chosen)
                if new_text != text:
                    text = new_text
                    caret = min(caret, len(text))
                    self._clear_selection(key, caret)
                    sel = None
                    changed = True
                    self._set_message("Applied JSON suggestion")
                    self.fields[key] = text
                    self.field_caret[key] = caret
            return

        if tab_pressed:
            if shift and self._is_json_editor_field(key):
                return
            if self._is_json_editor_field(key):
                suggestions = self._json_comma_suggestions(text)
                if suggestions:
                    # Suggestions are accepted with Shift+Tab only.
                    pass
            if sel is not None:
                ensure_snapshot()
                sline, eline = self._line_range_from_selection(text, key)
                lines = self._split_lines(text)
                for li in range(sline, eline + 1):
                    lines[li] = (" " * indent_size) + lines[li]
                text = "\n".join(lines)
                self._select_line_span(key, text, sline, eline)
                caret = int(self.field_sel_active.get(key, 0))
                sel = self._selection_range(key)
                changed = True
            else:
                replace_selection(" " * indent_size)

        if backspace_pressed:
            if sel is not None:
                ensure_snapshot()
                s, e = sel
                text = text[:s] + text[e:]
                caret = s
                self._clear_selection(key, caret)
                sel = None
                changed = True
            elif caret > 0:
                ensure_snapshot()
                text = text[: caret - 1] + text[caret:]
                caret -= 1
                self._clear_selection(key, caret)
                changed = True
        if delete_pressed:
            if sel is not None:
                ensure_snapshot()
                s, e = sel
                text = text[:s] + text[e:]
                caret = s
                self._clear_selection(key, caret)
                sel = None
                changed = True
            elif caret < len(text):
                ensure_snapshot()
                text = text[:caret] + text[caret + 1 :]
                self._clear_selection(key, caret)
                changed = True

        entered = self.input.consume_text_input(self.passcode)
        if entered:
            chunk = "".join(entered)
            replace_selection(chunk)

        if enter_pressed:
            if key in {"pos_x", "pos_y", "size_w", "size_h"}:
                self.fields[key] = text
                self.field_caret[key] = caret
                self._clear_selection(key, caret)
                self._apply_transform_from_fields(silent=True)
                self.active_field = None
                return
            replace_selection("\n")

        if changed or self.fields.get(key, "") != text:
            self.fields[key] = text
            if key == "element_json":
                self._try_instant_apply_element_json()
        self.field_caret[key] = caret

    def _start_component_inline_edit(self, path):
        self.component_inline_edit_path = path
        current = self._component_path_value()
        self.component_inline_edit_text = json.dumps(current, ensure_ascii=False)
        self.component_inline_caret = len(self.component_inline_edit_text)
        self.active_field = None

    def _stop_component_inline_edit(self, apply_changes):
        if self.component_inline_edit_path is None:
            return

        if apply_changes:
            selected = self._selected_element()
            if selected is None or self._is_locked_element(selected):
                self._set_message("Selected element is locked")
            else:
                comp = selected.getComponent(self.selected_component)
                if comp is None or not isinstance(comp.config, dict):
                    self._set_message("Missing component")
                else:
                    try:
                        parsed = self._parse_value(self.component_inline_edit_text)
                        PathDict.set(comp.config, self.component_inline_edit_path, parsed)
                        selected.elmData[self.selected_component] = json.loads(json.dumps(comp.config))
                        self.fields["component_value"] = json.dumps(parsed, indent=2)
                        self._set_message("Component value applied")
                    except Exception:
                        self._set_message("Invalid value")

        self.component_inline_edit_path = None
        self.component_inline_edit_text = ""
        self.component_inline_caret = 0

    def _update_component_inline_edit(self):
        if self.component_inline_edit_path is None:
            return

        if self.input.get_key_down(pygame.K_ESCAPE, self.passcode):
            self._stop_component_inline_edit(False)
            return

        if self.input.get_key_down(pygame.K_RETURN, self.passcode) or self.input.get_key_down(pygame.K_KP_ENTER, self.passcode):
            self._stop_component_inline_edit(True)
            return

        if self.input.get_key_down(pygame.K_LEFT, self.passcode):
            self.component_inline_caret = max(0, self.component_inline_caret - 1)
        if self.input.get_key_down(pygame.K_RIGHT, self.passcode):
            self.component_inline_caret = min(len(self.component_inline_edit_text), self.component_inline_caret + 1)
        if self.input.get_key_down(pygame.K_HOME, self.passcode):
            self.component_inline_caret = 0
        if self.input.get_key_down(pygame.K_END, self.passcode):
            self.component_inline_caret = len(self.component_inline_edit_text)

        entered = self.input.consume_text_input(self.passcode)
        if entered:
            text = "".join(entered)
            left = self.component_inline_edit_text[:self.component_inline_caret]
            right = self.component_inline_edit_text[self.component_inline_caret:]
            self.component_inline_edit_text = left + text + right
            self.component_inline_caret += len(text)

        if self.input.get_key_down(pygame.K_BACKSPACE, self.passcode) and self.component_inline_caret > 0:
            left = self.component_inline_edit_text[: self.component_inline_caret - 1]
            right = self.component_inline_edit_text[self.component_inline_caret :]
            self.component_inline_edit_text = left + right
            self.component_inline_caret -= 1

        if self.input.get_key_down(pygame.K_DELETE, self.passcode) and self.component_inline_caret < len(self.component_inline_edit_text):
            left = self.component_inline_edit_text[: self.component_inline_caret]
            right = self.component_inline_edit_text[self.component_inline_caret + 1 :]
            self.component_inline_edit_text = left + right

    def _start_element_inline_rename(self, path):
        if not path:
            return
        if path == "screen":
            self._set_message("screen is locked")
            return
        element = self.manager.getElement(path)
        if self._is_locked_element(element):
            self._set_message("Selected element is locked")
            return

        self.element_inline_rename_path = path
        self.element_inline_rename_text = path.rsplit(".", 1)[-1]
        self.element_inline_rename_caret = len(self.element_inline_rename_text)
        self.active_field = None

    def _stop_element_inline_rename(self, apply_changes):
        if self.element_inline_rename_path is None:
            return

        old_path = self.element_inline_rename_path
        if apply_changes:
            new_leaf = self.element_inline_rename_text.strip()
            if not new_leaf:
                self._set_message("Name cannot be empty")
            else:
                parent = old_path.rsplit(".", 1)[0] if "." in old_path else ""
                new_path = f"{parent}.{new_leaf}" if parent else new_leaf
                ok, msg = self.manager.rename_element_path(old_path, new_path)
                if ok:
                    self.selected_path = new_path
                    self._set_message("Renamed")
                else:
                    self._set_message(msg)

        self.element_inline_rename_path = None
        self.element_inline_rename_text = ""
        self.element_inline_rename_caret = 0

    def _update_element_inline_rename(self):
        if self.element_inline_rename_path is None:
            return

        if self.input.get_key_down(pygame.K_ESCAPE, self.passcode):
            self._stop_element_inline_rename(False)
            return

        if self.input.get_key_down(pygame.K_RETURN, self.passcode) or self.input.get_key_down(pygame.K_KP_ENTER, self.passcode):
            self._stop_element_inline_rename(True)
            return

        if self.input.get_key_down(pygame.K_LEFT, self.passcode):
            self.element_inline_rename_caret = max(0, self.element_inline_rename_caret - 1)
        if self.input.get_key_down(pygame.K_RIGHT, self.passcode):
            self.element_inline_rename_caret = min(len(self.element_inline_rename_text), self.element_inline_rename_caret + 1)
        if self.input.get_key_down(pygame.K_HOME, self.passcode):
            self.element_inline_rename_caret = 0
        if self.input.get_key_down(pygame.K_END, self.passcode):
            self.element_inline_rename_caret = len(self.element_inline_rename_text)

        entered = self.input.consume_text_input(self.passcode)
        if entered:
            text = "".join(entered)
            left = self.element_inline_rename_text[: self.element_inline_rename_caret]
            right = self.element_inline_rename_text[self.element_inline_rename_caret :]
            self.element_inline_rename_text = left + text + right
            self.element_inline_rename_caret += len(text)

        if self.input.get_key_down(pygame.K_BACKSPACE, self.passcode) and self.element_inline_rename_caret > 0:
            left = self.element_inline_rename_text[: self.element_inline_rename_caret - 1]
            right = self.element_inline_rename_text[self.element_inline_rename_caret :]
            self.element_inline_rename_text = left + right
            self.element_inline_rename_caret -= 1

        if self.input.get_key_down(pygame.K_DELETE, self.passcode) and self.element_inline_rename_caret < len(self.element_inline_rename_text):
            left = self.element_inline_rename_text[: self.element_inline_rename_caret]
            right = self.element_inline_rename_text[self.element_inline_rename_caret + 1 :]
            self.element_inline_rename_text = left + right

    def _start_state_inline_edit(self, path):
        if self._is_state_value_locked(path):
            self._set_message("This value is locked")
            return
        self.state_inline_edit_path = path
        game_state = getattr(self.manager, "GAME_STATE", None)
        current = game_state.get(path) if game_state is not None else None
        self.state_inline_edit_text = json.dumps(current, ensure_ascii=False)
        self.state_inline_caret = len(self.state_inline_edit_text)
        self.active_field = None

    def _start_state_inline_rename(self, path):
        if not path:
            return
        if self._is_state_name_locked(path):
            self._set_message("This key is locked")
            return
        self.state_inline_edit_path = None
        self.state_inline_edit_text = ""
        self.state_inline_caret = 0
        self.state_inline_rename_path = path
        self.state_inline_rename_text = path.rsplit(".", 1)[-1]
        self.state_inline_rename_caret = len(self.state_inline_rename_text)
        self.active_field = None

    def _stop_state_inline_rename(self, apply_changes):
        if getattr(self, "state_inline_rename_path", None) is None:
            return

        old_path = self.state_inline_rename_path
        if apply_changes:
            new_leaf = self.state_inline_rename_text.strip()
            if not new_leaf:
                self._set_message("Name cannot be empty")
            else:
                parent = old_path.rsplit(".", 1)[0]
                new_path = f"{parent}.{new_leaf}"
                ok, msg = self.manager.rename_game_state_path(old_path, new_path)
                if ok:
                    self.selected_state_path = new_path
                    self._set_message("GAME_STATE key renamed")
                else:
                    self._set_message(msg)

        self.state_inline_rename_path = None
        self.state_inline_rename_text = ""
        self.state_inline_rename_caret = 0

    def _update_state_inline_rename(self):
        if getattr(self, "state_inline_rename_path", None) is None:
            return

        if self.input.get_key_down(pygame.K_ESCAPE, self.passcode):
            self._stop_state_inline_rename(False)
            return

        if self.input.get_key_down(pygame.K_RETURN, self.passcode) or self.input.get_key_down(pygame.K_KP_ENTER, self.passcode):
            self._stop_state_inline_rename(True)
            return

        if self.input.get_key_down(pygame.K_LEFT, self.passcode):
            self.state_inline_rename_caret = max(0, self.state_inline_rename_caret - 1)
        if self.input.get_key_down(pygame.K_RIGHT, self.passcode):
            self.state_inline_rename_caret = min(len(self.state_inline_rename_text), self.state_inline_rename_caret + 1)
        if self.input.get_key_down(pygame.K_HOME, self.passcode):
            self.state_inline_rename_caret = 0
        if self.input.get_key_down(pygame.K_END, self.passcode):
            self.state_inline_rename_caret = len(self.state_inline_rename_text)

        entered = self.input.consume_text_input(self.passcode)
        if entered:
            text = "".join(entered)
            left = self.state_inline_rename_text[: self.state_inline_rename_caret]
            right = self.state_inline_rename_text[self.state_inline_rename_caret :]
            self.state_inline_rename_text = left + text + right
            self.state_inline_rename_caret += len(text)

        if self.input.get_key_down(pygame.K_BACKSPACE, self.passcode) and self.state_inline_rename_caret > 0:
            left = self.state_inline_rename_text[: self.state_inline_rename_caret - 1]
            right = self.state_inline_rename_text[self.state_inline_rename_caret :]
            self.state_inline_rename_text = left + right
            self.state_inline_rename_caret -= 1

        if self.input.get_key_down(pygame.K_DELETE, self.passcode) and self.state_inline_rename_caret < len(self.state_inline_rename_text):
            left = self.state_inline_rename_text[: self.state_inline_rename_caret]
            right = self.state_inline_rename_text[self.state_inline_rename_caret + 1 :]
            self.state_inline_rename_text = left + right

    def _stop_state_inline_edit(self, apply_changes):
        if self.state_inline_edit_path is None:
            return

        if apply_changes:
            game_state = getattr(self.manager, "GAME_STATE", None)
            if game_state is None:
                self._set_message("No GAME_STATE available")
            else:
                try:
                    parsed = self._parse_value(self.state_inline_edit_text)
                    game_state.set(self.state_inline_edit_path, parsed)
                    self.fields["state_value"] = json.dumps(parsed, indent=2)
                    self._set_message("GAME_STATE value applied")
                except Exception:
                    self._set_message("Invalid value")

        self.state_inline_edit_path = None
        self.state_inline_edit_text = ""
        self.state_inline_caret = 0

    def _update_state_inline_edit(self):
        if self.state_inline_edit_path is None:
            return

        if self.input.get_key_down(pygame.K_ESCAPE, self.passcode):
            self._stop_state_inline_edit(False)
            return

        if self.input.get_key_down(pygame.K_RETURN, self.passcode) or self.input.get_key_down(pygame.K_KP_ENTER, self.passcode):
            self._stop_state_inline_edit(True)
            return

        if self.input.get_key_down(pygame.K_LEFT, self.passcode):
            self.state_inline_caret = max(0, self.state_inline_caret - 1)
        if self.input.get_key_down(pygame.K_RIGHT, self.passcode):
            self.state_inline_caret = min(len(self.state_inline_edit_text), self.state_inline_caret + 1)
        if self.input.get_key_down(pygame.K_HOME, self.passcode):
            self.state_inline_caret = 0
        if self.input.get_key_down(pygame.K_END, self.passcode):
            self.state_inline_caret = len(self.state_inline_edit_text)

        entered = self.input.consume_text_input(self.passcode)
        if entered:
            text = "".join(entered)
            left = self.state_inline_edit_text[:self.state_inline_caret]
            right = self.state_inline_edit_text[self.state_inline_caret:]
            self.state_inline_edit_text = left + text + right
            self.state_inline_caret += len(text)

        if self.input.get_key_down(pygame.K_BACKSPACE, self.passcode) and self.state_inline_caret > 0:
            left = self.state_inline_edit_text[: self.state_inline_caret - 1]
            right = self.state_inline_edit_text[self.state_inline_caret :]
            self.state_inline_edit_text = left + right
            self.state_inline_caret -= 1

        if self.input.get_key_down(pygame.K_DELETE, self.passcode) and self.state_inline_caret < len(self.state_inline_edit_text):
            left = self.state_inline_edit_text[: self.state_inline_caret]
            right = self.state_inline_edit_text[self.state_inline_caret + 1 :]
            self.state_inline_edit_text = left + right

    def _draw_button(self, surface, rect, label, active=False):
        fill = (65, 78, 95) if active else (38, 38, 38)
        pygame.draw.rect(surface, fill, rect)
        pygame.draw.rect(surface, (95, 95, 95), rect, 1)
        txt = self.small_font.render(label, True, (230, 230, 230))
        surface.blit(txt, (rect.x + 8, rect.y + 6))

    def _line_h(self):
        return max(14, self.small_font.get_height() + 1)

    def _is_json_editor_field(self, key):
        return key in {"component_value", "data_value", "element_json", "state_value"}

    def _json_error_line_index(self, text):
        raw = str(text)
        stripped = raw.strip()
        if not stripped or stripped[0] not in "[{":
            return None
        try:
            json.loads(raw)
            return None
        except Exception as ex:
            line = getattr(ex, "lineno", None)
            if isinstance(line, int) and line > 0:
                return line - 1
        return None

    def _auto_fix_json_commas(self, text):
        raw = str(text)
        stripped = raw.strip()
        if not stripped or stripped[0] not in "[{":
            return raw

        lines = raw.split("\n")
        sig = [i for i, line in enumerate(lines) if line.strip() != ""]
        for p, idx in enumerate(sig[:-1]):
            next_idx = sig[p + 1]
            cur = lines[idx]
            nxt = lines[next_idx].lstrip()

            body = cur.rstrip()
            indent_len = len(cur) - len(cur.lstrip(" "))
            indent = cur[:indent_len]
            content = body[indent_len:]
            content_core = content.rstrip(",")

            if nxt.startswith("}") or nxt.startswith("]"):
                lines[idx] = indent + content_core
                continue

            if not content_core:
                continue
            if content_core.endswith("{") or content_core.endswith("[") or content_core.endswith(":"):
                lines[idx] = indent + content_core
                continue

            lines[idx] = indent + content_core + ","

        fixed = "\n".join(lines)
        fixed = fixed.replace(",,", ",")
        fixed = fixed.replace(",\n}", "\n}")
        fixed = fixed.replace(",\n]", "\n]")
        return fixed

    def _json_comma_suggestions(self, text):
        raw = str(text)
        stripped = raw.strip()
        if not stripped or stripped[0] not in "[{":
            return []

        lines = raw.split("\n")
        sig = [i for i, line in enumerate(lines) if line.strip() != ""]
        out = []
        for p, idx in enumerate(sig[:-1]):
            next_idx = sig[p + 1]
            cur = lines[idx]
            nxt = lines[next_idx].lstrip()

            body = cur.rstrip()
            indent_len = len(cur) - len(cur.lstrip(" "))
            indent = cur[:indent_len]
            content = body[indent_len:]
            content_core = content.rstrip(",")

            if not content_core:
                continue

            if nxt.startswith("}") or nxt.startswith("]"):
                if content.endswith(","):
                    out.append({"line": idx, "kind": "remove_trailing_comma"})
                continue

            if content_core.endswith("{") or content_core.endswith("[") or content_core.endswith(":"):
                continue

            if not content.endswith(","):
                out.append({"line": idx, "kind": "insert_missing_comma"})

        return out

    def _nearest_json_suggestion(self, suggestions, caret_line):
        if not suggestions:
            return None
        line = int(max(0, caret_line))
        return min(suggestions, key=lambda s: (abs(int(s.get("line", 0)) - line), int(s.get("line", 0))))

    def _apply_json_suggestion(self, text, suggestion):
        if not suggestion:
            return text
        lines = str(text).split("\n")
        line_idx = int(suggestion.get("line", -1))
        if line_idx < 0 or line_idx >= len(lines):
            return text

        cur = lines[line_idx]
        kind = suggestion.get("kind")
        if kind == "remove_trailing_comma":
            body = cur.rstrip()
            if body.endswith(","):
                body = body[:-1].rstrip()
                lines[line_idx] = body
        elif kind == "insert_missing_comma":
            body = cur.rstrip()
            if body and not body.endswith(","):
                lines[line_idx] = body + ","

        return "\n".join(lines)

    def _split_lines(self, text):
        lines = str(text).split("\n")
        return lines if lines else [""]

    def _clamp_caret(self, key):
        text = self.fields.get(key, "")
        idx = int(self.field_caret.get(key, len(text)))
        idx = max(0, min(len(text), idx))
        self.field_caret[key] = idx
        return idx

    def _set_selection(self, key, anchor, active):
        self.field_sel_anchor[key] = int(anchor)
        self.field_sel_active[key] = int(active)

    def _clear_selection(self, key, caret):
        self._set_selection(key, caret, caret)

    def _selection_range(self, key):
        a = int(self.field_sel_anchor.get(key, self.field_caret.get(key, 0)))
        b = int(self.field_sel_active.get(key, self.field_caret.get(key, 0)))
        if a == b:
            return None
        return (min(a, b), max(a, b))

    def _line_range_from_selection(self, text, key):
        sel = self._selection_range(key)
        if not sel:
            caret = self._clamp_caret(key)
            line, _ = self._index_to_line_col(text, caret)
            return line, line
        s, e = sel
        sline, _ = self._index_to_line_col(text, s)
        end_probe = max(s, e - 1)
        eline, _ = self._index_to_line_col(text, end_probe)
        return sline, eline

    def _select_line_span(self, key, text, start_line, end_line):
        lines = self._split_lines(text)
        if not lines:
            return
        start_line = max(0, min(len(lines) - 1, int(start_line)))
        end_line = max(0, min(len(lines) - 1, int(end_line)))
        if end_line < start_line:
            start_line, end_line = end_line, start_line

        start_idx = self._line_col_to_index(text, start_line, 0)
        end_idx = self._line_col_to_index(text, end_line, len(lines[end_line]))
        if end_line < len(lines) - 1:
            end_idx += 1
        self._set_selection(key, start_idx, end_idx)
        self.field_caret[key] = end_idx

    def _index_to_line_col(self, text, idx):
        idx = max(0, min(len(text), idx))
        line = 0
        col = 0
        i = 0
        while i < idx:
            if text[i] == "\n":
                line += 1
                col = 0
            else:
                col += 1
            i += 1
        return line, col

    def _line_col_to_index(self, text, target_line, target_col):
        lines = self._split_lines(text)
        line = max(0, min(len(lines) - 1, int(target_line)))
        col = max(0, min(len(lines[line]), int(target_col)))
        idx = 0
        for i in range(line):
            idx += len(lines[i]) + 1
        idx += col
        return idx

    def _is_word_char(self, ch):
        return ch.isalnum() or ch == "_"

    def _prev_token_boundary(self, text, idx):
        idx = max(0, min(len(text), idx))
        if idx == 0:
            return 0

        i = idx
        while i > 0 and text[i - 1].isspace():
            i -= 1
        if i == 0:
            return 0

        if self._is_word_char(text[i - 1]):
            while i > 0 and self._is_word_char(text[i - 1]):
                i -= 1
            return i

        while i > 0 and (not text[i - 1].isspace()) and (not self._is_word_char(text[i - 1])):
            i -= 1
        return i

    def _next_token_boundary(self, text, idx):
        idx = max(0, min(len(text), idx))
        if idx >= len(text):
            return len(text)

        i = idx
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return len(text)

        if self._is_word_char(text[i]):
            while i < len(text) and self._is_word_char(text[i]):
                i += 1
            return i

        while i < len(text) and (not text[i].isspace()) and (not self._is_word_char(text[i])):
            i += 1
        return i

    def _content_rect_for_field(self, rect):
        return pygame.Rect(rect.x + 6, rect.y + 18, max(8, rect.w - 28), max(8, rect.h - 22))

    def _expanded_field_rect(self, key, rect):
        large_keys = {"component_value", "data_value", "element_json", "state_value"}
        if self.active_field != key or key not in large_keys:
            return rect
        sb = self._sidebar_rect()
        if key == "element_json":
            footer_h = 42
            return pygame.Rect(sb.x + 10, sb.y + 70, sb.w - 20, sb.h - 70 - footer_h - 10)
        return pygame.Rect(sb.x + 10, sb.y + 70, sb.w - 20, sb.h - 88)

    def _metadata_element_buttons(self, expanded=None):
        sb = self._sidebar_rect()
        if expanded is None:
            expanded = (self.active_field == "element_json")
        if expanded:
            y = sb.bottom - 36
        else:
            y = 388
        load_btn = pygame.Rect(sb.x + 10, y, 120, 30)
        apply_btn = pygame.Rect(sb.x + 140, y, 120, 30)
        return load_btn, apply_btn

    def _element_json_diff_paths(self, current, target, base_path=""):
        diffs = []
        if isinstance(current, dict) and isinstance(target, dict):
            keys = set(current.keys()) | set(target.keys())
            for key in sorted(keys):
                next_path = f"{base_path}.{key}" if base_path else str(key)
                if key not in current or key not in target:
                    diffs.append(next_path)
                    continue
                diffs.extend(self._element_json_diff_paths(current[key], target[key], next_path))
            return diffs

        if isinstance(current, list) and isinstance(target, list):
            if len(current) != len(target):
                diffs.append(base_path)
            count = min(len(current), len(target))
            for i in range(count):
                next_path = f"{base_path}[{i}]" if base_path else f"[{i}]"
                diffs.extend(self._element_json_diff_paths(current[i], target[i], next_path))
            return diffs

        if current != target:
            diffs.append(base_path)
        return diffs

    def _element_json_path_is_instant_safe(self, path):
        normalized = str(path).lower()
        while "[" in normalized and "]" in normalized:
            lidx = normalized.find("[")
            ridx = normalized.find("]", lidx)
            if ridx == -1:
                break
            normalized = normalized[:lidx] + normalized[ridx + 1 :]

        segments = [seg for seg in normalized.split(".") if seg]
        if not segments:
            return False

        if normalized == "container.pos" or normalized == "container.size":
            return True

        for seg in segments:
            if "color" in seg or "colour" in seg or "tint" in seg:
                return True
        return False

    def _apply_selected_element_json(self, parsed, silent=False, preserve_component_selection=False):
        selected = self._selected_element()
        if selected is None:
            if not silent:
                self._set_message("No selected element")
            return False
        if self._is_locked_element(selected):
            if not silent:
                self._set_message("Selected element is locked")
            return False
        if not isinstance(parsed, dict):
            if not silent:
                self._set_message("Element JSON must be an object")
            return False

        if self.manager.is_array_source(selected.path) and isinstance(parsed.get("array"), dict):
            ok, msg = self.manager.regenerate_array_source(selected.path, parsed)
            if not ok:
                if not silent:
                    self._set_message(msg)
                return False

            selected = self._selected_element()
            if selected is None:
                if not silent:
                    self._set_message("Array source missing after regenerate")
                return False

            if preserve_component_selection and self.selected_component:
                if selected.getComponent(self.selected_component) is None:
                    self.selected_component = None
                    self.selected_component_path = ""
                    self.fields["component_value"] = ""
                elif self.selected_component_path:
                    value = self._component_path_value()
                    self.fields["component_value"] = json.dumps(value, indent=2)
            else:
                self.selected_component = None
                self.selected_component_path = ""
                self.fields["component_value"] = ""

            self._sync_transform_fields()
            if not silent:
                self._set_message("Element JSON applied")
            return True

        selected.components.clear()
        selected.component_order.clear()
        selected.local_data = dict(parsed.get("data", {}))
        selected.elmData = json.loads(json.dumps(parsed))

        for key, value in parsed.items():
            if key in {"data", "copy", "array"}:
                continue
            module_name = f"{key}Component"
            if module_name not in self.manager.data.get("uiComponents", {}):
                continue
            selected.addComponent(key, self.manager.data, value)

        if preserve_component_selection and self.selected_component:
            if selected.getComponent(self.selected_component) is None:
                self.selected_component = None
                self.selected_component_path = ""
                self.fields["component_value"] = ""
            elif self.selected_component_path:
                value = self._component_path_value()
                self.fields["component_value"] = json.dumps(value, indent=2)
        else:
            self.selected_component = None
            self.selected_component_path = ""
            self.fields["component_value"] = ""

        self._sync_transform_fields()
        if not silent:
            self._set_message("Element JSON applied")
        return True

    def _try_instant_apply_element_json(self):
        selected = self._selected_element()
        if selected is None or self._is_locked_element(selected):
            return False

        text = self.fields.get("element_json", "")
        try:
            parsed = json.loads(text)
        except Exception:
            return False
        if not isinstance(parsed, dict):
            return False

        current_raw = self.manager.get_array_source_raw(selected.path)
        if current_raw is None:
            current_raw = getattr(selected, "elmData", {}) or {}
        current = json.loads(json.dumps(current_raw))
        diffs = self._element_json_diff_paths(current, parsed)
        if not diffs:
            return False
        if not all(self._element_json_path_is_instant_safe(path) for path in diffs):
            return False

        return self._apply_selected_element_json(parsed, silent=True, preserve_component_selection=True)

    def _set_caret_from_click(self, key, mx, my):
        rect = self.field_rect_cache.get(key)
        if rect is None:
            return
        content = self._content_rect_for_field(rect)
        text = self.fields.get(key, "")
        lines = self._split_lines(text)
        line_h = self._line_h()
        scroll = max(0, int(self.field_scroll.get(key, 0)))

        rel_y = my - content.y
        target_line = scroll + max(0, int(rel_y // line_h))
        target_line = max(0, min(len(lines) - 1, target_line))

        line_text = lines[target_line]
        rel_x = max(0, mx - content.x)
        col = 0
        while col < len(line_text):
            w = self.small_font.size(line_text[: col + 1])[0]
            if w > rel_x:
                break
            col += 1

        self.field_caret[key] = self._line_col_to_index(text, target_line, col)

    def _focus_field_from_click(self, key, mx, my, allow_numeric_drag=False):
        self.active_field = key
        self._set_caret_from_click(key, mx, my)
        self._clear_selection(key, self.field_caret.get(key, 0))
        if allow_numeric_drag and key in {"pos_x", "pos_y", "size_w", "size_h"}:
            self._begin_numeric_drag(key)
            self.field_mouse_select_key = None
        else:
            self.numeric_drag_field = None
            self.field_mouse_select_key = key
            self.field_mouse_select_anchor = int(self.field_caret.get(key, 0))

    def _update_field_mouse_selection(self):
        key = self.field_mouse_select_key
        if key is None:
            return

        if self.input.get_mouse_button_up(1, self.passcode):
            self.field_mouse_select_key = None
            return

        if not self.input.get_mouse_button(1, self.passcode):
            return

        if self.active_field != key:
            self.field_mouse_select_key = None
            return

        if self.numeric_drag_field is not None:
            return

        rect = self.field_rect_cache.get(key)
        if rect is None:
            return

        mx, my = self.input.get_mouse_position(self.passcode)
        self._set_caret_from_click(key, mx, my)
        caret = int(self.field_caret.get(key, 0))
        self._set_selection(key, self.field_mouse_select_anchor, caret)

    def _tokenize_json_line(self, line):
        tokens = []
        i = 0
        n = len(line)

        def emit(text, color):
            if text:
                tokens.append((text, color))

        while i < n:
            ch = line[i]
            if ch.isspace():
                j = i
                while j < n and line[j].isspace():
                    j += 1
                emit(line[i:j], (200, 200, 200))
                i = j
                continue

            if ch in "{}[]:,":
                emit(ch, (180, 180, 180))
                i += 1
                continue

            if ch == '"':
                j = i + 1
                esc = False
                while j < n:
                    c = line[j]
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        j += 1
                        break
                    j += 1
                token = line[i:j]
                k = j
                while k < n and line[k].isspace():
                    k += 1
                color = (120, 210, 255) if (k < n and line[k] == ":") else (176, 255, 176)
                emit(token, color)
                i = j
                continue

            if ch.isdigit() or ch == "-":
                j = i + 1
                while j < n and (line[j].isdigit() or line[j] in ".eE+-"):
                    j += 1
                emit(line[i:j], (255, 215, 130))
                i = j
                continue

            if line.startswith("true", i) or line.startswith("false", i) or line.startswith("null", i):
                if line.startswith("true", i):
                    emit("true", (200, 160, 255))
                    i += 4
                elif line.startswith("false", i):
                    emit("false", (200, 160, 255))
                    i += 5
                else:
                    emit("null", (200, 160, 255))
                    i += 4
                continue

            j = i + 1
            while j < n and (not line[j].isspace()) and line[j] not in "{}[]:,":
                j += 1
            emit(line[i:j], (235, 235, 235))
            i = j

        return tokens

    def _draw_tokenized_line(self, surface, text, x, y, clip_rect):
        tx = x
        for token, color in self._tokenize_json_line(text):
            surf = self.small_font.render(token, True, color)
            if tx < clip_rect.right and tx + surf.get_width() > clip_rect.x:
                surface.blit(surf, (tx, y))
            tx += surf.get_width()

    def _detect_indent_size(self, text):
        lines = self._split_lines(text)
        counts = []
        for line in lines:
            stripped = line.lstrip(" ")
            if not stripped:
                continue
            lead = len(line) - len(stripped)
            if lead > 0:
                counts.append(lead)
        if not counts:
            return 4
        even = sum(1 for c in counts if c % 2 == 0)
        four = sum(1 for c in counts if c % 4 == 0)
        if even > 0 and even >= (len(counts) * 0.7) and four < even:
            return 2
        return 4

    def _draw_indent_guides(self, surface, line, x, y, line_h, indent_size, clip_rect):
        if indent_size <= 0:
            return
        leading = len(line) - len(line.lstrip(" "))
        if leading < indent_size:
            return
        levels = leading // indent_size
        indent_px = self.small_font.size(" " * indent_size)[0]
        for i in range(1, levels + 1):
            gx = x + i * indent_px - 2
            if clip_rect.x <= gx <= clip_rect.right:
                pygame.draw.line(surface, (35, 35, 44), (gx, y + 1), (gx, y + line_h), 1)

    def _parse_hex_color(self, text):
        if not isinstance(text, str):
            return None
        raw = text.strip()
        if raw.startswith("#"):
            raw = raw[1:]
        if len(raw) != 6:
            return None
        try:
            return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
        except Exception:
            return None

    def _hex_color_info_from_field_text(self, text):
        if not isinstance(text, str):
            return None
        stripped = text.strip()

        rgb = self._parse_hex_color(stripped)
        if rgb is not None:
            return {"color": rgb, "mode": "raw"}

        if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
            try:
                value = json.loads(stripped)
            except Exception:
                value = None
            if isinstance(value, str):
                rgb = self._parse_hex_color(value)
                if rgb is not None:
                    return {"color": rgb, "mode": "json_string"}
        return None

    def _hex_token_info_at_index(self, key, index):
        text = self.fields.get(key, "")
        if not text:
            return None

        idx = max(0, min(len(text), int(index)))

        # Check quoted token: "#RRGGBB"
        for i in range(max(0, idx - 10), min(len(text), idx + 12)):
            if i + 9 > len(text):
                break
            chunk = text[i:i + 9]
            if len(chunk) == 9 and chunk[0] == '"' and chunk[1] == '#' and chunk[-1] == '"':
                hex_part = chunk[1:8]
                if self._parse_hex_color(hex_part) is not None and i <= idx <= (i + 9):
                    return {
                        "start": i,
                        "end": i + 9,
                        "mode": "json_string",
                        "color": self._parse_hex_color(hex_part),
                    }

        # Check raw token: #RRGGBB
        for i in range(max(0, idx - 8), min(len(text), idx + 9)):
            if i + 7 > len(text):
                break
            chunk = text[i:i + 7]
            if len(chunk) == 7 and chunk[0] == '#':
                hex_part = chunk
                color = self._parse_hex_color(hex_part)
                if color is None:
                    continue
                if i <= idx <= (i + 7):
                    return {
                        "start": i,
                        "end": i + 7,
                        "mode": "raw",
                        "color": color,
                    }

        return None

    def _format_hex(self, color):
        r, g, b = color
        return f"#{int(r):02X}{int(g):02X}{int(b):02X}"

    def _hsv_to_rgb(self, h, s, v):
        r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0, max(0.0, min(1.0, float(s))), max(0.0, min(1.0, float(v))))
        return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))

    def _rgb_to_hsv(self, color):
        r, g, b = color
        return colorsys.rgb_to_hsv(max(0.0, min(1.0, r / 255.0)), max(0.0, min(1.0, g / 255.0)), max(0.0, min(1.0, b / 255.0)))

    def _current_picker_rgb(self):
        return self._hsv_to_rgb(self.color_picker_h, self.color_picker_s, self.color_picker_v)

    def _color_picker_rect(self):
        sb = self._sidebar_rect()
        sw, sh = self._screen_size()
        w = 310
        h = 280
        gap = 10
        x = (sb.x - w - gap) if self.sidebar_side == "right" else (sb.right + gap)
        y = sb.centery - (h // 2)
        x = max(10, min(sw - w - 10, x))
        y = max(10, min(sh - h - 10, y))
        return pygame.Rect(int(x), int(y), int(w), int(h))

    def _wheel_radius(self, picker_rect):
        return max(24, min(96, (picker_rect.h - 90) // 2))

    def _wheel_center(self, picker_rect):
        r = self._wheel_radius(picker_rect)
        return (picker_rect.x + 18 + r, picker_rect.y + 24 + r)

    def _value_slider_rect(self, picker_rect):
        cx, cy = self._wheel_center(picker_rect)
        r = self._wheel_radius(picker_rect)
        return pygame.Rect(cx + r + 14, cy - r, 18, r * 2)

    def _color_apply_rect(self, picker_rect):
        return pygame.Rect(picker_rect.x + 14, picker_rect.bottom - 34, 90, 24)

    def _color_cancel_rect(self, picker_rect):
        return pygame.Rect(picker_rect.x + 14, picker_rect.bottom - 34, 90, 24)

    def _wheel_surface(self, radius):
        radius = int(max(8, radius))
        cache_key = radius
        surf = self._color_wheel_cache.get(cache_key)
        if surf is not None:
            return surf

        size = radius * 2 + 1
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = radius
        cy = radius
        for y in range(size):
            for x in range(size):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    continue
                sat = dist / float(radius)
                hue = (math.atan2(dy, dx) / (2.0 * math.pi)) % 1.0
                r, g, b = self._hsv_to_rgb(hue, sat, 1.0)
                surf.set_at((x, y), (r, g, b, 255))

        self._color_wheel_cache[cache_key] = surf
        return surf

    def _set_picker_hs_from_pos(self, picker_rect, mx, my):
        cx, cy = self._wheel_center(picker_rect)
        r = self._wheel_radius(picker_rect)
        dx = float(mx - cx)
        dy = float(my - cy)
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > r and dist > 0.0:
            scale = r / dist
            dx *= scale
            dy *= scale
            dist = r
        self.color_picker_s = max(0.0, min(1.0, dist / float(r)))
        self.color_picker_h = (math.atan2(dy, dx) / (2.0 * math.pi)) % 1.0

    def _set_picker_v_from_pos(self, picker_rect, my):
        srect = self._value_slider_rect(picker_rect)
        if srect.h <= 0:
            return
        t = max(0.0, min(1.0, (my - srect.y) / float(srect.h)))
        self.color_picker_v = 1.0 - t

    def _draw_color_picker(self, surface):
        if not self.color_picker_open:
            return

        rect = self._color_picker_rect()
        pygame.draw.rect(surface, (6, 6, 6), rect)
        pygame.draw.rect(surface, (100, 100, 100), rect, 1)

        title = self.small_font.render("Color Picker", True, (235, 235, 235))
        surface.blit(title, (rect.x + 12, rect.y + 10))

        cx, cy = self._wheel_center(rect)
        radius = self._wheel_radius(rect)
        wheel = self._wheel_surface(radius)
        surface.blit(wheel, (cx - radius, cy - radius))

        wx = int(round(cx + math.cos(self.color_picker_h * 2.0 * math.pi) * (self.color_picker_s * radius)))
        wy = int(round(cy + math.sin(self.color_picker_h * 2.0 * math.pi) * (self.color_picker_s * radius)))
        pygame.draw.circle(surface, (255, 255, 255), (wx, wy), 5, 1)

        srect = self._value_slider_rect(rect)
        for py in range(srect.h):
            t = py / float(max(1, srect.h - 1))
            v = 1.0 - t
            rr, gg, bb = self._hsv_to_rgb(self.color_picker_h, self.color_picker_s, v)
            pygame.draw.line(surface, (rr, gg, bb), (srect.x, srect.y + py), (srect.right - 1, srect.y + py))
        pygame.draw.rect(surface, (120, 120, 120), srect, 1)
        vy = int(srect.y + (1.0 - self.color_picker_v) * srect.h)
        pygame.draw.line(surface, (255, 255, 255), (srect.x - 2, vy), (srect.right + 2, vy), 2)

        preview = pygame.Rect(rect.right - 76, rect.y + 10, 58, 28)
        current_rgb = self._current_picker_rgb()
        pygame.draw.rect(surface, current_rgb, preview)
        pygame.draw.rect(surface, (180, 180, 180), preview, 1)

        hex_text = self.small_font.render(self._format_hex(current_rgb), True, (230, 230, 230))
        surface.blit(hex_text, (rect.x + 12, rect.y + 32))

        hsv_label = self.small_font.render(
            f"H:{int(self.color_picker_h*360):03d}  S:{int(self.color_picker_s*100):02d}%  V:{int(self.color_picker_v*100):02d}%",
            True,
            (210, 210, 210),
        )
        surface.blit(hsv_label, (rect.x + 12, rect.bottom - 52))

        self._draw_button(surface, self._color_cancel_rect(rect), "close")

    def _open_color_picker(self, target, mode, color):
        self.color_picker_open = True
        self.color_picker_target = target
        self.color_picker_mode = mode
        h, s, v = self._rgb_to_hsv(tuple(color))
        self.color_picker_h = h
        self.color_picker_s = s
        self.color_picker_v = v
        self.color_picker_drag_mode = None

    def _apply_color_picker_value(self):
        if not self.color_picker_target:
            return
        hex_text = self._format_hex(self._current_picker_rgb())
        target_type = self.color_picker_target.get("type")

        if target_type == "field":
            key = self.color_picker_target.get("key")
            if key:
                if self.color_picker_mode == "json_string":
                    self.fields[key] = json.dumps(hex_text)
                else:
                    self.fields[key] = hex_text
                if key == "element_json":
                    self._try_instant_apply_element_json()
            return

        if target_type == "field_token":
            key = self.color_picker_target.get("key")
            start = int(self.color_picker_target.get("start", 0))
            end = int(self.color_picker_target.get("end", start))
            if key:
                text = self.fields.get(key, "")
                start = max(0, min(len(text), start))
                end = max(start, min(len(text), end))
                repl = json.dumps(hex_text) if self.color_picker_mode == "json_string" else hex_text
                self.fields[key] = text[:start] + repl + text[end:]
                caret = start + len(repl)
                self.field_caret[key] = caret
                self.field_sel_anchor[key] = caret
                self.field_sel_active[key] = caret
                if key == "element_json":
                    self._try_instant_apply_element_json()
            return

        if target_type == "component_inline":
            path = self.color_picker_target.get("path")
            if not path:
                return
            self.selected_component_path = path
            selected = self._selected_element()
            if selected is None or self._is_locked_element(selected):
                return
            comp = selected.getComponent(self.selected_component)
            if comp is None or not isinstance(comp.config, dict):
                return

            PathDict.set(comp.config, path, hex_text)
            selected.elmData[self.selected_component] = json.loads(json.dumps(comp.config))
            self.fields["component_value"] = json.dumps(hex_text, indent=2)

            if self.component_inline_edit_path != path:
                self._start_component_inline_edit(path)
            self.component_inline_edit_text = json.dumps(hex_text) if self.color_picker_mode == "json_string" else hex_text
            self.component_inline_caret = len(self.component_inline_edit_text)
            return

        if target_type == "state_inline":
            path = self.color_picker_target.get("path")
            if not path or self._is_state_value_locked(path):
                return
            game_state = getattr(self.manager, "GAME_STATE", None)
            if game_state is None:
                return

            game_state.set(path, hex_text)
            self.fields["state_value"] = json.dumps(hex_text, indent=2)

            self.selected_state_path = path
            if self.state_inline_edit_path != path:
                self._start_state_inline_edit(path)
            self.state_inline_edit_text = json.dumps(hex_text) if self.color_picker_mode == "json_string" else hex_text
            self.state_inline_caret = len(self.state_inline_edit_text)

    def _close_color_picker(self, apply_changes):
        if apply_changes:
            self._apply_color_picker_value()
        self.color_picker_open = False
        self.color_picker_target = None
        self.color_picker_mode = None
        self.color_picker_drag_mode = None

    def _update_color_picker_input(self):
        if not self.color_picker_open:
            return False

        if self.input.get_key_down(pygame.K_ESCAPE, self.passcode):
            self._close_color_picker(False)
            return True

        rect = self._color_picker_rect()
        mx, my = self.input.get_mouse_position(self.passcode)

        if self.input.get_mouse_button_up(1, self.passcode):
            self.color_picker_drag_mode = None

        if self.color_picker_drag_mode is not None and self.input.get_mouse_button(1, self.passcode):
            if self.color_picker_drag_mode == "wheel":
                self._set_picker_hs_from_pos(rect, mx, my)
                self._apply_color_picker_value()
            elif self.color_picker_drag_mode == "value":
                self._set_picker_v_from_pos(rect, my)
                self._apply_color_picker_value()

        if self.input.get_mouse_button_down(1, self.passcode):
            if self._color_cancel_rect(rect).collidepoint((mx, my)):
                self._close_color_picker(False)
                return True

            cx, cy = self._wheel_center(rect)
            radius = self._wheel_radius(rect)
            dx = mx - cx
            dy = my - cy
            if (dx * dx + dy * dy) <= (radius * radius):
                self.color_picker_drag_mode = "wheel"
                self._set_picker_hs_from_pos(rect, mx, my)
                self._apply_color_picker_value()
                return True

            srect = self._value_slider_rect(rect)
            if srect.collidepoint((mx, my)):
                self.color_picker_drag_mode = "value"
                self._set_picker_v_from_pos(rect, my)
                self._apply_color_picker_value()
                return True

            if not rect.collidepoint((mx, my)):
                self._close_color_picker(False)
                return True

        return True

    def _draw_field(self, surface, rect, key, label, allow_color_picker=False):
        draw_rect = self._expanded_field_rect(key, rect)
        self.field_rect_cache[key] = draw_rect.copy()

        pygame.draw.rect(surface, (17, 17, 17), draw_rect)
        border = (95, 145, 220) if self.active_field == key else (75, 75, 75)
        pygame.draw.rect(surface, border, draw_rect, 1)
        title = self.small_font.render(label, True, (180, 180, 180))
        surface.blit(title, (draw_rect.x + 6, draw_rect.y + 3))

        content = self._content_rect_for_field(draw_rect)
        text = self.fields.get(key, "")
        lines = self._split_lines(text)
        line_h = self._line_h()
        visible = max(1, content.h // line_h)
        indent_size = self._detect_indent_size(text)
        json_error_line = self._json_error_line_index(text) if self._is_json_editor_field(key) else None
        json_suggestions = self._json_comma_suggestions(text) if self._is_json_editor_field(key) else []

        caret_idx = self._clamp_caret(key) if self.active_field == key else int(self.field_caret.get(key, len(text)))
        caret_line, caret_col = self._index_to_line_col(text, caret_idx)
        sel = self._selection_range(key) if self.active_field == key else None
        nearest_suggestion = self._nearest_json_suggestion(json_suggestions, caret_line) if json_suggestions else None
        suggestion_lines = {int(s.get("line", -1)): s for s in json_suggestions}
        nearest_line = int(nearest_suggestion.get("line", -1)) if nearest_suggestion else -1
        suppress_error_line = False
        if json_error_line is not None and (json_error_line - 1) in suggestion_lines:
            suppress_error_line = True

        scroll = max(0, int(self.field_scroll.get(key, 0)))
        max_scroll = max(0, len(lines) - visible)

        if self.active_field == key:
            if caret_line < scroll:
                scroll = caret_line
            elif caret_line >= scroll + visible:
                scroll = caret_line - visible + 1
        scroll = max(0, min(max_scroll, scroll))
        self.field_scroll[key] = scroll

        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(content))

        y = content.y
        start = scroll
        end = min(len(lines), start + visible)
        for li in range(start, end):
            if json_error_line is not None and li == json_error_line and not suppress_error_line:
                pygame.draw.rect(surface, (58, 18, 18), pygame.Rect(content.x, y, content.w, line_h))
            elif li in suggestion_lines:
                col = (26, 46, 88) if li == nearest_line else (14, 28, 58)
                pygame.draw.rect(surface, col, pygame.Rect(content.x, y, content.w, line_h))
            self._draw_indent_guides(surface, lines[li], content.x, y, line_h, indent_size, content)
            if sel is not None:
                sel_start, sel_end = sel
                line_start_idx = self._line_col_to_index(text, li, 0)
                line_end_idx = line_start_idx + len(lines[li])
                if sel_end > line_start_idx and sel_start < (line_end_idx + 1):
                    h_start = max(sel_start, line_start_idx)
                    h_end = min(sel_end, line_end_idx)
                    c1 = max(0, h_start - line_start_idx)
                    c2 = max(0, h_end - line_start_idx)
                    x1 = content.x + self.small_font.size(lines[li][:c1])[0]
                    x2 = content.x + self.small_font.size(lines[li][:c2])[0]
                    if sel_end > line_end_idx:
                        x2 = max(x2, x1 + 6)
                    if x2 > x1:
                        pygame.draw.rect(surface, (58, 87, 130), pygame.Rect(x1, y, x2 - x1, line_h))
            self._draw_tokenized_line(surface, lines[li], content.x, y, content)
            y += line_h

        if self.active_field == key:
            if start <= caret_line < end:
                line_text = lines[caret_line]
                cx = content.x + self.small_font.size(line_text[:caret_col])[0]
                cy = content.y + (caret_line - start) * line_h
                pygame.draw.line(surface, (245, 245, 245), (cx, cy), (cx, cy + line_h - 2), 1)

        surface.set_clip(old_clip)

        if allow_color_picker:
            info = self._hex_color_info_from_field_text(self.fields.get(key, ""))
            if info is not None:
                btn = pygame.Rect(draw_rect.right - 22, draw_rect.y + 17, 16, 16)
                pygame.draw.rect(surface, info["color"], btn)
                pygame.draw.rect(surface, (220, 220, 220), btn, 1)
                self._color_picker_buttons.append(
                    {
                        "rect": btn,
                        "target": {"type": "field", "key": key},
                        "mode": info["mode"],
                        "color": info["color"],
                    }
                )

    def _tab_button_rect(self, i):
        sb = self._sidebar_rect()
        x = sb.x + 10 + i * 112
        return pygame.Rect(x, sb.y + 34, 106, 28)

    def _draw_sidebar(self, surface):
        self._color_picker_buttons = []
        self.field_rect_cache = {}

        sb = self._sidebar_rect()
        pygame.draw.rect(surface, (8, 8, 8), sb)
        pygame.draw.line(surface, (75, 75, 75), (sb.x, sb.y), (sb.x, sb.bottom), 2)

        title = self.font.render("UI Editor", True, (235, 235, 235))
        surface.blit(title, (sb.x + 10, 8))

        move_btn = self._sidebar_move_button_rect()
        move_label = "<" if self.sidebar_side == "right" else ">"
        self._draw_button(surface, move_btn, move_label)

        for i, tab_name in enumerate(self.tabs):
            self._draw_button(surface, self._tab_button_rect(i), tab_name, active=(self.tab == tab_name))

        if self.tab == "elements":
            self._draw_elements_tab(surface)
        elif self.tab == "components":
            self._draw_components_tab(surface)
        elif self.tab == "metadata":
            self._draw_metadata_tab(surface)
        elif self.tab == "state":
            self._draw_state_tab(surface)

        self._draw_color_picker(surface)

        if self.message and self.message_time > 0.0:
            msg = self.small_font.render(self.message, True, (255, 210, 120))
            surface.blit(msg, (sb.x + 10, sb.bottom - 24))

    def _sidebar_move_button_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.right - 40, 6, 30, 24)

    def _elements_list_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.x + 10, 76, sb.w - 20, 260)

    def _components_list_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.x + 10, 76, sb.w - 20, 180)

    def _component_tree_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.x + 10, 308, sb.w - 20, 190)

    def _state_list_rect(self):
        sb = self._sidebar_rect()
        return pygame.Rect(sb.x + 10, 76, sb.w - 20, 290)

    def _visible_element_rows(self):
        paths = sorted([elm.path for elm in self.manager.flattenElements()])
        rows = []
        for path in paths:
            parts = path.split(".")
            hidden = False
            for i in range(1, len(parts)):
                ancestor = ".".join(parts[:i])
                if ancestor in self.collapsed_element_nodes:
                    hidden = True
                    break
            if hidden:
                continue

            prefix = f"{path}."
            has_children = any(other != path and other.startswith(prefix) for other in paths)
            rows.append({
                "path": path,
                "depth": max(0, len(parts) - 1),
                "has_children": has_children,
                "collapsed": path in self.collapsed_element_nodes,
            })
        return rows

    def _iter_state_rows(self):
        game_state = getattr(self.manager, "GAME_STATE", None)
        root = getattr(game_state, "state", None)
        if not isinstance(root, dict):
            return []

        rows = []

        def walk(node, path, depth):
            keys = sorted(node.keys())
            for key in keys:
                value = node[key]
                current_path = f"{path}.{key}" if path else key
                is_branch = isinstance(value, dict)
                rows.append({
                    "path": current_path,
                    "label": key,
                    "depth": depth,
                    "is_branch": is_branch,
                    "collapsed": current_path in self.collapsed_state_nodes,
                    "value": value,
                })
                if is_branch and current_path not in self.collapsed_state_nodes:
                    walk(value, current_path, depth + 1)

        walk(root, "", 0)
        return rows

    def _iter_component_rows(self):
        selected = self._selected_element()
        if selected is None or not self.selected_component:
            return []
        comp = selected.getComponent(self.selected_component)
        if comp is None or not isinstance(comp.config, dict):
            return []

        rows = []

        def walk(node, path, depth):
            keys = sorted(node.keys())
            for key in keys:
                value = node[key]
                current_path = f"{path}.{key}" if path else key
                is_branch = isinstance(value, dict)
                rows.append({
                    "path": current_path,
                    "label": key,
                    "depth": depth,
                    "is_branch": is_branch,
                    "collapsed": current_path in self.collapsed_component_nodes,
                    "value": value,
                })
                if is_branch and current_path not in self.collapsed_component_nodes:
                    walk(value, current_path, depth + 1)

        walk(comp.config, "", 0)
        return rows

    def _component_path_value(self):
        selected = self._selected_element()
        if selected is None or not self.selected_component_path:
            return None
        comp = selected.getComponent(self.selected_component)
        if comp is None:
            return None
        return PathDict.get(comp.config, self.selected_component_path)

    def _remove_component_path(self, comp_config, path):
        parts = path.split(".")
        node = comp_config
        for p in parts[:-1]:
            if not isinstance(node, dict) or p not in node:
                return False
            node = node[p]
        if isinstance(node, dict) and parts[-1] in node:
            del node[parts[-1]]
            return True
        return False

    def _load_selected_element_json(self):
        selected = self._selected_element()
        if selected is None:
            return

        raw_source = self.manager.get_array_source_raw(selected.path)
        if raw_source is not None and self.manager.is_array_source(selected.path):
            self.fields["element_json"] = json.dumps(raw_source, indent=2)
            return

        payload = {}
        if selected.local_data:
            payload["data"] = json.loads(json.dumps(selected.local_data))
        for name in selected.component_order:
            comp = selected.getComponent(name)
            if comp is not None:
                payload[name] = json.loads(json.dumps(comp.config))
        for key, value in selected.elmData.items():
            if key in {"data"}:
                continue
            if key in payload:
                continue
            payload[key] = json.loads(json.dumps(value))
        self.fields["element_json"] = json.dumps(payload, indent=2)

    def _load_selected_state_value(self):
        key = str(self.selected_state_path or "").strip()
        if not key:
            return
        if self.manager.GAME_STATE is None:
            return
        value = self.manager.GAME_STATE.get(key)
        self.fields["state_value"] = json.dumps(value, indent=2)

    def _element_root_key(self, path):
        parts = str(path).split(".")
        if len(parts) >= 2 and parts[0] == "screen":
            return parts[1]
        return parts[0] if parts else ""

    def _element_root_hue(self, path):
        root = self._element_root_key(path)
        if root in {"", "screen"}:
            return 0.60
        hseed = sum((i + 1) * ord(c) for i, c in enumerate(root))
        return (hseed % 360) / 360.0

    def _element_row_color(self, path, depth, is_selected, locked):
        if is_selected:
            return (52, 72, 98)
        hue = self._element_root_hue(path)
        sat = 0.38 if not locked else 0.22
        base_val = 0.24
        val = base_val / (1.0 + (max(0, int(depth)) * 0.55))
        val = max(0.10, min(0.28, val))
        r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _draw_elements_list(self, surface):
        rect = self._elements_list_rect()
        pygame.draw.rect(surface, (15, 15, 15), rect)
        pygame.draw.rect(surface, (75, 75, 75), rect, 1)

        rows = self._visible_element_rows()
        visible_rows = max(1, rect.h // 22)
        self.element_scroll = max(0, min(self.element_scroll, max(0, len(rows) - visible_rows)))
        start = self.element_scroll
        end = min(len(rows), start + visible_rows)

        y = rect.y + 2
        for i in range(start, end):
            item = rows[i]
            path = item["path"]
            row = pygame.Rect(rect.x + 2, y, rect.w - 4, 20)
            is_selected = path == self.selected_path
            locked = self.manager.is_array_locked(path) or path == "screen"
            color = self._element_row_color(path, item["depth"], is_selected, locked)
            pygame.draw.rect(surface, color, row)

            x = row.x + 6 + item["depth"] * 14
            if item["has_children"]:
                marker = ">" if item["collapsed"] else "v"
                marker_surf = self.small_font.render(marker, True, (190, 190, 190))
                surface.blit(marker_surf, (x, row.y + 3))
                x += 12

            base_label = path.rsplit(".", 1)[-1]
            if self.element_inline_rename_path == path:
                left = self.element_inline_rename_text[: self.element_inline_rename_caret]
                right = self.element_inline_rename_text[self.element_inline_rename_caret :]
                label = f"{left}|{right}"
            else:
                label = base_label
                if locked:
                    label = f"{label} [locked]"
            text_color = (255, 188, 188) if locked and not is_selected else (230, 230, 230)
            txt = self.small_font.render(label, True, text_color)
            surface.blit(txt, (x, row.y + 3))
            y += 22

    def _draw_components_list(self, surface):
        rect = self._components_list_rect()
        pygame.draw.rect(surface, (15, 15, 15), rect)
        pygame.draw.rect(surface, (75, 75, 75), rect, 1)

        selected = self._selected_element()
        names = selected.component_order[:] if selected is not None else []
        visible_rows = max(1, rect.h // 22)
        self.component_scroll = max(0, min(self.component_scroll, max(0, len(names) - visible_rows)))
        start = self.component_scroll
        end = min(len(names), start + visible_rows)

        y = rect.y + 2
        for i in range(start, end):
            name = names[i]
            row = pygame.Rect(rect.x + 2, y, rect.w - 4, 20)
            is_selected = name == self.selected_component
            pygame.draw.rect(surface, (52, 72, 98) if is_selected else (22, 22, 22), row)
            txt = self.small_font.render(name, True, (230, 230, 230))
            surface.blit(txt, (row.x + 6, row.y + 3))
            y += 22

    def _draw_elements_tab(self, surface):
        self._draw_elements_list(surface)
        sb = self._sidebar_rect()

        parent_text = self.selected_path or "(select parent in tree)"
        lbl = self.small_font.render(f"create parent: {parent_text}", True, (190, 190, 190))
        surface.blit(lbl, (sb.x + 10, 360))
        self._draw_field(surface, pygame.Rect(sb.x + 10, 388, sb.w - 20, 42), "new_name", "new element name")
        self._draw_button(surface, pygame.Rect(sb.x + 10, 444, 130, 30), "create element")
        tpl_name = self._resolve_element_template_name().replace("_", " ")
        self._draw_button(surface, self._element_template_button_rect(), f"template: {tpl_name} v", active=self.element_template_dropdown_open)

        self._draw_field(surface, pygame.Rect(sb.x + 10, 486, sb.w - 20, 42), "reparent_parent", "reparent parent path")
        self._draw_field(surface, pygame.Rect(sb.x + 10, 534, sb.w - 20, 42), "reparent_name", "reparent name (optional)")
        self._draw_button(surface, pygame.Rect(sb.x + 10, 582, 130, 30), "reparent")
        self._draw_button(surface, pygame.Rect(sb.x + 150, 582, 130, 30), "delete subtree")

        if self.element_template_dropdown_open:
            opts = self._element_template_options()
            rect = self._element_template_dropdown_rect()
            pygame.draw.rect(surface, (14, 14, 14), rect)
            pygame.draw.rect(surface, (95, 95, 95), rect, 1)
            row_h = 22
            visible = max(1, (rect.h - 4) // row_h)
            self.element_template_scroll = max(0, min(self.element_template_scroll, max(0, len(opts) - visible)))
            start = self.element_template_scroll
            end = min(len(opts), start + visible)
            y = rect.y + 2
            mx, my = self.input.get_mouse_position(self.passcode)
            for i in range(start, end):
                row = pygame.Rect(rect.x + 2, y, rect.w - 4, 20)
                hover = row.collidepoint((mx, my))
                is_selected = opts[i] == self.selected_element_template
                color = (40, 54, 74) if (hover or is_selected) else (22, 22, 22)
                pygame.draw.rect(surface, color, row)
                txt = self.small_font.render(opts[i].replace("_", " "), True, (230, 230, 230))
                surface.blit(txt, (row.x + 6, row.y + 3))
                y += row_h

    def _draw_components_tab(self, surface):
        self._draw_components_list(surface)
        sb = self._sidebar_rect()
        if self.active_field == "add_component":
            self.active_field = None

        add_btn = self._component_add_button_rect()
        opts = self._component_add_options()
        self._draw_button(surface, add_btn, "add component v", active=self.component_add_dropdown_open)
        option_btn = self._component_option_button_rect()
        option_label = "add option v" if self.selected_component else "add option"
        self._draw_button(surface, option_btn, option_label, active=self.component_option_dropdown_open)
        self._draw_button(surface, pygame.Rect(sb.x + 370, 502, 90, 30), "remove")

        self._draw_component_tree(surface)

        selected_path_text = self.selected_component_path or "(none)"
        label = self.small_font.render(f"key: {selected_path_text}", True, (190, 190, 190))
        surface.blit(label, (sb.x + 10, 538))
        self._draw_field(surface, pygame.Rect(sb.x + 10, 560, sb.w - 20, 42), "component_value", "value (json)")
        self._draw_button(surface, pygame.Rect(sb.x + 10, 606, 100, 30), "set key")
        self._draw_button(surface, pygame.Rect(sb.x + 118, 606, 120, 30), "remove key")

        if self.component_add_dropdown_open:
            rect = self._component_add_dropdown_rect()
            pygame.draw.rect(surface, (14, 14, 14), rect)
            pygame.draw.rect(surface, (95, 95, 95), rect, 1)
            row_h = 22
            visible = max(1, (rect.h - 4) // row_h)
            self.component_add_dropdown_scroll = max(0, min(self.component_add_dropdown_scroll, max(0, len(opts) - visible)))
            start = self.component_add_dropdown_scroll
            end = min(len(opts), start + visible)
            y = rect.y + 2
            mx, my = self.input.get_mouse_position(self.passcode)
            for i in range(start, end):
                row = pygame.Rect(rect.x + 2, y, rect.w - 4, 20)
                hover = row.collidepoint((mx, my))
                pygame.draw.rect(surface, (40, 54, 74) if hover else (22, 22, 22), row)
                txt = self.small_font.render(opts[i], True, (230, 230, 230))
                surface.blit(txt, (row.x + 6, row.y + 3))
                y += row_h

        if self.component_option_dropdown_open:
            entries = self._component_option_entries()
            rect = self._component_option_dropdown_rect()
            pygame.draw.rect(surface, (14, 14, 14), rect)
            pygame.draw.rect(surface, (95, 95, 95), rect, 1)
            row_h = 22
            visible = max(1, (rect.h - 4) // row_h)
            self.component_option_dropdown_scroll = max(0, min(self.component_option_dropdown_scroll, max(0, len(entries) - visible)))
            start = self.component_option_dropdown_scroll
            end = min(len(entries), start + visible)
            y = rect.y + 2
            mx, my = self.input.get_mouse_position(self.passcode)
            for i in range(start, end):
                item = entries[i]
                row = pygame.Rect(rect.x + 2, y, rect.w - 4, 20)
                hover = row.collidepoint((mx, my))
                pygame.draw.rect(surface, (40, 54, 74) if hover else (22, 22, 22), row)
                txt = self.small_font.render(f"{item['key']}: {item['type']}", True, (230, 230, 230))
                surface.blit(txt, (row.x + 6, row.y + 3))
                y += row_h

    def _draw_component_tree(self, surface):
        rect = self._component_tree_rect()
        pygame.draw.rect(surface, (15, 15, 15), rect)
        pygame.draw.rect(surface, (75, 75, 75), rect, 1)

        rows = self._iter_component_rows()
        visible_rows = max(1, rect.h // 22)
        self.component_tree_scroll = max(0, min(self.component_tree_scroll, max(0, len(rows) - visible_rows)))
        start = self.component_tree_scroll
        end = min(len(rows), start + visible_rows)

        y = rect.y + 2
        for i in range(start, end):
            item = rows[i]
            path = item["path"]
            row = pygame.Rect(rect.x + 2, y, rect.w - 4, 20)
            is_selected = path == self.selected_component_path
            pygame.draw.rect(surface, (52, 72, 98) if is_selected else (22, 22, 22), row)

            x = row.x + 6 + item["depth"] * 14
            if item["is_branch"]:
                marker = ">" if item["collapsed"] else "v"
                marker_surf = self.small_font.render(marker, True, (190, 190, 190))
                surface.blit(marker_surf, (x, row.y + 3))
                x += 12

            if item["is_branch"]:
                label = item["label"]
            else:
                if self.component_inline_edit_path == path:
                    color_info = self._hex_color_info_from_field_text(self.component_inline_edit_text)
                else:
                    color_info = self._hex_color_info_from_field_text(json.dumps(item["value"], ensure_ascii=False))

                if self.component_inline_edit_path == path:
                    left = self.component_inline_edit_text[: self.component_inline_caret]
                    right = self.component_inline_edit_text[self.component_inline_caret :]
                    shown = f"{item['label']}: {left}|{right}"
                    if len(shown) > 58:
                        shown = shown[:55] + "..."
                    label = shown
                else:
                    value_text = json.dumps(item["value"], ensure_ascii=False)
                    if len(value_text) > 30:
                        value_text = value_text[:27] + "..."
                    label = f"{item['label']}: {value_text}"

                if color_info is not None:
                    sw = pygame.Rect(row.right - 20, row.y + 2, 16, 16)
                    pygame.draw.rect(surface, color_info["color"], sw)
                    pygame.draw.rect(surface, (220, 220, 220), sw, 1)
                    self._color_picker_buttons.append(
                        {
                            "rect": sw,
                            "target": {"type": "component_inline", "path": path},
                            "mode": color_info["mode"],
                            "color": color_info["color"],
                        }
                    )
            txt = self.small_font.render(label, True, (230, 230, 230))
            surface.blit(txt, (x, row.y + 3))
            y += 22

    def _draw_metadata_tab(self, surface):
        sb = self._sidebar_rect()
        self._draw_field(surface, pygame.Rect(sb.x + 10, 76, sb.w - 20, 42), "data_key", "data key path")
        self._draw_field(surface, pygame.Rect(sb.x + 10, 124, sb.w - 20, 42), "data_value", "data value (json)", allow_color_picker=True)
        self._draw_button(surface, pygame.Rect(sb.x + 10, 172, 90, 30), "set data")
        self._draw_button(surface, pygame.Rect(sb.x + 110, 172, 120, 30), "remove data")

        self._draw_field(surface, pygame.Rect(sb.x + 10, 220, 110, 42), "pos_x", "pos x")
        self._draw_field(surface, pygame.Rect(sb.x + 126, 220, 110, 42), "pos_y", "pos y")
        self._draw_field(surface, pygame.Rect(sb.x + 242, 220, 110, 42), "size_w", "size w")
        self._draw_field(surface, pygame.Rect(sb.x + 358, 220, 100, 42), "size_h", "size h")
        self._draw_button(surface, pygame.Rect(sb.x + 10, 268, 130, 30), "apply transform")

        self._draw_field(surface, pygame.Rect(sb.x + 10, 320, sb.w - 20, 62), "element_json", "selected element JSON")
        load_btn, apply_btn = self._metadata_element_buttons()
        self._draw_button(surface, load_btn, "load element")
        self._draw_button(surface, apply_btn, "apply element")

    def _draw_state_tab(self, surface):
        sb = self._sidebar_rect()
        self._draw_state_tree(surface)
        label = self.small_font.render(f"selected: {self.selected_state_path or '(none)'}", True, (190, 190, 190))
        surface.blit(label, (sb.x + 10, 374))
        self._draw_field(surface, pygame.Rect(sb.x + 10, 396, sb.w - 20, 42), "state_value", "GAME_STATE value (json)")
        self._draw_button(surface, pygame.Rect(sb.x + 10, 444, 90, 30), "set")
        self._draw_button(surface, pygame.Rect(sb.x + 110, 444, 90, 30), "get")

    def _draw_state_tree(self, surface):
        rect = self._state_list_rect()
        pygame.draw.rect(surface, (15, 15, 15), rect)
        pygame.draw.rect(surface, (75, 75, 75), rect, 1)

        rows = self._iter_state_rows()
        visible_rows = max(1, rect.h // 22)
        self.state_scroll = max(0, min(self.state_scroll, max(0, len(rows) - visible_rows)))
        start = self.state_scroll
        end = min(len(rows), start + visible_rows)

        y = rect.y + 2
        for i in range(start, end):
            item = rows[i]
            path = item["path"]
            row = pygame.Rect(rect.x + 2, y, rect.w - 4, 20)
            is_selected = path == self.selected_state_path
            name_locked = self._is_state_name_locked(path)
            value_locked = self._is_state_value_locked(path)
            row_locked = name_locked or value_locked
            if is_selected:
                color = (52, 72, 98)
            elif row_locked:
                color = (42, 26, 26)
            else:
                color = (22, 22, 22)
            pygame.draw.rect(surface, color, row)

            x = row.x + 6 + item["depth"] * 14
            if item["is_branch"]:
                marker = ">" if item["collapsed"] else "v"
                marker_surf = self.small_font.render(marker, True, (190, 190, 190))
                surface.blit(marker_surf, (x, row.y + 3))
                x += 12

            if item["is_branch"]:
                if self.state_inline_rename_path == path:
                    left = self.state_inline_rename_text[: self.state_inline_rename_caret]
                    right = self.state_inline_rename_text[self.state_inline_rename_caret :]
                    label = f"{left}|{right}"
                else:
                    label = item["label"] + (" [locked]" if name_locked else "")
            else:
                key_label = item["label"]
                if self.state_inline_rename_path == path:
                    left = self.state_inline_rename_text[: self.state_inline_rename_caret]
                    right = self.state_inline_rename_text[self.state_inline_rename_caret :]
                    key_label = f"{left}|{right}"

                if self.state_inline_edit_path == path:
                    color_info = self._hex_color_info_from_field_text(self.state_inline_edit_text)
                else:
                    color_info = self._hex_color_info_from_field_text(json.dumps(item["value"], ensure_ascii=False))

                if self.state_inline_edit_path == path:
                    left = self.state_inline_edit_text[: self.state_inline_caret]
                    right = self.state_inline_edit_text[self.state_inline_caret :]
                    shown = f"{key_label}: {left}|{right}"
                    if len(shown) > 58:
                        shown = shown[:55] + "..."
                    label = shown
                else:
                    value_text = json.dumps(item["value"], ensure_ascii=False)
                    if len(value_text) > 30:
                        value_text = value_text[:27] + "..."
                    lock_suffix = " [locked]" if value_locked else ""
                    label = f"{key_label}: {value_text}{lock_suffix}"

                if color_info is not None and not value_locked:
                    sw = pygame.Rect(row.right - 20, row.y + 2, 16, 16)
                    pygame.draw.rect(surface, color_info["color"], sw)
                    pygame.draw.rect(surface, (220, 220, 220), sw, 1)
                    self._color_picker_buttons.append(
                        {
                            "rect": sw,
                            "target": {"type": "state_inline", "path": path},
                            "mode": color_info["mode"],
                            "color": color_info["color"],
                        }
                    )
            text_color = (255, 188, 188) if row_locked and not is_selected else (230, 230, 230)
            txt = self.small_font.render(label, True, text_color)
            surface.blit(txt, (x, row.y + 3))
            y += 22

    def _update_sidebar_input(self):
        mx, my = self.input.get_mouse_position(self.passcode)
        _, wheel_y = self.input.get_mouse_wheel(self.passcode)

        if self.color_picker_open:
            return

        if self.active_field is not None and wheel_y != 0:
            active_rect = self.field_rect_cache.get(self.active_field)
            if active_rect is not None and active_rect.collidepoint((mx, my)):
                current = int(self.field_scroll.get(self.active_field, 0))
                self.field_scroll[self.active_field] = max(0, current - int(wheel_y))
                return

        if self.tab == "elements" and self._elements_list_rect().collidepoint((mx, my)) and wheel_y != 0:
            self.element_scroll = max(0, self.element_scroll - int(wheel_y))

        if self.tab == "elements" and self.element_template_dropdown_open:
            drop_rect = self._element_template_dropdown_rect()
            if drop_rect.collidepoint((mx, my)) and wheel_y != 0:
                opts = self._element_template_options()
                row_h = 22
                visible = max(1, (drop_rect.h - 4) // row_h)
                max_scroll = max(0, len(opts) - visible)
                self.element_template_scroll = max(0, min(max_scroll, self.element_template_scroll - int(wheel_y)))
                return

        if self.tab == "components" and self._components_list_rect().collidepoint((mx, my)) and wheel_y != 0:
            self.component_scroll = max(0, self.component_scroll - int(wheel_y))

        if self.tab == "components" and self._component_tree_rect().collidepoint((mx, my)) and wheel_y != 0:
            self.component_tree_scroll = max(0, self.component_tree_scroll - int(wheel_y))

        if self.tab == "components" and self.component_add_dropdown_open:
            drop_rect = self._component_add_dropdown_rect()
            if drop_rect.collidepoint((mx, my)) and wheel_y != 0:
                opts = self._component_add_options()
                row_h = 22
                visible = max(1, (drop_rect.h - 4) // row_h)
                max_scroll = max(0, len(opts) - visible)
                self.component_add_dropdown_scroll = max(0, min(max_scroll, self.component_add_dropdown_scroll - int(wheel_y)))
                return

        if self.tab == "components" and self.component_option_dropdown_open:
            drop_rect = self._component_option_dropdown_rect()
            if drop_rect.collidepoint((mx, my)) and wheel_y != 0:
                opts = self._component_option_entries()
                row_h = 22
                visible = max(1, (drop_rect.h - 4) // row_h)
                max_scroll = max(0, len(opts) - visible)
                self.component_option_dropdown_scroll = max(0, min(max_scroll, self.component_option_dropdown_scroll - int(wheel_y)))
                return

        if self.tab == "state" and self._state_list_rect().collidepoint((mx, my)) and wheel_y != 0:
            self.state_scroll = max(0, self.state_scroll - int(wheel_y))

        if not self.input.get_mouse_button_down(1, self.passcode):
            return
        if not self._is_in_sidebar(mx, my):
            return

        for item in reversed(self._color_picker_buttons):
            if item["rect"].collidepoint((mx, my)):
                self._open_color_picker(item["target"], item["mode"], item["color"])
                return

        if self.active_field is not None:
            active_rect = self.field_rect_cache.get(self.active_field)
            if active_rect is not None and active_rect.collidepoint((mx, my)):
                self._set_caret_from_click(self.active_field, mx, my)
                self._clear_selection(self.active_field, self.field_caret.get(self.active_field, 0))

                caret = int(self.field_caret.get(self.active_field, 0))
                now = pygame.time.get_ticks()
                is_double = (
                    self.field_last_click_key == self.active_field
                    and (now - self.field_last_click_ms) <= 350
                    and abs(caret - int(self.field_last_click_caret)) <= 2
                )
                self.field_last_click_key = self.active_field
                self.field_last_click_ms = now
                self.field_last_click_caret = caret

                if is_double:
                    token = self._hex_token_info_at_index(self.active_field, caret)
                    if token is not None:
                        self._open_color_picker(
                            {
                                "type": "field_token",
                                "key": self.active_field,
                                "start": token["start"],
                                "end": token["end"],
                            },
                            token["mode"],
                            token["color"],
                        )
                        return

                if self.numeric_drag_field is None:
                    self.field_mouse_select_key = self.active_field
                    self.field_mouse_select_anchor = int(self.field_caret.get(self.active_field, 0))
                return

        self.dragging = False
        self.resizing = False

        if self._sidebar_move_button_rect().collidepoint((mx, my)):
            if self.element_inline_rename_path is not None:
                self._stop_element_inline_rename(True)
            if self.component_inline_edit_path is not None:
                self._stop_component_inline_edit(True)
            if self.state_inline_edit_path is not None:
                self._stop_state_inline_edit(True)
            if self.state_inline_rename_path is not None:
                self._stop_state_inline_rename(True)
            self.sidebar_side = "left" if self.sidebar_side == "right" else "right"
            return

        for i, tab_name in enumerate(self.tabs):
            if self._tab_button_rect(i).collidepoint((mx, my)):
                if self.element_inline_rename_path is not None:
                    self._stop_element_inline_rename(True)
                if self.component_inline_edit_path is not None:
                    self._stop_component_inline_edit(True)
                if self.state_inline_edit_path is not None:
                    self._stop_state_inline_edit(True)
                if self.state_inline_rename_path is not None:
                    self._stop_state_inline_rename(True)
                self.tab = tab_name
                self.active_field = None
                self.numeric_drag_field = None
                self.element_template_dropdown_open = False
                self.component_add_dropdown_open = False
                self.component_option_dropdown_open = False
                return

        if self.tab == "elements":
            self._click_elements_tab(mx, my)
        elif self.tab == "components":
            self._click_components_tab(mx, my)
        elif self.tab == "metadata":
            self._click_metadata_tab(mx, my)
        elif self.tab == "state":
            self._click_state_tab(mx, my)

    def _click_elements_tab(self, mx, my):
        tpl_btn = self._element_template_button_rect()
        if tpl_btn.collidepoint((mx, my)):
            self.element_template_dropdown_open = not self.element_template_dropdown_open
            return

        if self.element_template_dropdown_open:
            drop = self._element_template_dropdown_rect()
            opts = self._element_template_options()
            if drop.collidepoint((mx, my)):
                row_h = 22
                rel = my - (drop.y + 2)
                idx = self.element_template_scroll + int(rel // row_h)
                if 0 <= idx < len(opts):
                    self.selected_element_template = opts[idx]
                    self._set_message(f"Template: {opts[idx]}")
                self.element_template_dropdown_open = False
                return
            self.element_template_dropdown_open = False

        list_rect = self._elements_list_rect()
        if list_rect.collidepoint((mx, my)):
            rel = my - (list_rect.y + 2)
            row = rel // 22
            idx = self.element_scroll + int(row)
            rows = self._visible_element_rows()
            if 0 <= idx < len(rows):
                item = rows[idx]
                path = item["path"]
                depth_x = list_rect.x + 2 + 6 + item["depth"] * 14
                marker_rect = pygame.Rect(depth_x, list_rect.y + 2 + int(row) * 22, 12, 20)

                if item["has_children"] and marker_rect.collidepoint((mx, my)):
                    if path in self.collapsed_element_nodes:
                        self.collapsed_element_nodes.remove(path)
                    else:
                        self.collapsed_element_nodes.add(path)
                    return

                if self.element_inline_rename_path is not None and self.element_inline_rename_path != path:
                    self._stop_element_inline_rename(True)

                self.selected_path = path
                self.selected_component = None
                self._sync_transform_fields()
                self._load_selected_element_json()

                now = pygame.time.get_ticks()
                is_double = (
                    self.element_last_click_path == path
                    and (now - self.element_last_click_ms) <= 350
                )
                self.element_last_click_path = path
                self.element_last_click_ms = now
                if is_double:
                    self._start_element_inline_rename(path)
            return

        sb = self._sidebar_rect()
        field_rects = {
            "new_name": pygame.Rect(sb.x + 10, 388, sb.w - 20, 42),
            "reparent_parent": pygame.Rect(sb.x + 10, 486, sb.w - 20, 42),
            "reparent_name": pygame.Rect(sb.x + 10, 534, sb.w - 20, 42),
        }
        for key, rect in field_rects.items():
            if rect.collidepoint((mx, my)):
                if self.element_inline_rename_path is not None:
                    self._stop_element_inline_rename(True)
                self._focus_field_from_click(key, mx, my, allow_numeric_drag=False)
                return

        create_btn = pygame.Rect(sb.x + 10, 444, 130, 30)
        reparent_btn = pygame.Rect(sb.x + 10, 582, 130, 30)
        delete_btn = pygame.Rect(sb.x + 150, 582, 130, 30)

        if create_btn.collidepoint((mx, my)):
            parent = self.selected_path
            name = self.fields["new_name"].strip()
            if not parent:
                self._set_message("Select parent element first")
                return
            if not name:
                self._set_message("Element name is required")
                return
            if self.manager.getElement(parent) is None:
                self._set_message("Parent does not exist")
                return
            path = f"{parent}.{name}"
            template_name = self._resolve_element_template_name()
            bundle = self._build_element_template_bundle(template_name, path)
            paths = sorted(bundle.keys(), key=lambda p: (p.count("."), p))

            for p in paths:
                if self.manager.getElement(p) is not None:
                    self._set_message(f"Path already exists: {p}")
                    return

            created_count = 0
            for p in paths:
                created = self.manager.create_element(p, bundle.get(p))
                if created is not None:
                    created_count += 1

            if created_count == 0:
                self._set_message("Could not create element")
                return

            self.selected_path = path
            self._sync_transform_fields()
            self._load_selected_element_json()
            self._set_message(f"Created {created_count} element(s) from {template_name}")
            return

        if reparent_btn.collidepoint((mx, my)):
            selected = self._selected_element()
            if selected is None:
                self._set_message("No selected element")
                return
            if self._is_locked_element(selected):
                self._set_message("Selected element is locked")
                return
            parent = self.fields["reparent_parent"].strip()
            name = self.fields["reparent_name"].strip() or None
            ok, msg, new_path = self.manager.reparent_element(selected.path, parent, name)
            if ok:
                self.selected_path = new_path
            self._set_message(msg)
            return

        if delete_btn.collidepoint((mx, my)):
            selected = self._selected_element()
            if selected is None:
                self._set_message("No selected element")
                return
            if self._is_locked_element(selected):
                self._set_message("Selected element is locked")
                return
            removed = self.manager.remove_element_tree(selected.path)
            self.selected_path = None
            self.selected_component = None
            self._set_message(f"Removed {removed} element(s)")

    def _click_components_tab(self, mx, my):
        selected = self._selected_element()
        if selected is None:
            self._set_message("No selected element")
            return

        add_btn = self._component_add_button_rect()
        opts = self._component_add_options()
        if add_btn.collidepoint((mx, my)):
            self.component_add_dropdown_open = not self.component_add_dropdown_open
            if self.component_add_dropdown_open:
                self.component_option_dropdown_open = False
            return

        option_btn = self._component_option_button_rect()
        if option_btn.collidepoint((mx, my)):
            if not self.selected_component:
                self._set_message("Select a component first")
                self.component_option_dropdown_open = False
                return
            self.component_option_dropdown_open = not self.component_option_dropdown_open
            if self.component_option_dropdown_open:
                self.component_add_dropdown_open = False
            return

        if self.component_add_dropdown_open:
            drop = self._component_add_dropdown_rect()
            if drop.collidepoint((mx, my)):
                row_h = 22
                rel = my - (drop.y + 2)
                idx = self.component_add_dropdown_scroll + int(rel // row_h)
                if 0 <= idx < len(opts):
                    if self._is_locked_element(selected):
                        self._set_message("Selected element is locked")
                        self.component_add_dropdown_open = False
                        return
                    base_name = opts[idx]
                    name = self._next_component_instance_name(selected, base_name)
                    if not name:
                        self._set_message("Invalid component")
                        self.component_add_dropdown_open = False
                        return
                    selected.addComponent(name, self.manager.data, {})
                    selected.elmData[name] = {}
                    self.selected_component = name
                    self.selected_component_path = ""
                    self.fields["component_value"] = ""
                    self.component_add_dropdown_open = False
                    self._set_message(f"Added {name}")
                return
            self.component_add_dropdown_open = False

        if self.component_option_dropdown_open:
            drop = self._component_option_dropdown_rect()
            entries = self._component_option_entries()
            if drop.collidepoint((mx, my)):
                row_h = 22
                rel = my - (drop.y + 2)
                idx = self.component_option_dropdown_scroll + int(rel // row_h)
                if 0 <= idx < len(entries):
                    if self._is_locked_element(selected):
                        self._set_message("Selected element is locked")
                        self.component_option_dropdown_open = False
                        return

                    comp = selected.getComponent(self.selected_component)
                    if comp is None or not isinstance(comp.config, dict):
                        self._set_message("Missing component")
                        self.component_option_dropdown_open = False
                        return

                    entry = entries[idx]
                    key = str(entry.get("key", "")).strip()
                    allow_multiple = bool(entry.get("allow_multiple", False))
                    if not key:
                        self.component_option_dropdown_open = False
                        return

                    if allow_multiple:
                        key = self._unique_dict_key(comp.config, key)
                    elif key in comp.config:
                        self._set_message(f"{key} already exists")
                        self.component_option_dropdown_open = False
                        return

                    comp.config[key] = json.loads(json.dumps(entry.get("default")))
                    selected.elmData[self.selected_component] = json.loads(json.dumps(comp.config))
                    self.selected_component_path = key
                    self.fields["component_value"] = json.dumps(comp.config.get(key), indent=2)
                    self._set_message(f"Added option {key}")
                    self.component_option_dropdown_open = False
                return
            self.component_option_dropdown_open = False

        list_rect = self._components_list_rect()
        if list_rect.collidepoint((mx, my)):
            rel = my - (list_rect.y + 2)
            row = rel // 22
            idx = self.component_scroll + int(row)
            names = selected.component_order[:]
            if 0 <= idx < len(names):
                if self.component_inline_edit_path is not None:
                    self._stop_component_inline_edit(True)
                self.selected_component = names[idx]
                self.selected_component_path = ""
            return

        tree_rect = self._component_tree_rect()
        if tree_rect.collidepoint((mx, my)):
            rel = my - (tree_rect.y + 2)
            row = rel // 22
            idx = self.component_tree_scroll + int(row)
            rows = self._iter_component_rows()
            if 0 <= idx < len(rows):
                item = rows[idx]
                marker_x = tree_rect.x + 2 + 6 + item["depth"] * 14
                marker_rect = pygame.Rect(marker_x, tree_rect.y + 2 + int(row) * 22, 12, 20)
                if item["is_branch"] and marker_rect.collidepoint((mx, my)):
                    path = item["path"]
                    if path in self.collapsed_component_nodes:
                        self.collapsed_component_nodes.remove(path)
                    else:
                        self.collapsed_component_nodes.add(path)
                    return

                if self.component_inline_edit_path is not None and self.component_inline_edit_path != item["path"]:
                    self._stop_component_inline_edit(True)

                self.selected_component_path = item["path"]
                value = self._component_path_value()
                self.fields["component_value"] = json.dumps(value, indent=2)

                now = pygame.time.get_ticks()
                is_double = (
                    self.component_last_click_path == item["path"]
                    and (now - self.component_last_click_ms) <= 350
                )
                self.component_last_click_path = item["path"]
                self.component_last_click_ms = now

                if is_double and not item["is_branch"]:
                    self._start_component_inline_edit(item["path"])
            return

        sb = self._sidebar_rect()
        field_rects = {
            "component_value": pygame.Rect(sb.x + 10, 560, sb.w - 20, 42),
        }
        for key, rect in field_rects.items():
            if rect.collidepoint((mx, my)):
                if self.component_inline_edit_path is not None:
                    self._stop_component_inline_edit(True)
                self._focus_field_from_click(key, mx, my, allow_numeric_drag=False)
                return

        rm_btn = pygame.Rect(sb.x + 370, 502, 90, 30)
        set_btn = pygame.Rect(sb.x + 10, 606, 100, 30)
        remove_key_btn = pygame.Rect(sb.x + 118, 606, 120, 30)

        if rm_btn.collidepoint((mx, my)):
            if self._is_locked_element(selected):
                self._set_message("Selected element is locked")
                return
            if not self.selected_component:
                self._set_message("No selected component")
                return
            if self.selected_component == "container" and self._is_locked_element(selected):
                self._set_message("Screen container cannot be removed")
                return
            selected.removeComponent(self.selected_component)
            selected.elmData.pop(self.selected_component, None)
            self._set_message(f"Removed {self.selected_component}")
            self.selected_component = None
            self.selected_component_path = ""
            self.fields["component_value"] = ""
            return

        if set_btn.collidepoint((mx, my)):
            if self._is_locked_element(selected):
                self._set_message("Selected element is locked")
                return
            if not self.selected_component:
                self._set_message("No selected component")
                return
            if not self.selected_component_path:
                self._set_message("No selected key path")
                return
            parsed = self._parse_value(self.fields["component_value"])
            comp = selected.getComponent(self.selected_component)
            if comp is None or not isinstance(comp.config, dict):
                self._set_message("Missing component")
                return
            PathDict.set(comp.config, self.selected_component_path, parsed)
            selected.elmData[self.selected_component] = json.loads(json.dumps(comp.config))
            self._set_message("Component value applied")
            return

        if remove_key_btn.collidepoint((mx, my)):
            if self._is_locked_element(selected):
                self._set_message("Selected element is locked")
                return
            if not self.selected_component:
                self._set_message("No selected component")
                return
            if not self.selected_component_path:
                self._set_message("No selected key path")
                return
            comp = selected.getComponent(self.selected_component)
            if comp is None or not isinstance(comp.config, dict):
                self._set_message("Missing component")
                return
            if not self._remove_component_path(comp.config, self.selected_component_path):
                self._set_message("Could not remove key")
                return
            selected.elmData[self.selected_component] = json.loads(json.dumps(comp.config))
            self.selected_component_path = ""
            self.fields["component_value"] = ""
            self._set_message("Component key removed")

    def _click_metadata_tab(self, mx, my):
        selected = self._selected_element()
        if selected is None:
            self._set_message("No selected element")
            return

        sb = self._sidebar_rect()
        field_rects = {
            "data_key": pygame.Rect(sb.x + 10, 76, sb.w - 20, 42),
            "data_value": pygame.Rect(sb.x + 10, 124, sb.w - 20, 42),
            "pos_x": pygame.Rect(sb.x + 10, 220, 110, 42),
            "pos_y": pygame.Rect(sb.x + 126, 220, 110, 42),
            "size_w": pygame.Rect(sb.x + 242, 220, 110, 42),
            "size_h": pygame.Rect(sb.x + 358, 220, 100, 42),
            "element_json": pygame.Rect(sb.x + 10, 320, sb.w - 20, 62),
        }
        for key, rect in field_rects.items():
            if rect.collidepoint((mx, my)):
                self._focus_field_from_click(key, mx, my, allow_numeric_drag=True)
                return

        set_btn = pygame.Rect(sb.x + 10, 172, 90, 30)
        rm_btn = pygame.Rect(sb.x + 110, 172, 120, 30)
        transform_btn = pygame.Rect(sb.x + 10, 268, 130, 30)
        load_btn, apply_btn = self._metadata_element_buttons(expanded=False)
        load_btn_expanded, apply_btn_expanded = self._metadata_element_buttons(expanded=True)

        if set_btn.collidepoint((mx, my)):
            if self._is_locked_element(selected):
                self._set_message("Selected element is locked")
                return
            key = self.fields["data_key"].strip()
            if not key:
                self._set_message("Data key required")
                return
            value = self._parse_value(self.fields["data_value"])
            selected.set_data(key, value)
            self._set_message("Data set")
            return

        if rm_btn.collidepoint((mx, my)):
            if self._is_locked_element(selected):
                self._set_message("Selected element is locked")
                return
            key = self.fields["data_key"].strip()
            if not key:
                self._set_message("Data key required")
                return
            parts = key.split(".")
            node = selected.local_data
            for p in parts[:-1]:
                if not isinstance(node, dict) or p not in node:
                    self._set_message("Data key not found")
                    return
                node = node[p]
            if isinstance(node, dict):
                node.pop(parts[-1], None)
                self._set_message("Data removed")
            return

        if transform_btn.collidepoint((mx, my)):
            if self._apply_transform_from_fields(silent=False):
                self._set_message("Transform applied")
            return

        if load_btn.collidepoint((mx, my)) or load_btn_expanded.collidepoint((mx, my)):
            self._load_selected_element_json()
            self._set_message("Loaded element JSON")
            return

        if apply_btn.collidepoint((mx, my)) or apply_btn_expanded.collidepoint((mx, my)):
            parsed = self._parse_value(self.fields["element_json"])
            self._apply_selected_element_json(parsed, silent=False, preserve_component_selection=False)

    def _click_state_tab(self, mx, my):
        sb = self._sidebar_rect()

        tree_rect = self._state_list_rect()
        if tree_rect.collidepoint((mx, my)):
            rel = my - (tree_rect.y + 2)
            row = rel // 22
            idx = self.state_scroll + int(row)
            rows = self._iter_state_rows()
            if 0 <= idx < len(rows):
                item = rows[idx]
                marker_x = tree_rect.x + 2 + 6 + item["depth"] * 14
                marker_rect = pygame.Rect(marker_x, tree_rect.y + 2 + int(row) * 22, 12, 20)
                if item["is_branch"] and marker_rect.collidepoint((mx, my)):
                    path = item["path"]
                    if path in self.collapsed_state_nodes:
                        self.collapsed_state_nodes.remove(path)
                    else:
                        self.collapsed_state_nodes.add(path)
                    return

                if self.state_inline_edit_path is not None and self.state_inline_edit_path != item["path"]:
                    self._stop_state_inline_edit(True)
                if self.state_inline_rename_path is not None and self.state_inline_rename_path != item["path"]:
                    self._stop_state_inline_rename(True)

                self.selected_state_path = item["path"]
                self._load_selected_state_value()

                now = pygame.time.get_ticks()
                is_double = (
                    self.state_last_click_path == item["path"]
                    and (now - self.state_last_click_ms) <= 350
                )
                self.state_last_click_path = item["path"]
                self.state_last_click_ms = now

                if is_double:
                    if item["is_branch"]:
                        self._start_state_inline_rename(item["path"])
                    else:
                        row_x = tree_rect.x + 2
                        marker_w = 12 if item["is_branch"] else 0
                        text_x = row_x + 6 + item["depth"] * 14 + marker_w
                        key_width = self.small_font.size(item["label"])[0]
                        value_click = mx > (text_x + key_width + 10)
                        if value_click:
                            self._start_state_inline_edit(item["path"])
                        else:
                            self._start_state_inline_rename(item["path"])
            return

        field_rects = {
            "state_value": pygame.Rect(sb.x + 10, 396, sb.w - 20, 42),
        }
        for key, rect in field_rects.items():
            if rect.collidepoint((mx, my)):
                if self.state_inline_edit_path is not None:
                    self._stop_state_inline_edit(True)
                if self.state_inline_rename_path is not None:
                    self._stop_state_inline_rename(True)
                self._focus_field_from_click(key, mx, my, allow_numeric_drag=False)
                return

        set_btn = pygame.Rect(sb.x + 10, 444, 90, 30)
        get_btn = pygame.Rect(sb.x + 110, 444, 90, 30)

        if self.manager.GAME_STATE is None:
            self._set_message("No GAME_STATE available")
            return

        if set_btn.collidepoint((mx, my)):
            if self.state_inline_edit_path is not None:
                self._stop_state_inline_edit(True)
            if self.state_inline_rename_path is not None:
                self._stop_state_inline_rename(True)
            key = self.selected_state_path.strip()
            if not key:
                self._set_message("State key required")
                return
            if self._is_state_value_locked(key):
                self._set_message("This value is locked")
                return
            value = self._parse_value(self.fields["state_value"])
            self.manager.GAME_STATE.set(key, value)
            self._set_message("GAME_STATE updated")
            return

        if get_btn.collidepoint((mx, my)):
            if self.state_inline_edit_path is not None:
                self._stop_state_inline_edit(True)
            if self.state_inline_rename_path is not None:
                self._stop_state_inline_rename(True)
            key = self.selected_state_path.strip()
            if not key:
                self._set_message("State key required")
                return
            value = self.manager.GAME_STATE.get(key)
            self.fields["state_value"] = json.dumps(value, indent=2)
            self._set_message("GAME_STATE value loaded")