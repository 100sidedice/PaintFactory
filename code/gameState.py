import json

class GameState:
    def __init__(self, data):
        self.data = data

        self.state = {
            "settings":{
                "max_items": 1000
            },
            "machines":{
                "conveyor_speed" : 1.0,
                "spawner_rate" : 1.0,
            },
            "inventory": {
                "money": 0
            }
        }

    def save(self, filepath="save.json"):
        """Save the current game state to a file."""
        with open(filepath, "w") as f:
            json.dump(self.state, f)

    def load(self, filepath="save.json"):
        """Load game state from a file."""
        with open(filepath, "r") as f:
            self.state = json.load(f)

    def get(self, key_path, default=None):
        """Get a value from the game state using a key path, e.g. "machines.machine1.pos"."""
        keys = key_path.split(".")
        current = self.state
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def set(self, key_path, value):
        """Set a value in the game state using a key path, creating nested dicts as needed."""
        keys = key_path.split(".")
        current = self.state
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value