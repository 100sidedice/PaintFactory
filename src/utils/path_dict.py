class PathDict:
    """Utility helpers for dot-path access in nested dictionaries."""

    @staticmethod
    def get(data, key_path, default=None):
        """Get a value from nested dicts using dot paths (ex: "a.b.c")."""
        if key_path is None or key_path == "":
            return data

        keys = key_path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @staticmethod
    def set(data, key_path, value):
        """Set a value in nested dicts using dot paths, creating dicts as needed."""
        if key_path is None or key_path == "":
            raise ValueError("key_path must be a non-empty string")

        keys = key_path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
