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


        if (self.input.get_mouse_up(1)):
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


        if (self.input.get_mouse_up(3)):
            tileSize = 16
            tw, th = tileSize, tileSize
            x = int(self.machine.pos[0] * tw)
            y = int(self.machine.pos[1] * th)
            eventData = {"button": 3, "pos": pygame.Vector2(x, y)}
            self.machine.pushEvent("i_have_been_clicked_via_a_right_click", eventData, componentName=self.name, component=self)
            if (self.last_click_type == "right" and (pygame.time.get_ticks() / 1000.0 - self.last_click_time) < self.double_click_interval):
                self.machine.pushEvent("i_have_been_clicked_via_a_right_click_for_the_second_time", eventData, componentName=self.name, component=self)
            self.last_click_time = pygame.time.get_ticks() / 1000.0
            self.last_click_type = "right"