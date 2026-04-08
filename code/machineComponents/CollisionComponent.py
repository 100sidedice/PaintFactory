from Component import Component
import pygame

class CollisionComponent(Component):
    """Component that handles collision detection for a machine."""
    def __init__(self, name, machine):
        super().__init__(name, machine)
        self.collision_rect = machine.callData("rect")  # pygame.Rect defining the collision area
        self.updateType = "continuous" # Update every tick

    def update(self, items, delta):
        """Check for collisions with items and handle them."""
        for item in items:
            if self.collision_rect.collidepoint(item.pos):
                self.handle_collision(item)

    def handle_collision(self, item):
        """Handle the collision with the given item."""
        self.machine.pushEvent("collision", {"item": item, "edges": self.get_distance_from_edges(item)}, self.name)

        print(f"Collision detected between {self.machine.name} and {item.name}")


    def get_distance_from_edges(self, item):
        """Return the percentage distance of the item from each edge of the collision rect. [i.e. 3-way conveyors can use this to determine which direction to move the item]"""
        if not self.collision_rect.colliderect(pygame.Rect(item.pos, (1, 1))):
            return None  # Item is not colliding

        left_dist = item.pos[0] - self.collision_rect.left
        right_dist = self.collision_rect.right - item.pos[0]
        top_dist = item.pos[1] - self.collision_rect.top
        bottom_dist = self.collision_rect.bottom - item.pos[1]

        total_width = self.collision_rect.width
        total_height = self.collision_rect.height

        return {
            "left": left_dist / total_width,
            "right": right_dist / total_width,
            "top": top_dist / total_height,
            "bottom": bottom_dist / total_height
        }