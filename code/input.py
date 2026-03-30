import pygame

class Input:
    _key_down = set()
    _key_held = set()
    _key_up = set()
    _mouse_down = set()
    _mouse_held = set()
    _mouse_up = set()
    _mouse_pos = (0, 0)
    _mouse_rel = (0, 0)
    
    @classmethod
    def update(cls):
        cls._key_down.clear()
        cls._key_up.clear()
        cls._mouse_down.clear()
        cls._mouse_up.clear()
        cls._mouse_rel = (0, 0)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                cls._key_down.add(event.key)
                cls._key_held.add(event.key)
            elif event.type == pygame.KEYUP:
                cls._key_up.add(event.key)
                cls._key_held.discard(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                cls._mouse_down.add(event.button)
                cls._mouse_held.add(event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                cls._mouse_up.add(event.button)
                cls._mouse_held.discard(event.button)
            elif event.type == pygame.MOUSEMOTION:
                cls._mouse_pos = event.pos
                cls._mouse_rel = event.rel
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()
    
    @classmethod
    def get_key_down(cls, key):
        return key in cls._key_down
    
    @classmethod
    def get_key(cls, key):
        return key in cls._key_held
    
    @classmethod
    def get_key_up(cls, key):
        return key in cls._key_up
    
    @classmethod
    def get_mouse_button_down(cls, button):
        return button in cls._mouse_down
    
    @classmethod
    def get_mouse_button(cls, button):
        return button in cls._mouse_held
    
    @classmethod
    def get_mouse_button_up(cls, button):
        return button in cls._mouse_up
    
    @classmethod
    def get_mouse_position(cls):
        return cls._mouse_pos
    
    @classmethod
    def get_mouse_motion(cls):
        return cls._mouse_rel
