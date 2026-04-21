import pygame

from src.UI.uiComponents.UIcomponent import UIComponent


class TextComponent(UIComponent):
    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self.passcode = f"ui.text.{self.element.path}"
        self.focused = False
        self._blink_elapsed = 0.0
        self.editing_flag = self.config.get("editingFlag", "__editingText")
        if self.element.get_data(self.editing_flag) is None:
            self.element.set_data(self.editing_flag, False)

    def _resolve_value(self, value, default=None):
        if isinstance(value, str):
            if value.startswith("__"):
                return self.element.get_data(value, default)
            if value.startswith("$theme."):
                return self.manager.callData(f"themeDefaults.{value[7:]}", default)
            if value.startswith("themeDefaults."):
                return self.manager.callData(value, default)
        return value if value is not None else default

    def _parse_color(self, value, default=(255, 255, 255)):
        value = self._resolve_value(value, default)

        if isinstance(value, str):
            color_text = value.strip()
            if color_text.startswith("#"):
                color_text = color_text[1:]
            if len(color_text) == 6:
                try:
                    return (
                        int(color_text[0:2], 16),
                        int(color_text[2:4], 16),
                        int(color_text[4:6], 16),
                    )
                except ValueError:
                    return default

        if isinstance(value, (list, tuple)) and len(value) >= 3:
            return (int(value[0]), int(value[1]), int(value[2]))

        return default

    def _get_font(self):
        size = int(self._resolve_value(self.config.get("fontSize", 20), 20))
        font_name = self._resolve_value(self.config.get("font", None), None)
        return pygame.font.SysFont(font_name, size)

    def _get_text_key(self):
        return self.config.get("bind", "__text")

    def _is_editable(self):
        return bool(self.config.get("editable", False))

    def _inside(self):
        rect = self.get_rect()
        if rect is None:
            return False
        mx, my = self.input.get_mouse_position(self.passcode if self.focused else None)
        return rect.collidepoint((mx, my))

    def _focus(self):
        if self.focused:
            return
        self.focused = True
        self._blink_elapsed = 0.0
        self.element.set_data(self.editing_flag, True)
        self.input.lock(self.passcode, {"type": "unlock"})

    def _blur(self):
        if not self.focused:
            return
        self.focused = False
        self.element.set_data(self.editing_flag, False)
        self.input.unlock(self.passcode)

    def _handle_focus_clicks(self):
        if self.input.get_mouse_button_down(1, self.passcode if self.focused else None):
            if self._inside() and self._is_editable():
                self._focus()
            elif self.focused:
                self._blur()

    def _handle_keyboard(self):
        if not self.focused or not self._is_editable():
            return

        text_key = self._get_text_key()
        current = str(self.element.get_data(text_key, ""))
        max_len = int(self.config.get("maxLength", 999999))

        entered = self.input.consume_text_input(self.passcode)
        if entered:
            for chunk in entered:
                if len(current) >= max_len:
                    break
                remaining = max_len - len(current)
                current += chunk[:remaining]
            self.element.set_data(text_key, current)

        if self.input.get_key_down(pygame.K_BACKSPACE, self.passcode):
            self.element.set_data(text_key, current[:-1])

        if self.input.get_key_down(pygame.K_RETURN, self.passcode) or self.input.get_key_down(pygame.K_KP_ENTER, self.passcode):
            submit_event = self.config.get("submitEvent")
            if submit_event:
                self.manager.emit_event(submit_event, {"source": self.element.path, "text": self.element.get_data(text_key, "")}, scope=self.config.get("submitScope"), source_element=self.element.path, componentName=self.name, component=self)
            if self.config.get("blurOnEnter", True):
                self._blur()

        if self.input.get_key_down(pygame.K_ESCAPE, self.passcode):
            self._blur()

    def update(self, delta):
        if not self.element.is_visible():
            return

        self._handle_focus_clicks()
        self._handle_keyboard()
        self._blink_elapsed += delta

    def draw(self, surface):
        if not self.element.is_visible():
            return

        rect = self.get_rect()
        if rect is None:
            return

        text_key = self._get_text_key()
        value = str(self.element.get_data(text_key, ""))
        placeholder = str(self.config.get("placeholder", ""))

        font = self._get_font()
        text_color = self._parse_color(self.config.get("color", "$theme.text.color"), (255, 255, 255))
        placeholder_color = self._parse_color(self.config.get("placeholderColor", "$theme.text.placeholder_color"), (150, 150, 150))
        caret_color = self._parse_color(self.config.get("caretColor", "$theme.caret.color"), (255, 255, 255))
        blink_rate = float(self._resolve_value(self.config.get("caretBlinkRate", "$theme.caret.blink_rate"), 0.5) or 0.5)
        blink_rate = max(0.05, blink_rate)

        padding = self.config.get("padding", [6, 4])
        px = int(padding[0]) if len(padding) > 0 else 6
        py = int(padding[1]) if len(padding) > 1 else 4
        content_x = rect.x + px
        content_y = rect.y + py
        content_w = max(0, rect.w - (px * 2))
        content_h = max(0, rect.h - (py * 2))

        draw_text = value if value else placeholder
        color = text_color if value else placeholder_color
        wrap_enabled = bool(self.config.get("wrap", False))

        # prepare lines (either single line or wrapped)
        lines = []
        if not draw_text:
            lines = [""]
        else:
            if not wrap_enabled:
                lines = [draw_text]
            else:
                # wrap by words to fit content_w
                raw_lines = draw_text.split("\n")
                for rl in raw_lines:
                    words = rl.split(" ")
                    cur = ""
                    for w in words:
                        candidate = w if cur == "" else cur + " " + w
                        w_surf = font.render(candidate, True, color)
                        if w_surf.get_width() <= content_w:
                            cur = candidate
                        else:
                            if cur != "":
                                lines.append(cur)
                            # if single word longer than width, break the word
                            if font.render(w, True, color).get_width() > content_w and len(w) > 1:
                                # crude char-level break
                                part = ""
                                for ch in w:
                                    cand2 = part + ch
                                    if font.render(cand2, True, color).get_width() <= content_w:
                                        part = cand2
                                    else:
                                        if part:
                                            lines.append(part)
                                        part = ch
                                if part:
                                    cur = part
                                else:
                                    cur = ""
                            else:
                                cur = w
                    if cur != "":
                        lines.append(cur)

        # measure lines and clip to content_h (ellipsis last line if needed)
        line_surfaces = [font.render(l, True, color) for l in lines]
        line_h = font.get_height()
        max_lines = max(1, content_h // line_h) if line_h > 0 else len(line_surfaces)
        if len(line_surfaces) > max_lines:
            # truncate and add ellipsis to last visible line
            line_surfaces = line_surfaces[:max_lines]
            last_text = lines[max_lines - 1]
            ell = "..."
            # shorten last_text until it fits with ellipsis
            while last_text and font.render(last_text + ell, True, color).get_width() > content_w:
                last_text = last_text[:-1]
            line_surfaces[-1] = font.render((last_text + ell) if last_text else ell, True, color)

        # horizontal alignment
        align = str(self.config.get("align", "left") or "left").strip().lower()
        # vertical alignment for block of lines
        block_h = len(line_surfaces) * line_h
        vertical_align = self.config.get("verticalAlign", self.config.get("valign", "top"))
        vertical_align = str(vertical_align or "top").strip().lower()
        if vertical_align in {"center", "middle"}:
            text_y = content_y + (content_h - block_h) // 2
        elif vertical_align in {"bottom", "end"}:
            text_y = content_y + content_h - block_h
        else:
            text_y = content_y

        old_clip = surface.get_clip()
        surface.set_clip(old_clip.clip(rect))
        # blit each line
        for idx, ls in enumerate(line_surfaces):
            lw = ls.get_width()
            if align in {"center", "middle"}:
                text_x = content_x + (content_w - lw) // 2
            elif align in {"right", "end"}:
                text_x = content_x + content_w - lw
            else:
                text_x = content_x
            surface.blit(ls, (text_x, text_y + idx * line_h))

        if self.focused and self._is_editable():
            phase = (self._blink_elapsed % (blink_rate * 2.0))
            caret_visible = phase < blink_rate
            if caret_visible:
                caret_text = font.render(value, True, text_color)
                caret_x = text_x + caret_text.get_width() + 1
                caret_y1 = text_y
                caret_y2 = text_y + max(1, font.get_height() - 2)
                pygame.draw.line(surface, caret_color, (caret_x, caret_y1), (caret_x, caret_y2), 1)

        surface.set_clip(old_clip)
