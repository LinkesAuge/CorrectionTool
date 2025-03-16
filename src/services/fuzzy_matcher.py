"""
fuzzy_matcher.py

Description: Service for fuzzy matching of text strings
Usage:
    from src.services.fuzzy_matcher import FuzzyMatcher
    matcher = FuzzyMatcher(threshold=0.85)
    score = matcher.get_similarity("Krimelmonster", "Krümelmonster")
"""

from typing import Dict, List, Optional, Tuple, Union

from fuzzywuzzy import fuzz


class FuzzyMatcher:
    """
    Service for fuzzy matching of text strings.
    
    Uses fuzzy string matching to find similar strings and calculate similarity scores.
    
    Attributes:
        threshold (float): Minimum similarity score to consider a match (0.0-1.0)
        
    Implementation Notes:
        - Uses FuzzyWuzzy library for string similarity calculations
        - Provides various matching algorithms
        - Configurable threshold for match determination
    """
    
    def __init__(self, threshold: float = 0.85) -> None:
        """
        Initialize a FuzzyMatcher.
        
        Args:
            threshold (float, optional): Minimum similarity score (0.0-1.0)
        """
        self.threshold = threshold
    
    def get_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings.
        
        Args:
            str1 (str): First string
            str2 (str): Second string
            
        Returns:
            float: Similarity score (0.0-1.0)
        """
        # Use token_sort_ratio for better handling of word order
        ratio = fuzz.token_sort_ratio(str1, str2) / 100.0
        return ratio
    
    def is_match(self, str1: str, str2: str) -> bool:
        """
        Check if two strings are considered a match based on threshold.
        
        Args:
            str1 (str): First string
            str2 (str): Second string
            
        Returns:
            bool: True if similarity exceeds threshold, False otherwise
        """
        return self.get_similarity(str1, str2) >= self.threshold
    
    def find_best_match(self, query: str, choices: List[str]) -> Tuple[str, float]:
        """
        Find the best match for a query string from a list of choices.
        
        Args:
            query (str): The string to match
            choices (List[str]): List of possible matches
            
        Returns:
            Tuple[str, float]: (Best match, Similarity score)
            
        Raises:
            ValueError: If choices list is empty
        """
        if not choices:
            raise ValueError("Choices list cannot be empty")
            
        best_match = ""
        best_score = 0.0
        
        for choice in choices:
            score = self.get_similarity(query, choice)
            if score > best_score:
                best_score = score
                best_match = choice
        
        return best_match, best_score
    
    def find_matches(self, query: str, choices: List[str]) -> List[Tuple[str, float]]:
        """
        Find all matches for a query string from a list of choices.
        
        Args:
            query (str): The string to match
            choices (List[str]): List of possible matches
            
        Returns:
            List[Tuple[str, float]]: List of (match, score) pairs exceeding threshold
        """
        matches = []
        
        for choice in choices:
            score = self.get_similarity(query, choice)
            if score >= self.threshold:
                matches.append((choice, score))
        
        # Sort by score in descending order
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def correct_text(self, text: str, valid_choices: List[str]) -> Tuple[str, float]:
        """
        Attempt to correct text using fuzzy matching.
        
        Args:
            text (str): The text to correct
            valid_choices (List[str]): List of valid choices
            
        Returns:
            Tuple[str, float]: (Corrected text, Confidence score)
        """
        if not valid_choices:
            return text, 0.0
            
        if text in valid_choices:
            return text, 1.0
            
        best_match, score = self.find_best_match(text, valid_choices)
        
        if score >= self.threshold:
            return best_match, score
        else:
            return text, 0.0 