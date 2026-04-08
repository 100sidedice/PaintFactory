class Item:
    def __init__(self, name, pos=(0, 0), spriteManager=None, id=0):
        self.name = name
        self.pos = pos
        self.spriteManager = spriteManager
        self.sprite = spriteManager.add_sprite(name, pos, 0)
        self.id = id

    def update(self, delta):
        self.sprite.pos.x = self.pos[0]
        self.sprite.pos.y = self.pos[1]