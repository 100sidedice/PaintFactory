from src.UI.uiComponents.ui_component import UIComponent
import pygame
import random
import math


class ParticleComponent(UIComponent):
    """Particle spawner component.

    Config options supported:
      - size_min, size_max (pixels)
      - colors: array of colors (hex string, rgba list, or theme refs)
      - blend: int (number of interpolation steps between listed colors)
      - speed_min, speed_max (pixels per second)
      - gravity_type: "none" | "direction" | "spiral"
      - gravity_strength: float (only for direction/spiral)
      - gravity_direction: degrees (for direction)
      - num_max: int (max concurrent particles)
      - spawn_rate_min, spawn_rate_max: particles per second
      - rot_min, rot_max: degrees per second initial angular velocity
      - particle_shapes: array of shapes: "circle","square","star"

    This is intentionally lightweight — it uses software drawing and simple
    physics. Tweak values for performance.
    """

    def __init__(self, name, element, config=None):
        super().__init__(name, element, config)
        self.updateType = "continuous"

        cfg = config or {}
        self.size_min = float(cfg.get("size_min", 2))
        self.size_max = float(cfg.get("size_max", 6))

        self.speed_min = float(cfg.get("speed_min", 10))
        self.speed_max = float(cfg.get("speed_max", 60))

        self.rot_min = float(cfg.get("rot_min", 0))
        self.rot_max = float(cfg.get("rot_max", 360))

        self.spawn_rate_min = float(cfg.get("spawn_rate_min", 5))
        self.spawn_rate_max = float(cfg.get("spawn_rate_max", 10))

        self.num_max = int(cfg.get("num_max", 200))

        self.gravity_type = str(cfg.get("gravity_type", "none") or "none")
        self.gravity_strength = float(cfg.get("gravity_strength", cfg.get("gravity", 0.0)))
        self.gravity_direction = float(cfg.get("gravity_direction", 90.0))

        self.blend = int(cfg.get("blend", 0))

        shapes = cfg.get("particle_shapes") or cfg.get("particle_shape") or ["circle"]
        if isinstance(shapes, str):
            shapes = [s.strip() for s in shapes.split(",") if s.strip()]
        self.shapes = [s for s in shapes if s in ("circle", "square", "star")] or ["circle"]

        raw_colors = cfg.get("colors") or cfg.get("color") or [(255, 255, 255, 255)]
        if isinstance(raw_colors, (str, dict)):
            raw_colors = [raw_colors]
        # parse colors using same logic as ColorRect
        self._raw_colors = raw_colors

        self.particles = []
        self._spawn_acc = 0.0

        self._palette = self._build_palette(self._raw_colors, self.blend)
        # spawn position can be absolute pixels, fraction [0..1], or special token "__middle"
        self.spawn_pos = cfg.get("spawn_pos", ["__middle", "__middle"])

    def _clamp_byte(self, value, default=255):
        try:
            return max(0, min(255, int(value)))
        except Exception:
            return int(default)

    def _parse_color(self, value):
        # Basic parsing similar to ColorRectComponent expectations.
        if isinstance(value, str) and value.startswith("__"):
            value = self.element.get_data(value, value)
        elif isinstance(value, str) and value.startswith("$theme."):
            value = self.manager.callData(f"themeDefaults.{value[7:]}", value)
        elif isinstance(value, str) and value.startswith("themeDefaults."):
            value = self.manager.callData(value, value)

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
                        255,
                    )
                except ValueError:
                    return (255, 255, 255, 255)
            if len(color_text) == 8:
                try:
                    return (
                        int(color_text[0:2], 16),
                        int(color_text[2:4], 16),
                        int(color_text[4:6], 16),
                        int(color_text[6:8], 16),
                    )
                except ValueError:
                    return (255, 255, 255, 255)

        if isinstance(value, (list, tuple)) and len(value) >= 4:
            return (
                self._clamp_byte(value[0]),
                self._clamp_byte(value[1]),
                self._clamp_byte(value[2]),
                self._clamp_byte(value[3]),
            )

        if isinstance(value, (list, tuple)) and len(value) >= 3:
            return (
                self._clamp_byte(value[0]),
                self._clamp_byte(value[1]),
                self._clamp_byte(value[2]),
                255,
            )

        return (255, 255, 255, 255)

    def _lerp_color(self, a, b, t):
        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
            int(a[3] + (b[3] - a[3]) * t),
        )

    def _build_palette(self, raw_colors, blend):
        parsed = [self._parse_color(c) for c in raw_colors]
        if not parsed:
            return [(255, 255, 255, 255)]
        if len(parsed) == 1 or blend <= 0:
            return parsed
        palette = []
        for i in range(len(parsed) - 1):
            a = parsed[i]
            b = parsed[i + 1]
            palette.append(a)
            steps = blend + 1
            for s in range(1, steps + 1):
                t = s / float(steps + 1)
                palette.append(self._lerp_color(a, b, t))
        palette.append(parsed[-1])
        return palette

    def update(self, delta, *args, **kwargs):
        if not self.element or not self.element.is_visible():
            return

        rect = self.get_rect()
        if rect is None:
            return

        # Refresh palette in case bound values changed
        self._palette = self._build_palette(self._raw_colors, self.blend)

        # spawn logic
        rate = random.uniform(self.spawn_rate_min, self.spawn_rate_max)
        self._spawn_acc += rate * delta
        to_spawn = int(self._spawn_acc)
        self._spawn_acc -= to_spawn

        for _ in range(to_spawn):
            if len(self.particles) >= self.num_max:
                break
            self._spawn_particle(rect)

        # update particles
        gx = gy = 0.0
        if self.gravity_type == "direction":
            angle = math.radians(self.gravity_direction)
            gx = math.cos(angle) * self.gravity_strength
            gy = -math.sin(angle) * self.gravity_strength

        center = (rect.centerx, rect.centery)
        alive = []
        for p in self.particles:
            # apply velocity
            if self.gravity_type == "spiral":
                # apply a small centripetal/spiral pull
                dx = p["x"] - center[0]
                dy = p["y"] - center[1]
                tx = -dy
                ty = dx
                a = self.gravity_strength * 0.01
                p["vx"] += tx * a * delta
                p["vy"] += ty * a * delta
            else:
                p["vx"] += gx * delta
                p["vy"] += gy * delta

            p["x"] += p["vx"] * delta
            p["y"] += p["vy"] * delta
            p["rot"] += p["rot_v"] * delta

            # remove only when outside manager surface
            keep = True
            try:
                screen_rect = self.manager.surface.get_rect()
                # allow a small margin equal to particle size
                margin = max(16, int(p.get("size", 2) * 4))
                if (
                    p["x"] < screen_rect.left - margin
                    or p["x"] > screen_rect.right + margin
                    or p["y"] < screen_rect.top - margin
                    or p["y"] > screen_rect.bottom + margin
                ):
                    keep = False
            except Exception:
                pass

            if keep:
                alive.append(p)

        self.particles = alive

    def _spawn_particle(self, rect):
        # determine spawn origin based on spawn_pos config
        sx, sy = self.spawn_pos if isinstance(self.spawn_pos, (list, tuple)) else (self.spawn_pos, self.spawn_pos)

        def resolve_coord(val, start, length):
            # val may be '__middle', a float fraction (0..1), or an absolute number
            try:
                if isinstance(val, str) and val.strip() == "__middle":
                    return start + length / 2.0
                f = float(val)
                if 0.0 <= f <= 1.0:
                    return start + f * length
                return start + f
            except Exception:
                return start + length / 2.0

        x = resolve_coord(sx, rect.left, rect.width)
        y = resolve_coord(sy, rect.top, rect.height)

        # pick a direction outward from the center of the element
        center_x = rect.left + rect.width / 2.0
        center_y = rect.top + rect.height / 2.0
        # direction vector from center to spawn point (if spawn at center, choose random)
        dx = x - center_x
        dy = y - center_y
        if abs(dx) < 1e-3 and abs(dy) < 1e-3:
            angle = random.uniform(0, math.tau)
            dx = math.cos(angle)
            dy = math.sin(angle)
        # normalize
        mag = math.hypot(dx, dy)
        if mag == 0:
            nx, ny = 1.0, 0.0
        else:
            nx, ny = dx / mag, dy / mag

        speed = random.uniform(self.speed_min, self.speed_max)
        vx = nx * speed
        vy = ny * speed
        size = random.uniform(self.size_min, self.size_max)
        rot_v = math.radians(random.uniform(self.rot_min, self.rot_max))
        color = random.choice(self._palette) if self._palette else (255, 255, 255, 255)
        shape = random.choice(self.shapes)
        p = {"x": x, "y": y, "vx": vx, "vy": vy, "size": size, "color": color, "rot": 0.0, "rot_v": rot_v, "shape": shape}
        self.particles.append(p)

    def draw(self, surface):
        if not self.element or not self.element.is_visible():
            return
        # draw particles
        for p in self.particles:
            col = p.get("color", (255, 255, 255, 255))
            size = int(max(1, p.get("size", 2)))
            if col[3] >= 255:
                if p["shape"] == "circle":
                    pygame.draw.circle(surface, col[:3], (int(p["x"]), int(p["y"])), size)
                elif p["shape"] == "square":
                    rect = pygame.Rect(int(p["x"] - size / 2), int(p["y"] - size / 2), size, size)
                    pygame.draw.rect(surface, col[:3], rect)
                else:
                    # simple star approximation using polygon
                    pts = []
                    cx = p["x"]
                    cy = p["y"]
                    for i in range(5):
                        a = math.radians(i * 72 + p.get("rot", 0))
                        r = size
                        pts.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
                        a2 = math.radians(i * 72 + 36 + p.get("rot", 0))
                        pts.append((int(cx + math.cos(a2) * (r / 2)), int(cy + math.sin(a2) * (r / 2))))
                    pygame.draw.polygon(surface, col[:3], pts)
            else:
                # draw with alpha on temporary surface
                surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                ox = size * 2
                oy = size * 2
                if p["shape"] == "circle":
                    pygame.draw.circle(surf, col, (ox, oy), size)
                elif p["shape"] == "square":
                    r = pygame.Rect(ox - size // 2, oy - size // 2, size, size)
                    pygame.draw.rect(surf, col, r)
                else:
                    pts = []
                    cx = ox
                    cy = oy
                    for i in range(5):
                        a = math.radians(i * 72 + p.get("rot", 0))
                        r = size
                        pts.append((int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)))
                        a2 = math.radians(i * 72 + 36 + p.get("rot", 0))
                        pts.append((int(cx + math.cos(a2) * (r / 2)), int(cy + math.sin(a2) * (r / 2))))
                    pygame.draw.polygon(surf, col, pts)
                surface.blit(surf, (int(p["x"] - ox), int(p["y"] - oy)))
