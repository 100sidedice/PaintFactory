from .Component import Component
import pygame

class ClickComponent(Component):
    def __init__(self, name, machine, componentData):
        super().__init__(name, machine, componentData)

        self.input = machine.callData("input")
        self.updateType = "continuous"

        self.double_click_interval = 0.3
        self.last_click_time = 0
        self.last_click_type = None

    def update(self, items, delta):
        if(self.input.is_locked("click")): return


        if (self.input.get_mouse_button_up(1)):
            # Only fire left-click events when the mouse is over this machine's rect
            mouse_pos = self.input.get_mouse_position()
            camera = self.machine.machineManager.tilemap.camera
            world_mouse = camera.screen_to_world(mouse_pos)
            rect = self.machine.callData("rect")
            if rect.collidepoint(world_mouse):
                tileSize = 16
                tw, th = tileSize, tileSize
                x = int(self.machine.pos[0] * tw)
                y = int(self.machine.pos[1] * th)
                eventData = {"button": 1, "pos": pygame.Vector2(x, y)}
                self.machine.pushEvent("i_have_been_clicked_via_a_left_click", eventData, componentName=self.name, component=self)
                if (self.last_click_type == "left" and (pygame.time.get_ticks() / 1000.0 - self.last_click_time) < self.double_click_interval):
                    self.machine.pushEvent("i_have_been_clicked_via_a_left_click_for_the_second_time", eventData, componentName=self.name, component=self)

                self.last_click_time = pygame.time.get_ticks() / 1000.0
                self.last_click_type = "left"


        if (self.input.get_mouse_button_up(3)):
            # Only fire right-click events when the mouse is over this machine's rect
            mouse_pos = self.input.get_mouse_position()
            camera = self.machine.machineManager.tilemap.camera
            world_mouse = camera.screen_to_world(mouse_pos)
            rect = self.machine.callData("rect")
            if rect.collidepoint(world_mouse):
                tileSize = 16
                tw, th = tileSize, tileSize
                x = int(self.machine.pos[0] * tw)
                y = int(self.machine.pos[1] * th)
                eventData = {"button": 3, "pos": pygame.Vector2(x, y)}
                # Notify components and manager about the right-click
                self.machine.pushEvent("i_have_been_clicked_via_a_right_click", eventData, componentName=self.name, component=self)
                # Print to console when this machine is right-clicked
                print(f"Right-clicked machine: {self.machine.name} at {eventData['pos']}")
                if (self.last_click_type == "right" and (pygame.time.get_ticks() / 1000.0 - self.last_click_time) < self.double_click_interval):
                    self.machine.pushEvent("i_have_been_clicked_via_a_right_click_for_the_second_time", eventData, componentName=self.name, component=self)
                self.last_click_time = pygame.time.get_ticks() / 1000.0
                self.last_click_type = "right"