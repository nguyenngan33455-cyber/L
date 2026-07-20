"""Tests for data loader module."""

import json
import tempfile
from pathlib import Path

import pytest

from zbgym.data.loader import DataLoader, get_loader


class TestDataLoader:
    """Test DataLoader class."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            
            # Create test data files
            (data_dir / "characters.json").write_text(json.dumps({
                "soldier": {"name": "Soldier", "health": 100},
                "scout": {"name": "Scout", "health": 80}
            }))
            
            (data_dir / "weapons.json").write_text(json.dumps({
                "rifle": {"name": "Rifle", "damage": 20},
                "pistol": {"name": "Pistol", "damage": 10}
            }))
            
            (data_dir / "skills.json").write_text(json.dumps({
                "heal": {"name": "Heal", "cooldown": 5.0},
                "shield": {"name": "Shield", "cooldown": 10.0}
            }))
            
            yield data_dir

    def test_load_existing_file(self, temp_data_dir):
        """Test loading an existing data file."""
        loader = DataLoader(temp_data_dir)
        data = loader.load("characters")
        
        assert "soldier" in data
        assert data["soldier"]["name"] == "Soldier"
        assert data["soldier"]["health"] == 100

    def test_load_nonexistent_file(self, temp_data_dir):
        """Test loading a non-existent file returns empty dict."""
        loader = DataLoader(temp_data_dir)
        data = loader.load("nonexistent")
        
        assert data == {}

    def test_caching(self, temp_data_dir):
        """Test that data is cached."""
        loader = DataLoader(temp_data_dir)
        
        # First load
        data1 = loader.load("characters")
        
        # Modify file
        (temp_data_dir / "characters.json").write_text(json.dumps({"modified": True}))
        
        # Second load should return cached
        data2 = loader.load("characters", use_cache=True)
        
        assert "modified" not in data2
        assert "soldier" in data2

    def test_cache_disabled(self, temp_data_dir):
        """Test loading without cache."""
        loader = DataLoader(temp_data_dir)
        
        # First load
        data1 = loader.load("characters")
        
        # Modify file
        (temp_data_dir / "characters.json").write_text(json.dumps({"modified": True}))
        
        # Second load without cache should return new data
        data2 = loader.load("characters", use_cache=False)
        
        assert "modified" in data2

    def test_clear_cache(self, temp_data_dir):
        """Test clearing cache."""
        loader = DataLoader(temp_data_dir)
        
        # Load data
        loader.load("characters")
        
        # Clear cache
        loader.clear_cache()
        
        # Modify file
        (temp_data_dir / "characters.json").write_text(json.dumps({"modified": True}))
        
        # Load again should get new data
        data = loader.load("characters")
        assert "modified" in data

    def test_reload(self, temp_data_dir):
        """Test reload method."""
        loader = DataLoader(temp_data_dir)
        
        # Load data
        loader.load("characters")
        
        # Modify file
        (temp_data_dir / "characters.json").write_text(json.dumps({"modified": True}))
        
        # Reload
        loader.reload()
        
        # Load again should get new data
        data = loader.load("characters")
        assert "modified" in data

    def test_get_characters(self, temp_data_dir):
        """Test get_characters helper."""
        loader = DataLoader(temp_data_dir)
        data = loader.get_characters()
        
        assert "soldier" in data
        assert "scout" in data

    def test_get_character(self, temp_data_dir):
        """Test get_character helper."""
        loader = DataLoader(temp_data_dir)
        
        soldier = loader.get_character("soldier")
        assert soldier is not None
        assert soldier["name"] == "Soldier"
        
        nonexistent = loader.get_character("nonexistent")
        assert nonexistent is None

    def test_get_weapons(self, temp_data_dir):
        """Test get_weapons helper."""
        loader = DataLoader(temp_data_dir)
        data = loader.get_weapons()
        
        assert "rifle" in data
        assert "pistol" in data

    def test_get_weapon(self, temp_data_dir):
        """Test get_weapon helper."""
        loader = DataLoader(temp_data_dir)
        
        rifle = loader.get_weapon("rifle")
        assert rifle is not None
        assert rifle["damage"] == 20

    def test_get_skills(self, temp_data_dir):
        """Test get_skills helper."""
        loader = DataLoader(temp_data_dir)
        data = loader.get_skills()
        
        assert "heal" in data
        assert "shield" in data

    def test_get_skill(self, temp_data_dir):
        """Test get_skill helper."""
        loader = DataLoader(temp_data_dir)
        
        heal = loader.get_skill("heal")
        assert heal is not None
        assert heal["cooldown"] == 5.0

    def test_get_maps_empty(self, temp_data_dir):
        """Test get_maps returns empty dict if no maps."""
        loader = DataLoader(temp_data_dir)
        data = loader.get_maps()
        
        assert data == {}

    def test_get_projectiles(self, temp_data_dir):
        """Test get_projectiles."""
        (temp_data_dir / "projectiles.json").write_text(json.dumps({
            "bullet": {"speed": 1000}
        }))
        
        loader = DataLoader(temp_data_dir)
        data = loader.get_projectiles()
        
        assert "bullet" in data

    def test_get_effects(self, temp_data_dir):
        """Test get_effects."""
        (temp_data_dir / "effects.json").write_text(json.dumps({
            "burn": {"duration": 3.0}
        }))
        
        loader = DataLoader(temp_data_dir)
        data = loader.get_effects()
        
        assert "burn" in data

    def test_get_buffs(self, temp_data_dir):
        """Test get_buffs."""
        (temp_data_dir / "buffs.json").write_text(json.dumps({
            "damage_boost": {"modifier": 1.25}
        }))
        
        loader = DataLoader(temp_data_dir)
        data = loader.get_buffs()
        
        assert "damage_boost" in data

    def test_get_loot(self, temp_data_dir):
        """Test get_loot."""
        (temp_data_dir / "loot.json").write_text(json.dumps({
            "health_pack": {"healing": 50}
        }))
        
        loader = DataLoader(temp_data_dir)
        data = loader.get_loot()
        
        assert "health_pack" in data


class TestGlobalLoader:
    """Test global loader singleton."""

    def test_get_loader_returns_singleton(self):
        """Test that get_loader returns the same instance."""
        loader1 = get_loader()
        loader2 = get_loader()
        
        assert loader1 is loader2

    def test_global_loader_works(self):
        """Test global loader can load data."""
        loader = get_loader()
        
        # Should not raise even if files don't exist
        data = loader.get_characters()
        assert isinstance(data, dict)
