import json
from ..utils.path_dict import PathDict

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
        return PathDict.get(self.state, key_path, default)
    
    def set(self, key_path, value):
        """Set a value in the game state using a key path, creating nested dicts as needed."""
        PathDict.set(self.state, key_path, value)