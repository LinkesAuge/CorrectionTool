"""
correction_rule.py

Description: Data model for correction rules
Usage:
    from src.models.correction_rule import CorrectionRule
    rule = CorrectionRule(from_text="Krimelmonster", to_text="Krümelmonster", category="player")
"""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple


@dataclass
class CorrectionRule:
    """
    Represents a correction rule for text replacement.

    A rule defines a text string to be replaced and its replacement value.

    Attributes:
        from_text (str): The text to be replaced
        to_text (str): The replacement text
        rule_type (str): Type of rule ('exact' or 'fuzzy')
        priority (int): Priority of the rule (higher numbers = higher priority)
        category (Optional[str]): Category the rule applies to ('chest', 'player', 'source', 'general')

    Implementation Notes:
        - Uses dataclass for simplified initialization
        - Supports exact string matching and fuzzy matching
        - Higher priority rules are applied first
        - Category specifies where to apply the rule:
          - 'chest': Apply only to chest_type fields
          - 'player': Apply only to player fields
          - 'source': Apply only to source fields
          - 'general': Apply to all fields
    """

    # Rule type constants
    EXACT = "exact"
    FUZZY = "fuzzy"
    EXACT_IGNORE_CASE = "exact_ignore_case"
    CONTAINS = "contains"
    CONTAINS_IGNORE_CASE = "contains_ignore_case"

    # Category mapping to old field targets for backward compatibility
    CATEGORY_TO_FIELD = {
        "chest": "chest_type",
        "player": "player",
        "source": "source",
        "general": None,
    }

    # Field to category mapping for backward compatibility
    FIELD_TO_CATEGORY = {
        "chest_type": "chest",
        "player": "player",
        "source": "source",
        None: "general",
    }

    from_text: str
    to_text: str
    rule_type: Literal[
        "exact", "fuzzy", "exact_ignore_case", "contains", "contains_ignore_case"
    ] = "exact"
    priority: int = 0
    category: Literal["chest", "player", "source", "general"] = "general"

    def __post_init__(self):
        """Validate and normalize the category field."""
        if self.category not in ("chest", "player", "source", "general"):
            self.category = "general"

    @property
    def field_target(self) -> Optional[str]:
        """
        Get the field target for backward compatibility.

        Returns:
            Optional[str]: Field target ('chest_type', 'player', 'source', or None)
        """
        return self.CATEGORY_TO_FIELD.get(self.category)

    @field_target.setter
    def field_target(self, value: Optional[str]) -> None:
        """
        Set the category based on field_target for backward compatibility.

        Args:
            value (Optional[str]): Field target ('chest_type', 'player', 'source', or None)
        """
        self.category = self.FIELD_TO_CATEGORY.get(value, "general")

    def apply_to_text(self, text: str) -> Tuple[str, bool]:
        """
        Apply the rule to a text string.

        Args:
            text (str): The text to apply the rule to

        Returns:
            tuple[str, bool]: (Corrected text, Whether correction was applied)
        """
        if self.rule_type == self.EXACT:
            if self.from_text == text:
                return self.to_text, True
            return text, False

        elif self.rule_type == self.EXACT_IGNORE_CASE:
            if self.from_text.lower() == text.lower():
                return self.to_text, True
            return text, False

        elif self.rule_type == self.CONTAINS:
            if self.from_text in text:
                corrected = text.replace(self.from_text, self.to_text)
                return corrected, corrected != text
            return text, False

        elif self.rule_type == self.CONTAINS_IGNORE_CASE:
            lower_from = self.from_text.lower()
            lower_text = text.lower()
            if lower_from in lower_text:
                # Need to do case-preserving replacement
                index = lower_text.find(lower_from)
                prefix = text[:index]
                suffix = text[index + len(self.from_text) :]
                return prefix + self.to_text + suffix, True
            return text, False

        elif self.rule_type == self.FUZZY:
            # Fuzzy matching implementation
            # Import here to avoid circular imports
            from src.services.fuzzy_matcher import FuzzyMatcher

            # Create a fuzzy matcher with a reasonable threshold
            matcher = FuzzyMatcher(threshold=0.85)

            # If the text is an exact match to from_text, replace it entirely
            if text.strip() == self.from_text.strip():
                return self.to_text, True

            # For partial matches within longer text, we need to split and check each word
            words = text.split()
            if not words:
                return text, False

            # Check if any word is a fuzzy match to from_text
            any_replaced = False
            for i, word in enumerate(words):
                # Check if this word is a fuzzy match
                if matcher.is_match(word, self.from_text):
                    words[i] = self.to_text
                    any_replaced = True

            # If any replacements were made, join the words back together
            if any_replaced:
                corrected = " ".join(words)
                return corrected, True

            return text, False

        # Default case - no changes
        return text, False

    def applies_to_field(self, field: str) -> bool:
        """
        Check if this rule applies to a specific field.

        Args:
            field (str): The field to check ('chest_type', 'player', or 'source')

        Returns:
            bool: True if the rule applies to the field, False otherwise
        """
        # General category applies to all fields
        if self.category == "general":
            return True

        # Map field name to category
        field_category = self.FIELD_TO_CATEGORY.get(field)

        # Check if rule category matches field category
        return self.category == field_category

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the rule to a dictionary.

        Returns:
            Dict[str, str]: Dictionary representation of the rule
        """
        return {
            "from_text": self.from_text,
            "to_text": self.to_text,
            "rule_type": self.rule_type,
            "priority": str(self.priority),
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "CorrectionRule":
        """
        Create a CorrectionRule from a dictionary.

        Args:
            data (Dict[str, str]): Dictionary representation of the rule

        Returns:
            CorrectionRule: The created rule

        Raises:
            ValueError: If required fields are missing
        """
        if "from_text" not in data or "to_text" not in data:
            raise ValueError("Dictionary must contain 'from_text' and 'to_text' keys")

        rule_type = data.get("rule_type", "exact")
        if rule_type not in (
            "exact",
            "fuzzy",
            "exact_ignore_case",
            "contains",
            "contains_ignore_case",
        ):
            rule_type = "exact"

        priority = int(data.get("priority", 0))

        # Try to get the category first, then fall back to field_target for compatibility
        if "category" in data:
            category = data["category"]
            if category not in ("chest", "player", "source", "general"):
                category = "general"
        elif "field_target" in data:
            field_target = data["field_target"]
            category = cls.FIELD_TO_CATEGORY.get(field_target, "general")
        else:
            category = "general"

        return cls(
            from_text=data["from_text"],
            to_text=data["to_text"],
            rule_type=rule_type,  # type: ignore
            priority=priority,
            category=category,  # type: ignore
        )

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> "CorrectionRule":
        """
        Create a CorrectionRule from a CSV row.

        Args:
            row (Dict[str, str]): CSV row with 'From', 'To', and optionally 'Category' columns

        Returns:
            CorrectionRule: The created rule

        Raises:
            ValueError: If required fields are missing
        """
        # Check for required fields
        if not row:
            raise ValueError("CSV row is empty")

        # Check for required fields with case-insensitive matching
        from_value = None
        to_value = None
        category = "general"  # Default category

        # Find the 'From' field (case-insensitive)
        for key in row:
            if key.lower() == "from":
                from_value = row[key]
                break

        # Find the 'To' field (case-insensitive)
        for key in row:
            if key.lower() == "to":
                to_value = row[key]
                break

        # Find the 'Category' field (case-insensitive)
        for key in row:
            if key.lower() == "category":
                category_value = row[key]
                if category_value and isinstance(category_value, str):
                    category_value = category_value.lower()
                    if category_value in ("chest", "player", "source", "general"):
                        category = category_value
                break

        # Check if required fields were found
        if from_value is None:
            raise ValueError("CSV row must contain 'From' column")
        if to_value is None:
            raise ValueError("CSV row must contain 'To' column")

        # Check if values are empty
        if not from_value.strip():
            raise ValueError("'From' value cannot be empty")
        if not to_value.strip():
            raise ValueError("'To' value cannot be empty")

        # Create the rule
        return cls(
            from_text=from_value.strip(),
            to_text=to_value.strip(),
            category=category,  # type: ignore
        )

    def to_csv_row(self) -> Dict[str, str]:
        """
        Convert the rule to a CSV row.

        Returns:
            Dict[str, str]: CSV row with 'From', 'To', and 'Category' columns
        """
        return {"From": self.from_text, "To": self.to_text, "Category": self.category}
