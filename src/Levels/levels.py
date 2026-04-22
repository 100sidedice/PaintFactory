"""Level helpers aware of the game's preloaded asset dictionary.

This module provides functions to access level definitions. Prefer calling
these with the `preloaded_assets` mapping created by the game's
`preloadAssets()` (available as `Game.data`). If `preloaded_assets` is not
provided the functions will fall back to reading `data/levels.json` from
disk.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


def _from_preloaded(preloaded_assets: Optional[dict]) -> Optional[List[Dict[str, Any]]]:
    if not preloaded_assets:
        return None
    # preload stores both by name and by path
    return preloaded_assets.get("levels") or preloaded_assets.get("data/levels.json")


def load_levels(preloaded_assets: Optional[dict] = None) -> List[Dict[str, Any]]:
    """Return the list of levels.

    If `preloaded_assets` is provided, prefer the in-memory copy loaded at
    startup. Otherwise read `data/levels.json` from disk.
    """
    from_pre = _from_preloaded(preloaded_assets)
    if from_pre is not None:
        # normalise on a list of level dicts
        if isinstance(from_pre, list):
            return from_pre
        if isinstance(from_pre, dict):
            if "levels" in from_pre and isinstance(from_pre["levels"], list):
                return from_pre["levels"]
            # single-level object -> wrap in list
            return [from_pre]
    path = os.path.join(os.path.dirname(__file__), "levels.json")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return []
    return data.get("levels", [])


def get_level(level_id: Optional[int] = None, preloaded_assets: Optional[dict] = None) -> Optional[Dict[str, Any]]:
    levels = load_levels(preloaded_assets)
    if not levels:
        return None
    if level_id is None:
        # Prefer explicit level id 1 if present, otherwise fall back to first
        for lv in levels:
            try:
                if int(lv.get("id", -9999)) == 1:
                    return lv
            except Exception:
                continue
        return levels[0]
    for lv in levels:
        if lv.get("id") == level_id:
            return lv
    return None


def get_goal(level_id: Optional[int] = None, preloaded_assets: Optional[dict] = None) -> List[Dict[str, Any]]:
    lv = get_level(level_id, preloaded_assets=preloaded_assets)
    if not lv:
        return []
    return lv.get("goal", [])


def get_machine_limit(level_id: Optional[int], machine_type: str, preloaded_assets: Optional[dict] = None, default: Optional[int] = None) -> Optional[int]:
    lv = get_level(level_id, preloaded_assets=preloaded_assets)
    if not lv:
        return default
    return lv.get("machine_limits", {}).get(machine_type, default)
