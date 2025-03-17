"""
corrector.py

Description: Service for applying correction rules to chest entries
Usage:
    from src.services.corrector import Corrector
    corrector = Corrector()
    corrected_entries = corrector.apply_corrections(entries, rules)
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any

from src.models.chest_entry import ChestEntry
from src.models.correction_rule import CorrectionRule
from src.services.config_manager import ConfigManager
from src.services.fuzzy_matcher import FuzzyMatcher


class CorrectionResult:
    """
    Result of a correction operation.

    Stores information about a correction that was applied, including
    the original value, the corrected value, and the rule that was applied.

    Attributes:
        entry_index (int): Index of the entry in the original list
        field (str): Field that was corrected (chest_type, player, source)
        original_value (str): Original value before correction
        corrected_value (str): Value after correction
        rule (CorrectionRule): Rule that was applied
        match_score (float): Match score (for fuzzy matches)
    """

    def __init__(
        self,
        entry_index: int,
        field: str,
        original_value: str,
        corrected_value: str,
        rule: CorrectionRule,
        match_score: float = 1.0,
    ):
        """
        Initialize a correction result.

        Args:
            entry_index: Index of the entry in the original list
            field: Field that was corrected
            original_value: Original value before correction
            corrected_value: Value after correction
            rule: Rule that was applied
            match_score: Match score (for fuzzy matches)
        """
        self.entry_index = entry_index
        self.field = field
        self.original_value = original_value
        self.corrected_value = corrected_value
        self.rule = rule
        self.match_score = match_score

    def __str__(self) -> str:
        """
        Get string representation of the correction result.

        Returns:
            String representation
        """
        return (
            f"CorrectionResult(entry={self.entry_index}, field={self.field}, "
            f"original='{self.original_value}', corrected='{self.corrected_value}', "
            f"rule={self.rule.rule_type.name}, score={self.match_score:.2f})"
        )


class Corrector:
    """
    Service for applying correction rules to chest entries.

    This service applies correction rules to chest entries,
    handling both exact and fuzzy matches, and keeping track
    of which corrections were applied.

    Implementation Notes:
        - Applies correction rules to entries
        - Handles both exact and fuzzy matches
        - Sorts rules by priority
        - Keeps track of applied corrections
        - Provides detailed correction results
    """

    def __init__(self):
        """
        Initialize the Corrector.
        """
        self._config = ConfigManager()
        self._fuzzy_matcher = FuzzyMatcher()

        # Load configuration settings
        self._fuzzy_threshold = self._config.get_float(
            "corrections", "fuzzy_threshold", fallback=0.8
        )
        self._enable_fuzzy = self._config.get_bool("corrections", "enable_fuzzy", fallback=True)

        # Initialize correction results
        self._last_correction_results: List[CorrectionResult] = []
        self._logger = logging.getLogger(__name__)

    def get_last_results(self) -> List[CorrectionResult]:
        """
        Get the results of the last correction operation.

        Returns:
            List of correction results
        """
        return self._last_correction_results

    def apply_corrections(
        self,
        entries: List[ChestEntry],
        rules: List[CorrectionRule],
        fields: Optional[List[str]] = None,
    ) -> List[ChestEntry]:
        """
        Apply correction rules to a list of entries.

        Args:
            entries: List of chest entries to correct
            rules: List of correction rules to apply
            fields: Optional list of fields to correct (defaults to all fields)

        Returns:
            List of corrected entries
        """
        if not entries or not rules:
            return entries

        # Clear last results
        self._last_correction_results = []

        # Default fields if not specified
        if fields is None:
            fields = ["chest_type", "player", "source"]

        # Sort rules by priority (highest first)
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        # Group rules by category for more efficient application
        field_to_category = {"chest_type": "chest", "player": "player", "source": "source"}

        category_rules = {"chest": [], "player": [], "source": [], "general": []}

        for rule in sorted_rules:
            if rule.category in category_rules:
                category_rules[rule.category].append(rule)
            else:
                # Default to general if category is not recognized
                category_rules["general"].append(rule)

        # Apply corrections to each entry
        for entry_idx, entry in enumerate(entries):
            # Create copy of the entry to avoid modifying the original
            entry_copy = entry

            try:
                # Apply field-specific rules
                for field in fields:
                    if not hasattr(entry_copy, field):
                        self._logger.warning(f"Entry has no field '{field}'")
                        continue

                    # Get current field value
                    value = getattr(entry_copy, field)
                    if not value:
                        continue

                    # Get category for this field
                    category = field_to_category.get(field)
                    if not category:
                        continue

                    # Apply category-specific rules
                    category_specific_rules = category_rules.get(category, [])
                    for rule in category_specific_rules:
                        corrected_value, corrected = self._apply_rule_to_value(
                            value, rule, entry_idx, field
                        )
                        if corrected:
                            # Store original value if not already stored
                            if field not in entry_copy.original_values:
                                entry_copy.original_values[field] = value

                            # Update the field value
                            setattr(entry_copy, field, corrected_value)
                            value = corrected_value

                    # Apply general rules to all fields
                    for rule in category_rules["general"]:
                        corrected_value, corrected = self._apply_rule_to_value(
                            value, rule, entry_idx, field
                        )
                        if corrected:
                            # Store original value if not already stored
                            if field not in entry_copy.original_values:
                                entry_copy.original_values[field] = value

                            # Update the field value
                            setattr(entry_copy, field, corrected_value)
                            value = corrected_value

                # Replace the original entry with the corrected one
                entries[entry_idx] = entry_copy

            except Exception as e:
                self._logger.error(f"Error applying corrections to entry {entry_idx}: {str(e)}")
                # Continue with the next entry

        # Log correction results
        self._log_correction_results()

        return entries

    def _apply_rule_to_value(
        self, value: str, rule: CorrectionRule, entry_idx: int, field: str
    ) -> Tuple[str, bool]:
        """
        Apply a correction rule to a string value.

        Args:
            value: String value to correct
            rule: Correction rule to apply
            entry_idx: Index of the entry
            field: Field being corrected

        Returns:
            Tuple of (corrected value, whether correction was applied)
        """
        try:
            # Check if the rule applies to this field
            if not rule.applies_to_field(field):
                return value, False

            # Apply the rule
            corrected_value, corrected, match_score = self._apply_rule(value, rule)

            # If correction was applied, record the result
            if corrected:
                result = CorrectionResult(
                    entry_index=entry_idx,
                    field=field,
                    original_value=value,
                    corrected_value=corrected_value,
                    rule=rule,
                    match_score=match_score,
                )
                self._last_correction_results.append(result)
                return corrected_value, True

            return value, False

        except Exception as e:
            self._logger.error(
                f"Error applying rule to value: {str(e)}, "
                f"value='{value}', rule='{rule}', field='{field}'"
            )
            return value, False

    def _apply_rule(self, value: str, rule: CorrectionRule) -> Tuple[str, bool, float]:
        """
        Apply a correction rule to a string value.

        Args:
            value: String value to correct
            rule: Correction rule to apply

        Returns:
            Tuple of (corrected value, whether correction was applied, match score)
        """
        # Get the threshold for fuzzy matching
        threshold = self._fuzzy_threshold

        # Apply the rule based on its type
        if rule.rule_type == CorrectionRule.EXACT:
            # Exact matching is case-sensitive by default
            if rule.from_text == value:
                return rule.to_text, True, 1.0
            return value, False, 0.0

        elif rule.rule_type == CorrectionRule.EXACT_IGNORE_CASE:
            # Case-insensitive exact matching
            if rule.from_text.lower() == value.lower():
                return rule.to_text, True, 1.0
            return value, False, 0.0

        elif rule.rule_type == CorrectionRule.FUZZY:
            # Fuzzy matching with threshold
            match_score = self._fuzzy_matcher.similarity(rule.from_text, value)
            if match_score >= threshold:
                return rule.to_text, True, match_score
            return value, False, match_score

        elif rule.rule_type == CorrectionRule.CONTAINS:
            # Check if value contains the from_text
            if rule.from_text in value:
                # Replace the matching portion
                return value.replace(rule.from_text, rule.to_text), True, 1.0
            return value, False, 0.0

        elif rule.rule_type == CorrectionRule.CONTAINS_IGNORE_CASE:
            # Case-insensitive contains matching
            if rule.from_text.lower() in value.lower():
                # Need to find the actual text to replace (preserve case)
                start = value.lower().find(rule.from_text.lower())
                end = start + len(rule.from_text)
                actual_text = value[start:end]
                return value.replace(actual_text, rule.to_text), True, 1.0
            return value, False, 0.0

        else:
            # Unknown rule type
            self._logger.warning(f"Unknown rule type: {rule.rule_type}")
            return value, False, 0.0

    def _log_correction_results(self):
        """Log information about the last correction operation."""
        if not self._last_correction_results:
            self._logger.info("No corrections were applied")
            return

        self._logger.info(f"Applied {len(self._last_correction_results)} corrections:")

        # Group by rule type for more concise logging
        rule_type_counts: Dict[str, int] = {}
        field_counts: Dict[str, int] = {}

        for result in self._last_correction_results:
            rule_type = result.rule.rule_type.name
            rule_type_counts[rule_type] = rule_type_counts.get(rule_type, 0) + 1
            field_counts[result.field] = field_counts.get(result.field, 0) + 1

            # Log detailed information at debug level
            self._logger.debug(
                f"  {result.entry_index:3d}: {result.field:10s} "
                f"'{result.original_value}' -> '{result.corrected_value}' "
                f"({result.rule.rule_type.name}, score={result.match_score:.2f})"
            )

        # Log summary at info level
        for rule_type, count in rule_type_counts.items():
            self._logger.info(f"  {rule_type}: {count}")

        for field, count in field_counts.items():
            self._logger.info(f"  {field}: {count}")
