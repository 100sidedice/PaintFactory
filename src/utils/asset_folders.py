import os
import pygame

# Folder asset handlers registry -------------------------------------------------
# Handlers should be sync functions taking (folder_abs_path, folder_rel_path)
# and return a value that will be stored in `self.data[name]`/`self.data[path]`.
FOLDER_HANDLERS = {}


def register_folder_handler(key, func):
    FOLDER_HANDLERS[key] = func


def _load_images_from_folder(folder_abs_path, folder_rel_path):
    """Load image files from a folder and return a dict mapping multiple lookup keys
    to pygame.Surface objects: full relative path, basename, and name without ext.
    """
    out = {} 
    try:
        for entry in sorted(os.listdir(folder_abs_path)):
            full = os.path.join(folder_abs_path, entry)
            if not os.path.isfile(full):
                continue
            lower = entry.lower()
            if not (lower.endswith('.png') or lower.endswith('.jpg') or lower.endswith('.jpeg') or lower.endswith('.gif') or lower.endswith('.bmp')):
                continue
            rel_path = os.path.join(folder_rel_path, entry).replace('\\', '/')
            try:
                surf = pygame.image.load(full).convert_alpha()
            except Exception:
                # skip files that fail to load
                continue

            base = os.path.basename(rel_path)
            name_no_ext = os.path.splitext(base)[0]
            out[rel_path] = surf
            out[base] = surf
            out[name_no_ext] = surf
    except Exception:
        return {}
    return out


# register the built-in image folder handler
register_folder_handler('image', _load_images_from_folder)


def _load_files_list(folder_abs_path, folder_rel_path):
    out = []
    try:
        for entry in sorted(os.listdir(folder_abs_path)):
            full = os.path.join(folder_abs_path, entry)
            if not os.path.isfile(full):
                continue
            out.append(os.path.join(folder_rel_path, entry).replace('\\', '/'))
    except Exception:
        return []
    return out


register_folder_handler('files', _load_files_list)
