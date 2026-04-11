import pygame
import math

from src.UI.uiComponents.ui_component import UIComponent


class ContainerComponent(UIComponent):
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self.updateType = "continuous"
        self._layout_offset = None
        self._layout_size = None
        self._auto_size = None
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        self.scroll_vx = 0.0
        self.scroll_vy = 0.0

    def _keywords(self):
        return {str(k).lower() for k in self.config.get("keywords", [])}

    def has_keyword(self, keyword):
        return str(keyword).lower() in self._keywords()

    def is_static(self):
        return self.has_keyword("static")

    def _is_flex_enabled(self):
        return self.has_keyword("flex") or self.has_keyword("flexx") or self.has_keyword("flexy")

    def _stretch_axis(self):
        """Keyword-driven stretch flags.

        Supported keywords:
        - stretch   -> stretch X and Y
        - stretchX  -> stretch X only
        - stretchY  -> stretch Y only
        """
        sx = self.has_keyword("stretch") or self.has_keyword("stretchx")
        sy = self.has_keyword("stretch") or self.has_keyword("stretchy")
        return sx, sy

    def _flex_axis_flags(self):
        """Return (flex_x, flex_y) resolved from flex keywords."""
        axis = self._flex_axis()
        if axis == "x":
            return True, False
        if axis == "y":
            return False, True
        if axis == "both":
            return True, True
        return False, False

    def _flex_axis(self):
        if self.has_keyword("flexx") and not self.has_keyword("flexy"):
            return "x"
        if self.has_keyword("flexy") and not self.has_keyword("flexx"):
            return "y"
        if self.has_keyword("flex"):
            return str(self._opts().get("axis", "both")).lower()
        return None

    def _is_scroll_enabled(self):
        return self.has_keyword("scrollable") or self.has_keyword("scroll") or self.has_keyword("scrollx") or self.has_keyword("scrolly")

    def _scroll_axis_enabled(self):
        opts = self._opts()
        explicit_x = opts.get("scrollX")
        explicit_y = opts.get("scrollY")

        if explicit_x is None:
            sx = self.has_keyword("scrollx")
        else:
            sx = bool(explicit_x)

        if explicit_y is None:
            sy = self.has_keyword("scrolly") or self.has_keyword("scrollable") or self.has_keyword("scroll")
        else:
            sy = bool(explicit_y)

        # plain scroll keyword defaults to Y scrolling
        if self.has_keyword("scroll") and explicit_y is None and not self.has_keyword("scrollx"):
            sy = True

        return sx, sy

    def _opts(self):
        return self.config.get("opts", {})

    def _input_passcodes(self):
        """Optional passcode or passcode list allowed to read input while locked."""
        return self._opts().get("inputPasscodes", None)

    def _override_transform_enabled(self):
        # True => layout systems may override configured size (including shrinking).
        # False => do not shrink below configured base size.
        return bool(self._opts().get("overrideTransform", True))

    def _padding(self, context=None):
        """Resolve padding with behavior-priority fallback.

        Priority requested: flex > stretch > grid.
        Supported keys in `opts`:
        - flexPadding
        - stretchPadding
        - gridPadding
        - padding (global fallback)
        """
        opts = self._opts()

        if context == "flex":
            pad = opts.get("flexPadding", opts.get("stretchPadding", opts.get("gridPadding", opts.get("padding", [0, 0]))))
        elif context == "stretch":
            pad = opts.get("stretchPadding", opts.get("gridPadding", opts.get("padding", [0, 0])))
        elif context == "grid":
            pad = opts.get("gridPadding", opts.get("padding", [0, 0]))
        else:
            # Mixed-mode default priority: flex then stretch then grid then base padding.
            pad = opts.get("flexPadding", opts.get("stretchPadding", opts.get("gridPadding", opts.get("padding", [0, 0]))))

        if isinstance(pad, (int, float)):
            return int(pad), int(pad)
        if isinstance(pad, (list, tuple)):
            px = int(pad[0]) if len(pad) > 0 else 0
            py = int(pad[1]) if len(pad) > 1 else px
            return px, py
        return 0, 0

    def _base_pos(self):
        pos = self.config.get("pos", [0, 0])
        x = self._to_float(pos[0] if len(pos) > 0 else 0.0)
        y = self._to_float(pos[1] if len(pos) > 1 else 0.0)
        return x, y

    def _to_float(self, value, default=0.0):
        try:
            return float(value)
        except Exception:
            return float(default)

    def _resolve_anchor_pos(self, axis, value, parent_container=None, own_size=0.0):
        """Resolve special anchor values for `pos`.

        Supported:
        - X axis: __left, __middle, __right
        - Y axis: __top, __middle, __bottom
        """
        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return self._to_float(value)

        token = value.lower()
        if not token.startswith("__"):
            return self._to_float(value)

        pw = 0.0
        ph = 0.0
        if parent_container is not None:
            try:
                parent_content = parent_container.get_content_rect()
                pw = float(parent_content.w)
                ph = float(parent_content.h)
            except Exception:
                pw = 0.0
                ph = 0.0

        own = float(own_size)

        if axis == "x":
            if token == "__left":
                return 0.0
            if token == "__middle":
                return (pw - own) / 2.0
            if token == "__right":
                return pw - own
            # cross-axis aliases
            if token == "__top":
                return 0.0
            if token == "__bottom":
                return pw - own

        if axis == "y":
            if token == "__top":
                return 0.0
            if token == "__middle":
                return (ph - own) / 2.0
            if token == "__bottom":
                return ph - own
            # cross-axis aliases
            if token == "__left":
                return 0.0
            if token == "__right":
                return ph - own

        return self._to_float(value)

    def _base_size(self):
        size = self.config.get("size", [0, 0])
        w = int(self._to_float(size[0], 0.0)) if len(size) > 0 else 0
        h = int(self._to_float(size[1], 0.0)) if len(size) > 1 else 0
        return w, h

    def _resolve_anchor_size(self, axis, value, local_pos=0.0, parent_container=None):
        """Resolve special anchor values for `size`.

        Supported:
        - X axis: __right | __width  -> width extends to parent's right edge
        - Y axis: __bottom | __height -> height extends to parent's bottom edge
        """
        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return self._to_float(value, 0.0)

        token = value.lower().strip()
        if not token.startswith("__"):
            return self._to_float(value, 0.0)

        pw = 0.0
        ph = 0.0
        if parent_container is not None:
            try:
                parent_content = parent_container.get_content_rect()
                pw = float(parent_content.w)
                ph = float(parent_content.h)
            except Exception:
                pw = 0.0
                ph = 0.0

        if axis == "x":
            if token in {"__right", "__width"}:
                return max(0.0, pw - float(local_pos))
            if token in {"__left", "__top"}:
                return 0.0

        if axis == "y":
            if token in {"__bottom", "__height"}:
                return max(0.0, ph - float(local_pos))
            if token in {"__left", "__top"}:
                return 0.0

        return self._to_float(value, 0.0)

    def clear_layout(self):
        self._layout_offset = None
        self._layout_size = None

    def set_layout_offset(self, x, y):
        self._layout_offset = (float(x), float(y))

    def set_layout_size(self, w, h):
        self._layout_size = (int(w), int(h))

    def get_preferred_size(self):
        if self._layout_size is not None and not self.is_static():
            return self._layout_size
        return self._base_size()

    def _local_pos(self):
        if self._layout_offset is not None and not self.is_static():
            return self._layout_offset
        return self._base_pos()

    def _local_size(self):
        if self._is_flex_enabled() and self._auto_size is not None:
            return self._auto_size
        if self._layout_size is not None and not self.is_static():
            return self._layout_size
        return self._base_size()

    def get_content_rect(self, rect=None):
        rect = rect or self.get_rect()
        px, py = self._padding()
        return pygame.Rect(rect.x + px, rect.y + py, max(0, rect.w - (px * 2)), max(0, rect.h - (py * 2)))

    def get_child_origin(self, child_element=None):
        content = self.get_content_rect()
        child_container = child_element.getComponent("container") if child_element is not None else None
        child_static = bool(child_container and child_container.is_static())

        ox = content.x
        oy = content.y
        if self._is_scroll_enabled() and not child_static:
            sx, sy = self._scroll_axis_enabled()
            if sx:
                ox -= int(self.scroll_x)
            if sy:
                oy -= int(self.scroll_y)
        return ox, oy

    def get_rect(self):
        # resolve raw position first so anchor tokens can be interpreted
        raw_pos = self.config.get("pos", [0, 0])
        raw_x = raw_pos[0] if len(raw_pos) > 0 else 0.0
        raw_y = raw_pos[1] if len(raw_pos) > 1 else 0.0
        raw_size = self.config.get("size", [0, 0])
        raw_w = raw_size[0] if len(raw_size) > 0 else 0
        raw_h = raw_size[1] if len(raw_size) > 1 else 0

        w, h = self._local_size()

        x = self._resolve_anchor_pos("x", raw_x, own_size=w)
        y = self._resolve_anchor_pos("y", raw_y, own_size=h)

        # layout overrides still apply for non-static children
        if self._layout_offset is not None and not self.is_static():
            x, y = self._layout_offset

        if not self.has_keyword("globalparent"):
            parent = self.element.get_parent()
            if parent is not None:
                parent_container = parent.getComponent("container")
                if parent_container is not None:
                    # re-resolve anchor tokens against parent container content size
                    if self._layout_offset is None or self.is_static():
                        x = self._resolve_anchor_pos("x", raw_x, parent_container, own_size=w)
                        y = self._resolve_anchor_pos("y", raw_y, parent_container, own_size=h)
                    if self._layout_size is None or self.is_static():
                        w = self._resolve_anchor_size("x", raw_w, local_pos=x, parent_container=parent_container)
                        h = self._resolve_anchor_size("y", raw_h, local_pos=y, parent_container=parent_container)
                    px, py = parent_container.get_child_origin(self.element)
                    x += px
                    y += py
                else:
                    parent_rect = parent.get_rect()
                    if parent_rect is not None:
                        x += parent_rect.x
                        y += parent_rect.y

        return pygame.Rect(int(x), int(y), int(w), int(h))

    def _iter_direct_children(self):
        return self.manager.get_children(self.element.path, direct_only=True)

    def _apply_grid_layout(self):
        if not self.has_keyword("grid"):
            return

        opts = self._opts()
        cols = int(opts.get("columns", 1) or 1)
        cols = max(1, cols)

        gap_value = opts.get("gap", [0, 0])
        if isinstance(gap_value, (int, float)):
            gap_x = gap_y = int(gap_value)
        else:
            gap_x = int(gap_value[0]) if len(gap_value) > 0 else 0
            gap_y = int(gap_value[1]) if len(gap_value) > 1 else gap_x

        stretch_x, stretch_y = self._stretch_axis()
        pad_context = "stretch" if (stretch_x or stretch_y) else "grid"
        pad_x, pad_y = self._padding(pad_context)
        cell_size = opts.get("cellSize")

        # Backward compatibility (legacy opts.stretch), used only if no stretch keywords are set.
        if not stretch_x and not stretch_y:
            stretch_value = opts.get("stretch", False)
            if isinstance(stretch_value, str):
                stretch_mode = stretch_value.lower()
            elif stretch_value is True:
                stretch_mode = "both"
            else:
                stretch_mode = "none"
            stretch_x = stretch_mode in {"x", "both", "true"}
            stretch_y = stretch_mode in {"y", "both", "true"}

        children = []
        for child in self._iter_direct_children():
            if not child.is_visible():
                continue
            child_container = child.getComponent("container")
            if child_container is None or child_container.is_static():
                continue
            children.append(child_container)

        if not children:
            return

        content_rect = self.get_content_rect()
        rows = max(1, math.ceil(len(children) / cols))

        if cell_size is not None:
            base_cw = int(cell_size[0]) if len(cell_size) > 0 else 0
            base_ch = int(cell_size[1]) if len(cell_size) > 1 else 0
        else:
            widths = [c._base_size()[0] for c in children]
            heights = [c._base_size()[1] for c in children]
            base_cw = max(widths) if widths else 0
            base_ch = max(heights) if heights else 0

        available_w = content_rect.w - gap_x * (cols - 1)
        if stretch_x and cols > 0 and available_w > 0:
            cw = max(1, int(available_w / cols))
        else:
            cw = base_cw

        available_h = content_rect.h - gap_y * (rows - 1)
        if stretch_y and rows > 0 and available_h > 0:
            ch = max(1, int(available_h / rows))
        else:
            ch = base_ch

        index = 0
        for child_container in children:
            col = index % cols
            row = index // cols
            # layout offsets are relative to parent's content origin,
            # so do not add padding a second time here.
            x = col * (cw + gap_x)
            y = row * (ch + gap_y)
            child_container.set_layout_offset(x, y)
            # Axis-specific override: flexX overrides stretchX only, flexY overrides stretchY only.
            if stretch_x or stretch_y:
                base_w, base_h = child_container._base_size()
                child_flex_x, child_flex_y = child_container._flex_axis_flags()
                final_w = cw if (stretch_x and not child_flex_x) else base_w
                final_h = ch if (stretch_y and not child_flex_y) else base_h
                child_container.set_layout_size(final_w, final_h)
            index += 1

    def _apply_stretch_layout(self):
        """Apply stretchX/stretchY to direct children for non-grid containers."""
        if self.has_keyword("grid"):
            return

        stretch_x, stretch_y = self._stretch_axis()
        if not (stretch_x or stretch_y):
            return

        content_rect = self.get_content_rect()
        for child in self._iter_direct_children():
            if not child.is_visible():
                continue
            child_container = child.getComponent("container")
            if child_container is None or child_container.is_static():
                continue

            base_w, base_h = child_container._base_size()
            child_flex_x, child_flex_y = child_container._flex_axis_flags()

            # Axis-specific flex override: flexX blocks stretchX, flexY blocks stretchY.
            target_w = content_rect.w if (stretch_x and not child_flex_x) else base_w
            target_h = content_rect.h if (stretch_y and not child_flex_y) else base_h

            # Optional protection against shrinking below configured child size.
            if not child_container._override_transform_enabled():
                target_w = max(base_w, target_w)
                target_h = max(base_h, target_h)

            child_container.set_layout_size(target_w, target_h)

    def _apply_flex_size(self):
        if not self._is_flex_enabled():
            self._auto_size = None
            return

        axis = self._flex_axis() or "both"
        pad_x, pad_y = self._padding("flex")

        min_left = 0
        min_top = 0
        max_right = 0
        max_bottom = 0
        first = True
        for child in self._iter_direct_children():
            if not child.is_visible():
                continue
            child_container = child.getComponent("container")
            if child_container is None:
                continue
            cx, cy = child_container._local_pos()
            cw, ch = child_container._local_size()
            left = int(cx)
            top = int(cy)
            right = int(cx + cw)
            bottom = int(cy + ch)
            if first:
                min_left, min_top = left, top
                max_right, max_bottom = right, bottom
                first = False
            else:
                min_left = min(min_left, left)
                min_top = min(min_top, top)
                max_right = max(max_right, right)
                max_bottom = max(max_bottom, bottom)

        if first:
            min_left = 0
            min_top = 0

        base_w, base_h = self._base_size()
        content_w = max(0, max_right - min(0, min_left))
        content_h = max(0, max_bottom - min(0, min_top))
        target_w = content_w + pad_x * 2
        target_h = content_h + pad_y * 2

        if not self._override_transform_enabled():
            target_w = max(base_w, target_w)
            target_h = max(base_h, target_h)

        if axis == "x":
            self._auto_size = (target_w, base_h)
        elif axis == "y":
            self._auto_size = (base_w, target_h)
        else:
            self._auto_size = (target_w, target_h)

    def _content_bounds(self):
        min_x = 0
        min_y = 0
        max_x = 0
        max_y = 0

        first = True
        for child in self._iter_direct_children():
            if not child.is_visible():
                continue
            child_container = child.getComponent("container")
            if child_container is None or child_container.is_static():
                continue
            cx, cy = child_container._local_pos()
            cw, ch = child_container._local_size()
            left = int(cx)
            top = int(cy)
            right = int(cx + cw)
            bottom = int(cy + ch)
            if first:
                min_x, min_y, max_x, max_y = left, top, right, bottom
                first = False
            else:
                min_x = min(min_x, left)
                min_y = min(min_y, top)
                max_x = max(max_x, right)
                max_y = max(max_y, bottom)

        if first:
            return 0, 0, 0, 0
        return min_x, min_y, max_x, max_y

    def _clamp_scroll(self):
        if not self._is_scroll_enabled():
            self.scroll_x = 0.0
            self.scroll_y = 0.0
            self.scroll_vx = 0.0
            self.scroll_vy = 0.0
            return

        opts = self._opts()
        mode = str(opts.get("limits", "element")).lower()
        scroll_x_enabled, scroll_y_enabled = self._scroll_axis_enabled()

        if not scroll_x_enabled:
            self.scroll_x = 0.0
            self.scroll_vx = 0.0
        if not scroll_y_enabled:
            self.scroll_y = 0.0
            self.scroll_vy = 0.0

        if mode == "infinite":
            return

        if mode == "values":
            min_x = float(opts.get("minX", 0.0))
            max_x = float(opts.get("maxX", 0.0))
            min_y = float(opts.get("minY", 0.0))
            max_y = float(opts.get("maxY", 0.0))
            self.scroll_x = max(min_x, min(self.scroll_x, max_x))
            self.scroll_y = max(min_y, min(self.scroll_y, max_y))
            return

        # element bounds
        content_rect = self.get_content_rect()
        min_x, min_y, max_x, max_y = self._content_bounds()
        content_w = max(0, max_x - min_x)
        content_h = max(0, max_y - min_y)
        max_scroll_x = max(0, content_w - content_rect.w)
        max_scroll_y = max(0, content_h - content_rect.h)
        self.scroll_x = max(0.0, min(self.scroll_x, float(max_scroll_x)))
        self.scroll_y = max(0.0, min(self.scroll_y, float(max_scroll_y)))

    def _update_scroll(self, delta):
        if not self._is_scroll_enabled():
            return

        rect = self.get_rect()
        passcodes = self._input_passcodes()
        mx, my = self.input.get_mouse_position(passcodes)
        opts = self._opts()
        scroll_x_enabled, scroll_y_enabled = self._scroll_axis_enabled()

        if not rect.collidepoint((mx, my)):
            damping = float(opts.get("scrollDamping", 18.0))
            t = max(0.0, min(1.0, damping * max(0.0, float(delta))))
            self.scroll_vx *= (1.0 - t)
            self.scroll_vy *= (1.0 - t)
            self._clamp_scroll()
            return

        wheel_x, wheel_y = self.input.get_mouse_wheel(passcodes)
        shift_held = self.input.get_key(pygame.K_LSHIFT, passcodes) or self.input.get_key(pygame.K_RSHIFT, passcodes)

        speed = float(opts.get("scrollSpeed", 24.0))
        impulse = float(opts.get("scrollImpulse", speed * 16.0))
        damping = float(opts.get("scrollDamping", 18.0))

        if shift_held and scroll_x_enabled and wheel_x == 0 and wheel_y != 0:
            wheel_x = wheel_y
            wheel_y = 0

        if scroll_y_enabled and wheel_y != 0:
            self.scroll_vy += -float(wheel_y) * impulse
        if scroll_x_enabled and wheel_x != 0:
            self.scroll_vx += -float(wheel_x) * impulse

        # velocity-based smoothing
        dt = max(0.0, float(delta))
        self.scroll_x += self.scroll_vx * dt
        self.scroll_y += self.scroll_vy * dt

        # exponential-like damping in discrete form
        t = max(0.0, min(1.0, damping * dt))
        self.scroll_vx *= (1.0 - t)
        self.scroll_vy *= (1.0 - t)

        # keep small velocity drift from accumulating
        if abs(self.scroll_vx) < 0.01:
            self.scroll_vx = 0.0
        if abs(self.scroll_vy) < 0.01:
            self.scroll_vy = 0.0

        self._clamp_scroll()

    def update(self, delta):
        # reset child layout every frame before applying layout containers
        for child in self._iter_direct_children():
            child_container = child.getComponent("container")
            if child_container is not None:
                child_container.clear_layout()

        self._apply_grid_layout()
        self._apply_stretch_layout()
        self._apply_flex_size()
        self._update_scroll(delta)
