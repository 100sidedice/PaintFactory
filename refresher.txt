""" Pygame start """
    import pygame
    import sys

    # 1. Initialize Pygame
    pygame.init()

    # 2. Setup the Display
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("My Pygame Refresher")

    # 3. Setup Clock for Frame Rate
    clock = pygame.time.Clock()
    FPS = 60

    # 4. Main Game Loop
    running = True
    while running:
        # Handle Events (Input)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Game Logic (Update) goes here

        # Rendering (Draw)
        screen.fill((30, 30, 30))  # Clear screen with a dark gray (RGB)
        
        # Update the Display
        pygame.display.flip()
        
        # Cap the Frame Rate
        clock.tick(FPS)

    # 5. Clean Up
    pygame.quit()
    sys.exit()


"""Images"""
    # Load standard image (JPG, etc.)
    player_img = pygame.image.load('assets/player.jpg').convert()

    # Load image with transparency (PNG)
    player_img = pygame.image.load('assets/player.png').convert_alpha()

    # Drawing it in your loop
    screen.blit(player_img, (x, y))

    # Replace 1 color with another
    def replace_color(surface, old_color, new_color):
        # Create a pixel array of the surface
        pixels = pygame.PixelArray(surface)
        # Replace the color
        pixels.replace(old_color, new_color)
        # Delete the array to unlock the surface
        del pixels 
        return surface

    # Masking
    # Pre-create one reusable surface
    tint_surf = pygame.Surface(base_img.get_size()).convert_alpha()

    for entity in all_entities:
        # 1. Clear the reusable surface with the entity's unique color
        tint_surf.fill(entity.unique_color)
        
        # 2. Blit the white base image onto the tint using MULTIPLY
        # This keeps the original shape/alpha but applies the new color
        tint_surf.blit(base_img, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # 3. Draw the resulting tinted sprite to the screen
        screen.blit(tint_surf, entity.pos)


"""Sprites"""
    class Player(pygame.sprite.Sprite):
        def __init__(self, color, x, y):
            # 1. Initialize the parent Sprite class
            super().__init__()
            
            # 2. Define the appearance (Surface)
            self.image = pygame.Surface((50, 50))
            self.image.fill(color)
            
            # 3. Define the position (Rect)
            # We use the surface's rect to handle movement and collisions
            self.rect = self.image.get_rect()
            self.rect.topleft = (x, y)
            
            # Custom attributes (speed, health, etc.)
            self.speed = 5

        def update(self):
            # 4. Define behavior (e.g., move right)
            self.rect.x += self.speed
            
            # Simple screen wrapping
            if self.rect.left > 800:
                self.rect.right = 0


"""Sprite groups"""
    # Create the group
    all_sprites = pygame.sprite.Group()

    # Create an instance and add it to the group
    player = Player((0, 255, 0), 100, 100)
    all_sprites.add(player)

    # Inside your Main Loop:
    all_sprites.update()          # Calls update() on every sprite in the group
    all_sprites.draw(screen)      # Blits every sprite's image at its rect position


"""Collision"""
    # Check if player hits a goal
    if player.rect.colliderect(goal_rect):
        print("Level Complete!")

    # Returns a LIST of all enemy sprites the player is touching
    hits = pygame.sprite.spritecollide(player, enemy_group, False)

    for enemy in hits:
        player.health -= 10
        print("Ouch!")


"""Saving data"""
    import json

    # Your game data
    data = {
        "player_name": "Hero",
        "score": 1500,
        "inventory": ["sword", "health_potion"],
        "position": {"x": 100, "y": 250}
    }

    # Save to a file
    with open("save_data.json", "w") as f:
        json.dump(data, f, indent=4)


"""Loading data"""
    # Load from a file
    try:
        with open("save_data.json", "r") as f:
            loaded_data = json.load(f)
        print(loaded_data["player_name"])  # Outputs: Hero
    except FileNotFoundError:
        print("No save file found!")


""" Signals """
    class Signal:
        def __init__(self):
            self._listeners = []

        def connect(self, callback):
            """Add a function to be called when the signal emits."""
            if callback not in self._listeners:
                self._listeners.append(callback)

        def emit(self, *args, **kwargs):
            """Call all connected functions with any provided data."""
            for listener in self._listeners:
                listener(*args, **kwargs)


""" Events """
    # Create the event object with custom data attributes
    win_event = pygame.event.Event(LEVEL_UP, score=100, message="You Win!")

    # Send it to the queue
    pygame.event.post(win_event)

    # Loop example
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == ENEMY_SPAWN:
            spawn_new_enemy()
            
        if event.type == LEVEL_UP:
            print(f"Stats: {event.score}, {event.message}")


""" Decorators """
    # Example 1 - Skip logic if paused
    is_paused = False

    def skip_if_paused(func):
        def wrapper(*args, **kwargs):
            if not is_paused:
                return func(*args, **kwargs)
            # Else: do nothing
        return wrapper

    @skip_if_paused
    def update_player_animation():
        # Logic to move frames...
        pass

    # Example 2 - Bounding HP value
    class Player:
        def __init__(self):
            self._hp = 100  # The actual data (private-ish)

        @property
        def hp(self):
            return self._hp

        @hp.setter
        def hp(self, value):
            # Constrain health between 0 and 100 automatically
            if value < 0:
                self._hp = 0
            elif value > 100:
                self._hp = 100
            else:
                self._hp = value
            
            print(f"HP set to: {self._hp}")

    # Usage:
    p = Player()
    p.hp -= 200    # Tries to set to -100
    print(p.hp)    # Result is 0 (Logic handled by setter!)

    # Example 3 - Game states
    class GameStateManager:
        def __init__(self, initial_state):
            self._state = None
            self.state = initial_state  # Triggers the @property setter

        @property
        def state(self):
            return self._state

        @state.setter
        def state(self, new_state):
            # 1. Run 'Exit' logic for the old state (e.g., stopping music)
            if self._state is not None:
                self._state.exit()
                
            # 2. Switch the state
            self._state = new_state
            
            # 3. Run 'Enter' logic for the new state (e.g., loading level)
            self._state.enter()

        def update(self):
            self._state.update()

        def draw(self, screen):
            self._state.draw(screen)


""" Subsurfaces """
    # Example 1: Spritesheet splitting

    # Load the big sheet once
    sheet = pygame.image.load('warrior_sheet.png').convert_alpha()

    # Create subsurfaces for specific frames
    # .subsurface((x, y, width, height))
    idle_frame = sheet.subsurface((0, 0, 32, 32))
    walk_frame = sheet.subsurface((32, 0, 32, 32))
    attack_frame = sheet.subsurface((64, 0, 32, 32))

    # Drawing them is the same as any other image
    screen.blit(walk_frame, (100, 100))

    # Example 2: Camera logic

    # 'world_surface' is your giant pre-rendered map
    camera_rect = pygame.Rect(player.x - 400, player.y - 300, 800, 600)

    # Clamp the rect so it doesn't go off the map edges
    camera_rect.clamp_ip(world_surface.get_rect())

    # Create a 'view' of just the area around the player
    visible_area = world_surface.subsurface(camera_rect)

    # Draw only that piece to the screen
    screen.blit(visible_area, (0, 0))


