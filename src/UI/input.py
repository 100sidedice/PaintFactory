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
    _mouse_wheel = (0, 0)
    _text_input = []

    # lock system
    # key: passcode
    # value: {
    #   "type": "timed"|"unlock",
    #   "time": float,
    #   "elapsed": float,
    #   "on_unlock": callable|None,
    #   "preunlock_called": bool
    # }
    _locks = {}
    _last_update_ms = None

    @classmethod
    def lock(cls, passcode, config, on_unlock=None):
        """Lock input behind a passcode.

        Examples:
            Input.lock("slider-1", {"type": "timed", "time": 0.1}, on_unlock=cb)
            Input.lock("slider-1", {"type": "unlock"}, on_unlock=cb)

        For timed locks, `on_unlock` is called one frame before unlock when possible.
        For manual locks, `on_unlock` is called during `unlock(passcode)`.
        """
        lock_type = (config or {}).get("type", "unlock")
        if lock_type not in {"timed", "unlock"}:
            raise ValueError("lock type must be 'timed' or 'unlock'")

        duration = float((config or {}).get("time", 0.0))
        if duration < 0:
            duration = 0.0

        callback = on_unlock if on_unlock is not None else (config or {}).get("on_unlock")

        cls._locks[passcode] = {
            "type": lock_type,
            "time": duration,
            "elapsed": 0.0,
            "on_unlock": callback,
            "preunlock_called": False,
        }

    @classmethod
    def unlock(cls, passcode):
        """Unlock input for the given passcode."""
        lock_data = cls._locks.get(passcode)
        if lock_data is None:
            return False

        callback = lock_data.get("on_unlock")
        if callable(callback) and lock_data.get("type") == "unlock":
            callback()

        cls._locks.pop(passcode, None)
        return True

    @classmethod
    def is_locked(cls, passcode=None):
        """Return whether input is locked.

        - `passcode=None`: True if any lock exists.
        - with passcode: True if locked and caller is not the lock owner.
        """
        if not cls._locks:
            return False
        if passcode is None:
            return True
        if isinstance(passcode, (list, tuple, set)):
            for code in passcode:
                if code in cls._locks:
                    return False
            return True
        return passcode not in cls._locks

    @classmethod
    def _process_timed_locks(cls, dt):
        to_remove = []
        for passcode, lock_data in list(cls._locks.items()):
            if lock_data.get("type") != "timed":
                continue

            lock_data["elapsed"] += dt
            remaining = lock_data["time"] - lock_data["elapsed"]
            callback = lock_data.get("on_unlock")

            # one-frame-before unlock callback when possible
            if (not lock_data.get("preunlock_called", False)) and callable(callback) and remaining <= max(0.0, dt):
                callback()
                lock_data["preunlock_called"] = True

            if lock_data["elapsed"] >= lock_data["time"]:
                to_remove.append(passcode)

        for passcode in to_remove:
            cls._locks.pop(passcode, None)
    
    @classmethod
    def update(cls, dt=None):
        if dt is None:
            now = pygame.time.get_ticks()
            if cls._last_update_ms is None:
                dt = 0.0
            else:
                dt = max(0.0, (now - cls._last_update_ms) / 1000.0)
            cls._last_update_ms = now

        cls._process_timed_locks(dt)

        cls._key_down.clear()
        cls._key_up.clear()
        cls._mouse_down.clear()
        cls._mouse_up.clear()
        cls._mouse_rel = (0, 0)
        cls._mouse_wheel = (0, 0)
        cls._text_input.clear()
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
            elif event.type == pygame.MOUSEWHEEL:
                cls._mouse_wheel = (event.x, event.y)
            elif event.type == pygame.TEXTINPUT:
                cls._text_input.append(event.text)
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()
    
    @classmethod
    def get_key_down(cls, key, passcode=None):
        if cls.is_locked(passcode):
            return False
        return key in cls._key_down
    
    @classmethod
    def get_key(cls, key, passcode=None):
        if cls.is_locked(passcode):
            return False
        return key in cls._key_held
    
    @classmethod
    def get_key_up(cls, key, passcode=None):
        if cls.is_locked(passcode):
            return False
        return key in cls._key_up
    
    @classmethod
    def get_mouse_button_down(cls, button, passcode=None):
        if cls.is_locked(passcode):
            return False
        return button in cls._mouse_down
    
    @classmethod
    def get_mouse_button(cls, button, passcode=None):
        if cls.is_locked(passcode):
            return False
        return button in cls._mouse_held
    
    @classmethod
    def get_mouse_button_up(cls, button, passcode=None):
        if cls.is_locked(passcode):
            return False
        return button in cls._mouse_up
    
    @classmethod
    def get_mouse_position(cls, passcode=None):
        if cls.is_locked(passcode):
            return cls._mouse_pos
        return cls._mouse_pos
    
    @classmethod
    def get_mouse_motion(cls, passcode=None):
        if cls.is_locked(passcode):
            return (0, 0)
        return cls._mouse_rel

    @classmethod
    def get_text_input(cls, passcode=None):
        if cls.is_locked(passcode):
            return []
        return list(cls._text_input)

    @classmethod
    def consume_text_input(cls, passcode=None):
        if cls.is_locked(passcode):
            return []
        result = list(cls._text_input)
        cls._text_input.clear()
        return result

    @classmethod
    def get_mouse_wheel(cls, passcode=None):
        if cls.is_locked(passcode):
            return (0, 0)
        return cls._mouse_wheel
