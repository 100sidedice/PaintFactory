import pygame

class Timer:
    """Flexible timer supporting multiple attachable callbacks.

    - Can be constructed with no arguments and configured later.
    - Attach callbacks that run once when the timer finishes (non-repeating),
      or attach loop callbacks that run every time the timer reaches its
      duration when `repeat=True`.

    Example:
        timer = Timer(2.0, repeat=True)
        timer.add_loop_callback(lambda: print("looped"))
        timer.add_finish_callback(lambda: print("finished"))

    Methods:
        - update(dt): advance timer and call callbacks as appropriate
        - set(duration, repeat=False, reset=True): configure timer
        - add_finish_callback(cb), add_loop_callback(cb)
        - remove_finish_callback(cb), remove_loop_callback(cb)
        - reset(), stop(), is_active()
    """

    def __init__(self, duration=None, callback=None, repeat=False):
        # Duration in seconds. If None, timer starts inactive until set().
        self.duration = float(duration) if duration is not None else None
        self.repeat = bool(repeat)
        self.elapsed = 0.0
        self.active = False if duration is None else True

        # support multiple callbacks
        self._finish_callbacks = []
        self._loop_callbacks = []
        if callback is not None:
            # legacy single callback attaches as a finish callback
            self._finish_callbacks.append(callback)

    def set(self, duration, repeat=False, reset=True):
        """Configure the timer. If `reset` is True, elapsed is zeroed and
        timer becomes active."""
        self.duration = float(duration)
        self.repeat = bool(repeat)
        if reset:
            self.reset()
        else:
            self.active = True

    def add_finish_callback(self, cb):
        if callable(cb):
            self._finish_callbacks.append(cb)

    def add_loop_callback(self, cb):
        if callable(cb):
            self._loop_callbacks.append(cb)

    def remove_finish_callback(self, cb):
        try:
            self._finish_callbacks.remove(cb)
        except ValueError:
            pass

    def remove_loop_callback(self, cb):
        try:
            self._loop_callbacks.remove(cb)
        except ValueError:
            pass

    def clear_callbacks(self):
        self._finish_callbacks.clear()
        self._loop_callbacks.clear()

    def update(self, dt):
        if not self.active or self.duration is None:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            # call loop callbacks first (they run every interval)
            for cb in list(self._loop_callbacks):
                try:
                    cb()
                except Exception:
                    pass

            if self.repeat:
                # subtract duration but keep overflow to preserve timing
                self.elapsed -= self.duration
            else:
                # call finish callbacks and deactivate
                for cb in list(self._finish_callbacks):
                    try:
                        cb()
                    except Exception:
                        pass
                self.active = False

    def reset(self):
        self.elapsed = 0.0
        if self.duration is not None:
            self.active = True

    def stop(self):
        self.active = False

    def is_active(self):
        return bool(self.active)