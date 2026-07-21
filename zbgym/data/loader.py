"""Data loader for ZBGym JSON databases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DataLoader:
    """Load and manage JSON data files."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """
        Initialize data loader.

        Args:
            data_dir: Directory containing JSON data files.
                     Defaults to zbgym/data/
        """
        if data_dir is None:
            data_dir = Path(__file__).parent
        self.data_dir = Path(data_dir)
        self._cache: dict[str, dict[str, Any]] = {}

    def load(self, name: str, use_cache: bool = True) -> dict[str, Any]:
        """
        Load a JSON data file.

        Args:
            name: Name of the data file (without .json extension)
            use_cache: Whether to cache loaded data

        Returns:
            Dictionary containing the data
        """
        if use_cache and name in self._cache:
            return self._cache[name]

        file_path = self.data_dir / f"{name}.json"
        if not file_path.exists():
            return {}

        with open(file_path) as f:
            data = json.load(f)

        if use_cache:
            self._cache[name] = data

        return data

    def get_characters(self) -> dict[str, Any]:
        """Get all character data."""
        return self.load("characters")

    def get_character(self, char_id: str) -> dict[str, Any] | None:
        """Get a specific character by ID."""
        data = self.get_characters()
        return data.get(char_id)

    def get_weapons(self) -> dict[str, Any]:
        """Get all weapon data."""
        return self.load("weapons")

    def get_weapon(self, weapon_id: str) -> dict[str, Any] | None:
        """Get a specific weapon by ID."""
        data = self.get_weapons()
        return data.get(weapon_id)

    def get_skills(self) -> dict[str, Any]:
        """Get all skill data."""
        return self.load("skills")

    def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        """Get a specific skill by ID."""
        data = self.get_skills()
        return data.get(skill_id)

    def get_maps(self) -> dict[str, Any]:
        """Get all map data."""
        return self.load("maps")

    def get_map(self, map_id: str) -> dict[str, Any] | None:
        """Get a specific map by ID."""
        data = self.get_maps()
        return data.get(map_id)

    def get_damage_types(self) -> dict[str, Any]:
        """Get all damage type definitions."""
        return self.load("damage_types")

    def get_effects(self) -> dict[str, Any]:
        """Get all effect definitions."""
        return self.load("effects")

    def get_projectiles(self) -> dict[str, Any]:
        """Get all projectile definitions."""
        return self.load("projectiles")

    def get_buffs(self) -> dict[str, Any]:
        """Get all buff definitions."""
        return self.load("buffs")

    def get_loot(self) -> dict[str, Any]:
        """Get all loot definitions."""
        return self.load("loot")

    def get_constants(self) -> dict[str, Any]:
        """Get game constants."""
        return self.load("constants")

    def get_movement(self) -> dict[str, Any]:
        """Get movement system configuration."""
        return self.load("movement")

    def get_animations(self) -> dict[str, Any]:
        """Get animation definitions."""
        return self.load("animations")

    # Aliases for load_* compatibility
    load_characters = get_characters
    load_character = get_character
    load_weapons = get_weapons
    load_weapon = get_weapon
    load_skills = get_skills
    load_skill = get_skill
    load_maps = get_maps
    load_map = get_map
    load_damage_types = get_damage_types
    load_effects = get_effects
    load_projectiles = get_projectiles
    load_buffs = get_buffs
    load_loot = get_loot
    load_constants = get_constants
    load_movement = get_movement
    load_animations = get_animations

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._cache.clear()

    def reload(self) -> None:
        """Reload all data files."""
        self.clear_cache()


# Global data loader instance
_global_loader: DataLoader | None = None


def get_loader() -> DataLoader:
    """Get the global data loader instance."""
    global _global_loader
    if _global_loader is None:
        _global_loader = DataLoader()
    return _global_loader
