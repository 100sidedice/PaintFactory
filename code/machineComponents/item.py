import pygame

class Item:
    def __init__(self, name, texture, itemGroup, rotation: int = 0):
        self.name = name
        # store discrete rotation (0..3) and rotate texture accordingly
        self.rotation = rotation % 4

        texture = pygame.transform.rotate(texture, self.rotation * 90)
        
        self.texture = texture
        self.pos = pygame.Vector2(0, 0)
        self.itemGroup = itemGroup

    def update(self, dt):
        pass

    def draw(self, surface, camera=None):
        if camera is not None:
            try:
                surface_pos = camera.apply_pos((self.pos.x, self.pos.y))
            except Exception:
                surface_pos = (int(self.pos.x - camera.offset.x), int(self.pos.y - camera.offset.y))
        else:
            surface_pos = (int(self.pos.x), int(self.pos.y))

        surface.blit(self.texture, surface_pos)

    def onAction(self, actionType):
        if actionType == "remove":
            self.itemGroup.remove(self)