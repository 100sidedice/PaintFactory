from src.UI.ui_element import UIelement
from src.utils.path_dict import PathDict
import copy

class UIManager:
    def __init__(self, data, input, surface, GAME_STATE=None, game=None):
        self.data = data
        self.input = input
        self.ui_elements = {}
        self.surface = surface
        self.GAME_STATE = GAME_STATE
        self.game = game

    def loadUIElements(self):
        """Load UI elements from data and create UIelement instances."""
        raw_ui_data = self.data.get("uiElements", {})
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

    def _expand_array(self, path, element_data):
        """Expand an element with `array` config into multiple concrete elements."""
        arr = element_data.get("array")
        if not isinstance(arr, dict):
            return {path: element_data}

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

                # Apply array spacing to container position.
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

        return expanded

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
        # Update children first, then parents (reverse depth order).
        for element in reversed(self.flattenElements()):
            if hasattr(element, "update"):
                element.update(delta)

    def draw(self):
        # Draw parents first, then children so children layer above.
        for element in self.flattenElements():
            if hasattr(element, "draw"):
                element.draw(self.surface)

    def addElement(self, path, data):
        """Add a UI element at the specified path."""
        element = UIelement(path, data, self.data, self, self.input)
        self.ui_elements[path] = element

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