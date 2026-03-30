import pygame


class Camera:
	def __init__(self, viewport_width: int, viewport_height: int, world_width: int | None = None, world_height: int | None = None):
		self.viewport = pygame.Rect(0, 0, viewport_width, viewport_height)
		self.world_width = world_width
		self.world_height = world_height
		self.offset = pygame.Vector2(0, 0)

	def set_world_size(self, width: int, height: int):
		self.world_width = width
		self.world_height = height

	def follow(self, target_rect: pygame.Rect):
		self.viewport.center = target_rect.center
		self._clamp_to_world()
		self.offset.x = self.viewport.x
		self.offset.y = self.viewport.y

	def update(self, target_rect: pygame.Rect | None = None):
		if target_rect is not None:
			self.follow(target_rect)

	def apply(self, rect: pygame.Rect) -> pygame.Rect:
		return rect.move(-int(self.offset.x), -int(self.offset.y))

	def apply_pos(self, pos: tuple[int, int]) -> tuple[int, int]:
		return (int(pos[0] - self.offset.x), int(pos[1] - self.offset.y))

	def screen_to_world(self, pos: tuple[int, int]) -> tuple[int, int]:
		return (int(pos[0] + self.offset.x), int(pos[1] + self.offset.y))

	def _clamp_to_world(self):
		if self.world_width is None or self.world_height is None:
			return
		max_x = max(0, self.world_width - self.viewport.width)
		max_y = max(0, self.world_height - self.viewport.height)
		self.viewport.x = max(0, min(self.viewport.x, max_x))
		self.viewport.y = max(0, min(self.viewport.y, max_y))

