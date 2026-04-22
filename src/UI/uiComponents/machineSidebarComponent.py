from src.UI.uiComponents.UIcomponent import UIComponent
import copy

class MachineSidebarComponent(UIComponent):
    """Populate the parent sidebar with a button per machine and keep counts updated.

    This component reads `manager.data['machines']` for available machine keys
    and creates child UI elements (based on an existing template) under the
    parent. It updates each child's `__count` data to show remaining allowed
    machines per the current level.
    """

    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self.child_paths = []
        self.template_path = f"{self.element.path}.machine-select0"
        # generate children once
        try:
            self._generate_children()
        except Exception:
            pass

    def _generate_children(self):
        manager = self.manager
        parent = self.element.path
        machines_defs = manager.callData("machines") or {}
        # determine current level machine_limits (only show machines listed there)
        try:
            from ...Levels import levels as levels_data
            level = levels_data.get_level(None, preloaded_assets=manager.data)
            level_limits = level.get("machine_limits", {}) if level else {}
        except Exception:
            level_limits = {}

        # Find template element data (raw) if present
        raw = None
        try:
            raw = manager.get_array_source_raw(self.template_path) or manager._raw_ui_data.get(self.template_path)
        except Exception:
            raw = manager._raw_ui_data.get(self.template_path) if hasattr(manager, '_raw_ui_data') else None

        if raw is None:
            # fall back to using an existing instantiated element
            tpl = manager.getElement(self.template_path)
            if tpl is not None:
                raw = copy.deepcopy(tpl.elmData)

        if not isinstance(raw, dict):
            return

        # Create one child per machine key (skip special keys like ALL).
        # Only include machines that are type=="machine" and present in level_limits.
        for key in sorted(k for k in machines_defs.keys() if k != "ALL"):
            defs = machines_defs.get(key) or {}
            if not isinstance(defs, dict):
                continue
            if defs.get("type") != "machine":
                continue
            # only include if the current level exposes this machine in limits
            if key not in level_limits:
                continue

            new_path = f"{parent}.{key}"
            payload = copy.deepcopy(raw)
            # ensure data exists
            payload.setdefault('data', {})
            payload['data']['__machineKey'] = key
            payload['data']['__count'] = ""
            # ensure generated child is visible (template may be hidden)
            try:
                payload['data']['__visible'] = True
            except Exception:
                pass
            # update image component to use the machine's sprite
            try:
                img = payload.get('image')
                if isinstance(img, dict):
                    img['path'] = defs.get('image', img.get('path'))
                    img['row'] = int(defs.get('row', img.get('row', 0)))
                    # use frame_offset as column where present
                    img['col'] = int(defs.get('frame_offset', img.get('col', 0)))
                    frame_size = defs.get('size') or defs.get('frameSize')
                    if isinstance(frame_size, (list, tuple)):
                        img['frameSize'] = frame_size
            except Exception:
                pass

            # Register element instance
            manager._replace_element_instance(new_path, payload)
            self.child_paths.append(new_path)

    def update(self, delta):
        # update counts based on level limits and current machines
        manager = self.manager
        game = getattr(manager, 'game', None)
        machine_manager = getattr(game, 'machine_manager', None) if game is not None else None
        levels = manager.callData('levels')

        for path in list(self.child_paths):
            elm = manager.getElement(path)
            if elm is None:
                continue
            key = elm.get_data('__machineKey')
            # reflect selected state from sidebar selection element
            try:
                sel = manager.getElement("screen.machineSidebar-left.selection")
                selected_key = sel.get_data("__selectedMachine") if sel is not None else None
                elm.set_data("__selected", True if selected_key and str(selected_key) == str(key) else False)
            except Exception:
                pass
            # fetch limit via levels helper if available
            limit = None
            try:
                from ...Levels import levels as levels_data
                limit = levels_data.get_machine_limit(None, key, preloaded_assets=manager.data, default=None)
            except Exception:
                limit = None

            current = 0
            if machine_manager is not None:
                try:
                    for m in machine_manager.machines:
                        if str(getattr(m, 'name', '')) == str(key):
                            current += 1
                except Exception:
                    current = 0

            if isinstance(limit, int):
                remaining = max(0, limit - current)
                elm.set_data('__count', str(remaining))
            else:
                elm.set_data('__count', '')
