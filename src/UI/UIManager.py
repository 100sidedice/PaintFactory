from src.UI.ui_element import UIelement
from src.UI.ui_editor import UIEditor
from src.utils.path_dict import PathDict
import json
import os
import copy
import pygame

class UIManager:
    def __init__(self, data, input, surface, GAME_STATE=None, game=None):
        self.data = data
        self.input = input
        self.ui_elements = {}
        self.surface = surface
        self.GAME_STATE = GAME_STATE
        self.game = game
        self.editor = UIEditor(self, input)
        self._raw_ui_data = {}
        self._editor_array_meta = {}
        self._editor_array_sources = {}

    def loadUIElements(self):
        """Load UI elements from data and create UIelement instances."""
        raw_ui_data = self.data.get("uiElements", {})
        self._raw_ui_data = copy.deepcopy(raw_ui_data)
        self._editor_array_meta = {}
        self._editor_array_sources = {}
        ui_data = self._preprocess_ui_data(raw_ui_data)
        for path in sorted(ui_data.keys(), key=lambda p: (p.count("."), p)):
            element_data = ui_data[path]
            self.addElement(path, element_data)

    def _deep_merge_missing(self, base, override):
        """Merge where `override` only replaces fields it explicitly defines.

        Nested dictionaries are merged recursively.
        """
        if not isinstance(base, dict) or not isinstance(override, dict):
            return copy.deepcopy(override)

        merged = copy.deepcopy(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge_missing(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged

    def _resolve_copies(self, raw_ui_data):
        """Resolve `copy` inheritance in UI element definitions."""
        resolved = {}
        resolving = set()

        def resolve(path):
            if path in resolved:
                return resolved[path]
            if path in resolving:
                raise ValueError(f"Circular UI copy detected at: {path}")
            if path not in raw_ui_data:
                raise KeyError(f"UI copy source not found: {path}")

            resolving.add(path)
            current = copy.deepcopy(raw_ui_data[path])
            copy_source = current.pop("copy", None)

            if copy_source is not None:
                base_data = resolve(copy_source)
                current = self._deep_merge_missing(base_data, current)

            resolving.remove(path)
            resolved[path] = current
            return current

        for path in raw_ui_data.keys():
            resolve(path)

        return resolved

    def _apply_template(self, text, context):
        if not isinstance(text, str):
            return text
        out = text
        for key, value in context.items():
            out = out.replace(f"${{{key}}}", str(value))
        return out

    def _template_obj(self, obj, context):
        if isinstance(obj, str):
            return self._apply_template(obj, context)
        if isinstance(obj, list):
            return [self._template_obj(item, context) for item in obj]
        if isinstance(obj, dict):
            new_obj = {}
            for key, value in obj.items():
                new_key = self._apply_template(key, context) if isinstance(key, str) else key
                new_obj[new_key] = self._template_obj(value, context)
            return new_obj
        return obj

    def _derive_self_array_leaf_template(self, path, count_x, count_y):
        leaf = path.rsplit(".", 1)[-1] if "." in path else path
        if count_x <= 1:
            i = len(leaf)
            while i > 0 and leaf[i - 1].isdigit():
                i -= 1
            if i < len(leaf):
                return f"{leaf[:i]}${{index2}}"
            return f"{leaf}${{index2}}"
        return f"{leaf}_${{index}}_${{index2}}"

    def _expand_array_legacy(self, path, element_data, arr):
        """Legacy mode: `path` acts as a template root and generated items live below it."""
        base = copy.deepcopy(element_data)
        base.pop("array", None)

        count_x = max(1, int(arr.get("x", arr.get("count", 1)) or 1))
        count_y = max(1, int(arr.get("y", 1) or 1))
        gap = arr.get("gap", [0, 0])
        start = arr.get("start", [0, 0])

        gap_x = float(gap[0]) if isinstance(gap, (list, tuple)) and len(gap) > 0 else 0.0
        gap_y = float(gap[1]) if isinstance(gap, (list, tuple)) and len(gap) > 1 else gap_x
        start_x = float(start[0]) if isinstance(start, (list, tuple)) and len(start) > 0 else 0.0
        start_y = float(start[1]) if isinstance(start, (list, tuple)) and len(start) > 1 else 0.0

        default_path_template = "${index}" if count_y == 1 else "${index}.${index2}"
        path_template = arr.get("path", default_path_template)

        expanded = {}
        for ix in range(count_x):
            for iy in range(count_y):
                context = {"index": ix, "index2": iy}
                instance = self._template_obj(base, context)

                container = instance.get("container")
                if isinstance(container, dict):
                    pos = container.get("pos", [0, 0])
                    if not isinstance(pos, list):
                        pos = [0, 0]
                    px = float(pos[0]) if len(pos) > 0 else 0.0
                    py = float(pos[1]) if len(pos) > 1 else 0.0
                    container["pos"] = [px + start_x + ix * gap_x, py + start_y + iy * gap_y]

                suffix = self._apply_template(path_template, context)
                new_path = f"{path}.{suffix}" if suffix else path
                expanded[new_path] = instance
                self._editor_array_meta[new_path] = {
                    "templatePath": path,
                    "sourcePath": path,
                    "indexX": ix,
                    "indexY": iy,
                    "locked": not (ix == 0 and iy == 0),
                    "mode": "template",
                }

        return expanded

    def _expand_array_self(self, path, element_data, arr):
        """Self mode: the current element remains concrete, and array adds siblings."""
        count_x = max(1, int(arr.get("x", arr.get("count", 1)) or 1))
        count_y = max(1, int(arr.get("y", 1) or 1))
        gap = arr.get("gap", [0, 0])
        start = arr.get("start", [0, 0])

        gap_x = float(gap[0]) if isinstance(gap, (list, tuple)) and len(gap) > 0 else 0.0
        gap_y = float(gap[1]) if isinstance(gap, (list, tuple)) and len(gap) > 1 else gap_x
        start_x = float(start[0]) if isinstance(start, (list, tuple)) and len(start) > 0 else 0.0
        start_y = float(start[1]) if isinstance(start, (list, tuple)) and len(start) > 1 else 0.0

        leaf_template = arr.get("path")
        if not isinstance(leaf_template, str) or not leaf_template:
            leaf_template = self._derive_self_array_leaf_template(path, count_x, count_y)

        parent_path = path.rsplit(".", 1)[0] if "." in path else ""
        self._editor_array_sources[path] = copy.deepcopy(element_data)

        base_without_array = copy.deepcopy(element_data)
        base_without_array.pop("array", None)

        base_context = {"index": 0, "index2": 0}
        base_instance = self._template_obj(base_without_array, base_context)
        base_container = base_instance.get("container")
        if isinstance(base_container, dict):
            pos = base_container.get("pos", [0, 0])
            if not isinstance(pos, list):
                pos = [0, 0]
            px = float(pos[0]) if len(pos) > 0 else 0.0
            py = float(pos[1]) if len(pos) > 1 else 0.0
            base_container["pos"] = [px + start_x, py + start_y]
        base_instance["array"] = copy.deepcopy(arr)

        expanded = {path: base_instance}
        self._editor_array_meta[path] = {
            "templatePath": path,
            "sourcePath": path,
            "indexX": 0,
            "indexY": 0,
            "locked": False,
            "mode": "self",
        }

        for ix in range(count_x):
            for iy in range(count_y):
                if ix == 0 and iy == 0:
                    continue

                context = {"index": ix, "index2": iy}
                instance = self._template_obj(base_without_array, context)

                container = instance.get("container")
                if isinstance(container, dict):
                    pos = container.get("pos", [0, 0])
                    if not isinstance(pos, list):
                        pos = [0, 0]
                    px = float(pos[0]) if len(pos) > 0 else 0.0
                    py = float(pos[1]) if len(pos) > 1 else 0.0
                    container["pos"] = [px + start_x + ix * gap_x, py + start_y + iy * gap_y]

                leaf = self._apply_template(leaf_template, context)
                new_path = f"{parent_path}.{leaf}" if parent_path else leaf
                if new_path == path or new_path in expanded:
                    continue

                expanded[new_path] = instance
                self._editor_array_meta[new_path] = {
                    "templatePath": path,
                    "sourcePath": path,
                    "indexX": ix,
                    "indexY": iy,
                    "locked": True,
                    "mode": "self",
                }

        return expanded

    def _expand_array(self, path, element_data):
        """Expand array definitions.

        Default mode is `self`: keep the source element path and add generated siblings.
        Legacy template behavior is available with `array.mode = "template"`.
        """
        arr = element_data.get("array")
        if not isinstance(arr, dict):
            return {path: element_data}

        mode = str(arr.get("mode", "self")).strip().lower()
        if mode == "template":
            return self._expand_array_legacy(path, element_data, arr)
        return self._expand_array_self(path, element_data, arr)

    def _preprocess_ui_data(self, raw_ui_data):
        """Resolve copy inheritance and array expansion."""
        copied = self._resolve_copies(raw_ui_data)
        final = {}
        for path, element_data in copied.items():
            expanded = self._expand_array(path, element_data)
            final.update(expanded)
        return final
            
    def flattenElements(self):
        """Return UI elements ordered by depth and subtree depth.

        Primary key: element path depth (parent -> child).
        Secondary key: max descendant depth under that element.
        This lets update traversal prefer branches with deeper interactive children.
        """
        elements = [elm for elm in self.ui_elements.values() if elm is not None]

        max_depth_cache = {}

        def subtree_max_depth(path):
            if path in max_depth_cache:
                return max_depth_cache[path]
            base = path.count(".")
            prefix = f"{path}."
            best = base
            for other_path in self.ui_elements.keys():
                if other_path == path or other_path.startswith(prefix):
                    best = max(best, other_path.count("."))
            max_depth_cache[path] = best
            return best

        return sorted(elements, key=lambda elm: (elm.path.count("."), subtree_max_depth(elm.path), elm.path))
    
    def update(self, delta):
        editor_passcode = self.editor.passcode if self.editor.enabled else None
        ctrl_down = self.input.get_key(pygame.K_LCTRL, editor_passcode) or self.input.get_key(pygame.K_RCTRL, editor_passcode)

        if ctrl_down and self.input.get_key_down(pygame.K_e, editor_passcode):
            self.editor.toggle()

        if self.editor.enabled:
            self.editor.update(delta)

        # Update children first, then parents (reverse depth order).
        for element in reversed(self.flattenElements()):
            if hasattr(element, "update"):
                element.update(delta)

    def draw(self):
        # Draw parents first, then children so children layer above.
        for element in self.flattenElements():
            if hasattr(element, "draw"):
                element.draw(self.surface)

        if self.editor.enabled:
            self.editor.draw(self.surface)

    def serialize_ui_elements(self):
        serialized = {}
        for element in self.flattenElements():
            payload = {}
            for key, value in element.elmData.items():
                if key in {"data"}:
                    continue
                if key in element.components:
                    continue
                payload[key] = copy.deepcopy(value)

            if element.local_data:
                payload["data"] = copy.deepcopy(element.local_data)

            for component_name in element.component_order:
                component = element.components.get(component_name)
                if component is None:
                    continue
                payload[component_name] = copy.deepcopy(component.config)

            serialized[element.path] = payload
        return serialized

    def available_component_names(self):
        components = self.data.get("uiComponents", {})
        names = []
        for module_name in components.keys():
            if module_name.endswith("Component") and len(module_name) > len("Component"):
                names.append(module_name[:-9])
        return sorted(set(names))

    def get_array_meta(self, path):
        return self._editor_array_meta.get(path)

    def get_array_source_path(self, path):
        meta = self.get_array_meta(path)
        if not meta:
            return None
        return meta.get("sourcePath")

    def is_array_source(self, path):
        source = self.get_array_source_path(path)
        return bool(source and source == path)

    def get_array_source_raw(self, path):
        source_path = path if self.is_array_source(path) else self.get_array_source_path(path)
        if not source_path:
            return None
        raw = self._editor_array_sources.get(source_path)
        if raw is None:
            return None
        return copy.deepcopy(raw)

    def is_array_locked(self, path):
        meta = self.get_array_meta(path)
        return bool(meta and meta.get("locked"))

    def _replace_element_instance(self, path, element_data):
        self.ui_elements[path] = UIelement(path, element_data, self.data, self, self.input)

    def regenerate_array_source(self, source_path, source_payload):
        if not source_path:
            return False, "Invalid source path"
        if not isinstance(source_payload, dict):
            return False, "Invalid source payload"

        arr = source_payload.get("array")
        if not isinstance(arr, dict):
            return False, "Source payload has no array"

        existing_group = [
            p for p, meta in self._editor_array_meta.items()
            if isinstance(meta, dict) and meta.get("sourcePath") == source_path
        ]

        for p in existing_group:
            if p != source_path:
                self.ui_elements.pop(p, None)
                self._editor_array_meta.pop(p, None)

        mode = str(arr.get("mode", "self")).strip().lower()
        if mode == "template":
            expanded = self._expand_array_legacy(source_path, source_payload, arr)
        else:
            expanded = self._expand_array_self(source_path, source_payload, arr)

        for p, payload in expanded.items():
            self._replace_element_instance(p, payload)

        return True, "Array regenerated"

    def export_ui_json(self, filepath):
        target = filepath
        if not os.path.isabs(target):
            target = os.path.join(os.getcwd(), target)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        payload = self.serialize_ui_elements()
        with open(target, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        return target

    def addElement(self, path, data):
        """Add a UI element at the specified path."""
        element = UIelement(path, data, self.data, self, self.input)
        self.ui_elements[path] = element

    def create_element(self, path, element_data=None):
        if not path or path in self.ui_elements:
            return None
        payload = copy.deepcopy(element_data or {
            "data": {"__visible": True},
            "container": {"pos": [0, 0], "size": [120, 40], "keywords": ["crop"], "opts": {}},
            "colorRect": {"color": "#202020"},
            "outline": {"width": 1, "color": "#606060"},
        })
        self.addElement(path, payload)
        return self.getElement(path)

    def remove_element_tree(self, path):
        if not path:
            return 0
        targets = [key for key in self.ui_elements.keys() if key == path or key.startswith(f"{path}.")]
        for key in targets:
            self.ui_elements.pop(key, None)
        return len(targets)

    def rename_element_path(self, old_path, new_path):
        if not old_path or not new_path:
            return False, "Invalid path"
        if old_path not in self.ui_elements:
            return False, "Source element does not exist"
        if old_path == new_path:
            return True, "No change"
        if new_path in self.ui_elements:
            return False, "Target path already exists"
        if new_path.startswith(f"{old_path}."):
            return False, "Target path cannot be inside source subtree"

        touched = [key for key in self.ui_elements.keys() if key == old_path or key.startswith(f"{old_path}.")]
        touched.sort(key=lambda p: p.count("."))

        remapped = []
        for key in touched:
            suffix = key[len(old_path):]
            remapped.append((key, f"{new_path}{suffix}"))

        moved = []
        for src, dst in remapped:
            elm = self.ui_elements.pop(src)
            elm.path = dst
            elm.name = dst
            moved.append((dst, elm))

        for dst, elm in moved:
            self.ui_elements[dst] = elm

        self._remap_element_path_references(old_path, new_path)

        return True, "Renamed"

    def reparent_element(self, path, new_parent_path, new_name=None):
        if not path or path not in self.ui_elements:
            return False, "Source element does not exist", None
        if "." not in path:
            return False, "Root element cannot be reparented", None
        if not new_parent_path or new_parent_path not in self.ui_elements:
            return False, "Target parent does not exist", None

        leaf = path.rsplit(".", 1)[1]
        name = (new_name or leaf).strip()
        if not name:
            return False, "Name cannot be empty", None
        target = f"{new_parent_path}.{name}"
        ok, msg = self.rename_element_path(path, target)
        return ok, msg, target if ok else None

    def _map_obj(self, obj, mapper):
        if isinstance(obj, dict):
            return {k: self._map_obj(v, mapper) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._map_obj(v, mapper) for v in obj]
        if isinstance(obj, str):
            return mapper(obj)
        return obj

    def _replace_path_token(self, text, old_path, new_path):
        if text == old_path:
            return new_path
        old_prefix = f"{old_path}."
        if text.startswith(old_prefix):
            return f"{new_path}{text[len(old_path):]}"
        return text

    def _replace_state_binding_token(self, text, old_path, new_path):
        old_root = f"__GAME_STATE.{old_path}"
        new_root = f"__GAME_STATE.{new_path}"
        if text == old_root:
            return new_root
        if text.startswith(f"{old_root}."):
            return f"{new_root}{text[len(old_root):]}"
        return text

    def _remap_element_path_references(self, old_path, new_path):
        def mapper(text):
            return self._replace_path_token(text, old_path, new_path)

        for element in self.ui_elements.values():
            element.local_data = self._map_obj(element.local_data, mapper)
            element.elmData = self._map_obj(element.elmData, mapper)
            for comp in element.components.values():
                comp.config = self._map_obj(comp.config, mapper)

    def rename_game_state_path(self, old_path, new_path):
        if self.GAME_STATE is None:
            return False, "No GAME_STATE"
        if not old_path or not new_path:
            return False, "Invalid path"
        if old_path == new_path:
            return True, "No change"

        root = self.GAME_STATE.state
        old_parts = old_path.split(".")
        new_parts = new_path.split(".")

        # Locate source
        node = root
        for p in old_parts[:-1]:
            if not isinstance(node, dict) or p not in node:
                return False, "Source path not found"
            node = node[p]
        if not isinstance(node, dict) or old_parts[-1] not in node:
            return False, "Source path not found"
        moved_value = node[old_parts[-1]]

        # Ensure target parent exists
        target_parent = root
        for p in new_parts[:-1]:
            if p not in target_parent or not isinstance(target_parent[p], dict):
                target_parent[p] = {}
            target_parent = target_parent[p]
        if new_parts[-1] in target_parent:
            return False, "Target already exists"

        # Move
        del node[old_parts[-1]]
        target_parent[new_parts[-1]] = moved_value

        def mapper(text):
            return self._replace_state_binding_token(text, old_path, new_path)

        for element in self.ui_elements.values():
            element.local_data = self._map_obj(element.local_data, mapper)
            element.elmData = self._map_obj(element.elmData, mapper)
            for comp in element.components.values():
                comp.config = self._map_obj(comp.config, mapper)

        return True, "Renamed"

    def removeElement(self, path):
        self.ui_elements.pop(path, None)

    def getElement(self, path, default=None):
        return self.ui_elements.get(path, default)

    def _nearest_existing_parent_path(self, path):
        if "." not in path:
            return None
        parent_path = path.rsplit(".", 1)[0]
        while parent_path:
            if parent_path in self.ui_elements:
                return parent_path
            if "." not in parent_path:
                break
            parent_path = parent_path.rsplit(".", 1)[0]
        return None

    def get_children(self, parent_path, direct_only=True):
        """Return child elements for a parent path.

        direct_only=True returns only one-level children (a.b -> a.b.c).
        """
        prefix = f"{parent_path}."
        results = []
        for element in self.flattenElements():
            if element.path == parent_path:
                continue
            if not element.path.startswith(prefix):
                continue

            if direct_only:
                nearest_parent = self._nearest_existing_parent_path(element.path)
                if nearest_parent != parent_path:
                    continue

            results.append(element)
        return results

    def _in_scope(self, element_path, scope):
        if not scope:
            return True
        for scope_path in scope:
            if element_path == scope_path or element_path.startswith(f"{scope_path}."):
                return True
        return False

    def emit_event(self, event, eventData=None, scope=None, source_element=None, componentName=None, component=None):
        payload = eventData or {}
        targets = [elm for elm in self.flattenElements() if self._in_scope(elm.path, scope)]
        for element in targets:
            element.handleEvent(event, payload, sourcePath=source_element, componentName=componentName, component=component)

        self.handleEvent(event, payload, source_element, componentName, component)
    
    def pushEvent(self, event, eventData, componentName = None, component = None):
        self.emit_event(event, eventData=eventData, componentName=componentName, component=component)
    
    def callData(self, path, default=None):
        """Utility function for UI components to access manager data"""
        
        match path:
            case _: return PathDict.get(self.data, path, default)

    def handleEvent(self, event, eventData, sourcePath=None, componentName=None, component=None):
        """Handle an event from a component. Can be overridden by subclasses."""
        pass