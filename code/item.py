class Item:
    def __init__(self, name, pos=(0, 0), rotation=0):
        self.name = name
        self.pos = pos
        self.rotation = rotation

    def update(self, delta):
        pass