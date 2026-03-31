import pygame


class Camera:
	def __init__(self, viewport_width: int, viewport_height: int, world_width: int | None = None, world_height: int | None = None):
		self.viewport = pygame.Rect(0, 0, viewport_width, viewport_height)
		self.world_width = world_width
		self.world_height = world_height
		# offset is top-left world coordinate visible in the viewport (in world units)
		self.offset = pygame.Vector2(0, 0)
		# zoom: screen_pixels per world_unit (1.0 = 1:1)
		self.zoom = 1.0

	def set_world_size(self, width: int, height: int):
		self.world_width = width
		self.world_height = height

	def fit_to_world(self, world_width: int, world_height: int, allow_zoom_in: bool = False, margin: int = 0):
		"""Compute zoom and offset so the entire world fits inside the viewport.

		If `allow_zoom_in` is False, zoom will not scale above 1.0 (no zoom-in).
		`margin` is in screen pixels to leave around the world when fitting.
		"""
		self.world_width = world_width
		self.world_height = world_height
		if world_width <= 0 or world_height <= 0:
			self.zoom = 1.0
			self.offset = pygame.Vector2(0, 0)
			return

		vw = max(1, self.viewport.width - margin * 2)
		vh = max(1, self.viewport.height - margin * 2)
		# desired zoom such that world fits in viewport: zoom = screen_pixels / world_units
		zoom_x = vw / world_width
		zoom_y = vh / world_height
		self.zoom = min(zoom_x, zoom_y)
		if not allow_zoom_in:
			self.zoom = min(self.zoom, 1.0)

		# compute visible world size (in world units)
		visible_w = self.viewport.width / self.zoom
		visible_h = self.viewport.height / self.zoom

		# center offset so world is centered in viewport
		off_x = (world_width - visible_w) / 2.0
		off_y = (world_height - visible_h) / 2.0
		# clamp
		off_x = max(0.0, min(off_x, max(0.0, world_width - visible_w)))
		off_y = max(0.0, min(off_y, max(0.0, world_height - visible_h)))
		self.offset = pygame.Vector2(off_x, off_y)

	def follow(self, target_rect: pygame.Rect):
		# move viewport center in world coordinates to target center
		# target_rect is in world coordinates
		world_view_w = self.viewport.width / self.zoom
		world_view_h = self.viewport.height / self.zoom
		cx, cy = target_rect.center
		nx = cx - world_view_w / 2.0
		ny = cy - world_view_h / 2.0
		self.offset.x = nx
		self.offset.y = ny
		self._clamp_to_world()

	def update(self, target_rect: pygame.Rect | None = None):
		if target_rect is not None:
			self.follow(target_rect)

	def apply(self, rect: pygame.Rect) -> pygame.Rect:
		# convert world rect to screen rect accounting for zoom
		x = int((rect.x - self.offset.x) * self.zoom)
		y = int((rect.y - self.offset.y) * self.zoom)
		w = int(rect.width * self.zoom)
		h = int(rect.height * self.zoom)
		return pygame.Rect(x, y, w, h)

	def apply_pos(self, pos: tuple[int, int]) -> tuple[int, int]:
		# world -> screen
		x = int((pos[0] - self.offset.x) * self.zoom)
		y = int((pos[1] - self.offset.y) * self.zoom)
		return (x, y)

	def screen_to_world(self, pos: tuple[int, int]) -> tuple[int, int]:
		# screen -> world
		x = pos[0] / self.zoom + self.offset.x
		y = pos[1] / self.zoom + self.offset.y
		return (int(x), int(y))

	def _clamp_to_world(self):
		if self.world_width is None or self.world_height is None:
			return
		# clamp offset so viewport remains inside world bounds (offset is in world units)
		world_view_w = self.viewport.width / self.zoom
		world_view_h = self.viewport.height / self.zoom
		max_x = max(0.0, self.world_width - world_view_w)
		max_y = max(0.0, self.world_height - world_view_h)
		self.offset.x = max(0.0, min(self.offset.x, max_x))
		self.offset.y = max(0.0, min(self.offset.y, max_y))

