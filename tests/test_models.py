"""
test_models.py

Description: Tests for data models
"""

import pytest
from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.models.validation_list import ValidationList


class TestChestEntry:
    """Tests for the ChestEntry class."""
    
    def test_initialization(self) -> None:
        """Test initialization of ChestEntry."""
        # Create a basic entry
        entry = ChestEntry(
            chest_type="Cobra Chest",
            player="Engelchen",
            source="Level 15 Crypt"
        )
        
        # Check fields
        assert entry.chest_type == "Cobra Chest"
        assert entry.player == "Engelchen"
        assert entry.source == "Level 15 Crypt"
        
        # Check original values are set
        assert entry.original_chest_type == "Cobra Chest"
        assert entry.original_player == "Engelchen"
        assert entry.original_source == "Level 15 Crypt"
        
        # Check no corrections or errors
        assert not entry.has_corrections()
        assert not entry.has_validation_errors()
    
    def test_apply_correction(self) -> None:
        """Test applying a correction to an entry."""
        entry = ChestEntry(
            chest_type="Rare Chest of VVealth",
            player="GUARDIENOfTHUNDER",
            source="Level 15 epic Crypt"
        )
        
        # Apply corrections
        entry.apply_correction("chest_type", "Rare Chest of Wealth")
        entry.apply_correction("player", "GUARDIENofTHUNDER")
        
        # Check corrected values
        assert entry.chest_type == "Rare Chest of Wealth"
        assert entry.player == "GUARDIENofTHUNDER"
        assert entry.source == "Level 15 epic Crypt"
        
        # Check original values are preserved
        assert entry.original_chest_type == "Rare Chest of VVealth"
        assert entry.original_player == "GUARDIENOfTHUNDER"
        assert entry.original_source == "Level 15 epic Crypt"
        
        # Check corrections list
        assert entry.has_corrections()
        assert len(entry.corrections) == 2
        assert ("chest_type", "Rare Chest of VVealth", "Rare Chest of Wealth") in entry.corrections
        assert ("player", "GUARDIENOfTHUNDER", "GUARDIENofTHUNDER") in entry.corrections
    
    def test_from_text(self) -> None:
        """Test creating a ChestEntry from text."""
        text = "Cobra Chest\nFrom: Engelchen\nSource: Level 15 Crypt"
        entry = ChestEntry.from_text(text)
        
        assert entry.chest_type == "Cobra Chest"
        assert entry.player == "Engelchen"
        assert entry.source == "Level 15 Crypt"
    
    def test_to_text(self) -> None:
        """Test converting a ChestEntry to text."""
        entry = ChestEntry(
            chest_type="Cobra Chest",
            player="Engelchen",
            source="Level 15 Crypt"
        )
        
        text = entry.to_text()
        assert text == "Cobra Chest\nFrom: Engelchen\nSource: Level 15 Crypt"
        
        # Test with player without "From:" prefix
        entry = ChestEntry(
            chest_type="Cobra Chest",
            player="From: Engelchen",
            source="Level 15 Crypt"
        )
        
        text = entry.to_text()
        assert text == "Cobra Chest\nFrom: Engelchen\nSource: Level 15 Crypt"


class TestCorrectionRule:
    """Tests for the CorrectionRule class."""
    
    def test_initialization(self) -> None:
        """Test initialization of CorrectionRule."""
        rule = CorrectionRule(
            from_text="Krimelmonster",
            to_text="Krümelmonster"
        )
        
        assert rule.from_text == "Krimelmonster"
        assert rule.to_text == "Krümelmonster"
        assert rule.rule_type == "exact"
        assert rule.priority == 0
        assert rule.field_target is None
    
    def test_apply_to_text(self) -> None:
        """Test applying a rule to text."""
        rule = CorrectionRule(
            from_text="VV",
            to_text="W"
        )
        
        corrected, applied = rule.apply_to_text("Rare Chest of VVealth")
        assert corrected == "Rare Chest of Wealth"
        assert applied is True
        
        corrected, applied = rule.apply_to_text("Cobra Chest")
        assert corrected == "Cobra Chest"
        assert applied is False


class TestValidationList:
    """Tests for the ValidationList class."""
    
    def test_initialization(self) -> None:
        """Test initialization of ValidationList."""
        player_list = ValidationList(
            list_type="player",
            entries=["Engelchen", "Sir Met", "Moony"]
        )
        
        assert player_list.list_type == "player"
        assert len(player_list.entries) == 3
        assert "Engelchen" in player_list.entries
        assert "Sir Met" in player_list.entries
        assert "Moony" in player_list.entries
    
    def test_add_remove_entry(self) -> None:
        """Test adding and removing entries."""
        player_list = ValidationList(list_type="player")
        
        # Add entries
        player_list.add_entry("Engelchen")
        player_list.add_entry("Sir Met")
        
        assert len(player_list.entries) == 2
        assert "Engelchen" in player_list.entries
        assert "Sir Met" in player_list.entries
        
        # Remove entry
        result = player_list.remove_entry("Engelchen")
        assert result is True
        assert len(player_list.entries) == 1
        assert "Engelchen" not in player_list.entries
        
        # Remove non-existent entry
        result = player_list.remove_entry("NonExistent")
        assert result is False
        assert len(player_list.entries) == 1
    
    def test_is_valid(self) -> None:
        """Test validation against the list."""
        player_list = ValidationList(
            list_type="player",
            entries=["Engelchen", "Sir Met", "Moony"]
        )
        
        assert player_list.is_valid("Engelchen") is True
        assert player_list.is_valid("Unknown") is False 