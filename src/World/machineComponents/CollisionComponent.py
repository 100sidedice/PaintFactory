from .Component import Component

class CollisionComponent(Component):
    """Component that handles collision detection for a machine."""
    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)
        self.collision_rect = machine.callData("rect")  # pygame.Rect defining the collision area
        self.updateType = "continuous" # Update every tick

    def update(self, items, delta):
        """Check for collisions with items and handle them."""
        tw, th = self.machine.callData("sprite").tile_size
        for item in items:
            item_world_pos = ((item.pos[0] + 0.5) * tw, (item.pos[1] + 0.5) * th)
            if self.collision_rect.collidepoint(item_world_pos):
                self.handle_collision(item, delta)

    def handle_collision(self, item, delta):
        """Handle the collision with the given item."""
        self.machine.pushEvent("collision", {"item": item, "edges": self.get_distance_from_edges(item), "delta": delta}, self.name)


    def get_distance_from_edges(self, item):
        """Return the percentage distance of the item from each edge of the collision rect. [i.e. 3-way conveyors can use this to determine which direction to move the item]"""
        tw, th = self.machine.callData("sprite").tile_size
        item_world_x = (item.pos[0] + 0.5) * tw
        item_world_y = (item.pos[1] + 0.5) * th

        if not self.collision_rect.collidepoint((item_world_x, item_world_y)):
            return None  # Item is not colliding

        left_dist = item_world_x - self.collision_rect.left
        right_dist = self.collision_rect.right - item_world_x
        top_dist = item_world_y - self.collision_rect.top
        bottom_dist = self.collision_rect.bottom - item_world_y

        total_width = self.collision_rect.width
        total_height = self.collision_rect.height

        return {
            "left": left_dist / total_width,
            "right": right_dist / total_width,
            "top": top_dist / total_height,
            "bottom": bottom_dist / total_height
        }