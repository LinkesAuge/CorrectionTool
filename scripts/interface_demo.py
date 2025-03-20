#!/usr/bin/env python3
"""
interface_demo.py

Description: Demonstration of interface-based architecture
Usage:
    python interface_demo.py
"""

import configparser
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Print a message directly to stdout to verify output is working
print("Starting interface demo...")


# Define the interface for ConfigManager (minimal version)
class IConfigManager(ABC):
    @abstractmethod
    def get_str(self, section: str, key: str, fallback: str = "") -> str:
        pass

    @abstractmethod
    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        pass

    @abstractmethod
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        pass


# Simple implementation of ConfigManager
class ConfigManager(IConfigManager):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config["General"] = {"app_name": "Interface Demo App"}
        self.config["Validation"] = {"case_sensitive": "false", "fuzzy_threshold": "50"}

    def get_str(self, section: str, key: str, fallback: str = "") -> str:
        return self.config.get(section, key, fallback=fallback)

    def get_bool(self, section: str, key: str, fallback: bool = False) -> bool:
        value = self.config.get(section, key, fallback=str(fallback))
        return value.lower() in ["true", "1", "yes", "y", "t"]

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        try:
            return float(self.config.get(section, key, fallback=str(fallback)))
        except ValueError:
            return fallback


# Simple FuzzyMatcher class
class FuzzyMatcher:
    def __init__(self, threshold=0.5):
        self.threshold = threshold

    def find_best_match(self, text: str, candidates: List[str]) -> Tuple[str, float]:
        if not candidates:
            return "", 0.0

        # Very simple fuzzy matching for demo purposes
        best_score = 0.0
        best_match = ""
        for candidate in candidates:
            # Count matching characters in same position
            match_count = sum(1 for a, b in zip(text.lower(), candidate.lower()) if a == b)
            max_len = max(len(text), len(candidate))
            score = match_count / max_len if max_len > 0 else 0.0

            if score > best_score:
                best_score = score
                best_match = candidate

        return best_match, best_score


# ValidationList using the interfaces
class ValidationList:
    def __init__(
        self,
        list_type: str = "player",
        entries: Optional[List[str]] = None,
        name: str = "Default",
        use_fuzzy_matching: bool = False,
        config_manager: Optional[IConfigManager] = None,
    ):
        self.list_type = list_type
        self.entries: Set[str] = set()
        self.name = name
        self._use_fuzzy_matching = use_fuzzy_matching
        self._config_manager = config_manager

        # Initialize fuzzy matcher with default threshold
        threshold = 0.5  # Default threshold - lowered to make demo match work

        # If config_manager is provided, use it to get threshold
        if self._config_manager:
            threshold = (
                self._config_manager.get_float("Validation", "fuzzy_threshold", fallback=50) / 100.0
            )

        self._fuzzy_matcher = FuzzyMatcher(threshold=threshold)

        # Add entries if provided
        if entries:
            for entry in entries:
                self.add_entry(entry)

    @property
    def use_fuzzy_matching(self) -> bool:
        return self._use_fuzzy_matching

    @use_fuzzy_matching.setter
    def use_fuzzy_matching(self, value: bool) -> None:
        self._use_fuzzy_matching = value

    def add_entry(self, entry: str) -> None:
        self.entries.add(entry.strip())

    def count(self) -> int:
        return len(self.entries)

    def is_valid(self, entry: str) -> Tuple[bool, float, Optional[str]]:
        if not entry:
            return False, 0.0, None

        # Default values
        case_sensitive = False

        # Get config settings if available
        if self._config_manager:
            case_sensitive = self._config_manager.get_bool(
                "Validation", "case_sensitive", fallback=False
            )

        # Normalize entry for comparison
        normalized_entry = entry.strip()

        # First try exact match (case sensitive or insensitive)
        for valid_entry in self.entries:
            # For exact matching
            if case_sensitive:
                if normalized_entry == valid_entry:
                    return True, 1.0, None
            else:
                if normalized_entry.lower() == valid_entry.lower():
                    return True, 1.0, None

        # If no exact match and fuzzy matching is enabled, try fuzzy matching
        if self._use_fuzzy_matching and self.entries:
            # Convert entries to list for fuzzy matching
            entries_list = list(self.entries)

            # Find best match
            best_match, score = self._fuzzy_matcher.find_best_match(normalized_entry, entries_list)

            # If score exceeds threshold, consider it valid
            if score >= self._fuzzy_matcher.threshold:
                return True, score, best_match

        # No match found
        return False, 0.0, None


def run_demo():
    """
    Run a demonstration of interface-based architecture.
    """
    print("Running interface demo...")

    # Create ConfigManager using the interface
    config: IConfigManager = ConfigManager()
    print(f"Created ConfigManager instance: {config}")

    # Use the interface methods
    app_name = config.get_str("General", "app_name", "Default App")
    print(f"App name from config: {app_name}")

    # Create a ValidationList using the interface
    player_list = ValidationList(
        list_type="player",
        entries=["Player1", "Player2", "Player3"],
        name="Demo Player List",
        use_fuzzy_matching=True,
        config_manager=config,  # Pass the interface instead of concrete class
    )
    print(f"Created ValidationList with {player_list.count()} entries")
    print(f"Fuzzy threshold: {player_list._fuzzy_matcher.threshold}")

    # Test validation
    test_name = "Player1"
    is_valid, confidence, matched = player_list.is_valid(test_name)
    print(f"Validation test for '{test_name}': valid={is_valid}, confidence={confidence:.2f}")

    # Test fuzzy matching
    test_name = "Playr1"  # Misspelled
    player_list.use_fuzzy_matching = True
    is_valid, confidence, matched = player_list.is_valid(test_name)
    print(
        f"Fuzzy match test for '{test_name}': valid={is_valid}, confidence={confidence:.2f}, matched={matched}"
    )

    print("Interface-based architecture demo completed successfully")


if __name__ == "__main__":
    run_demo()
