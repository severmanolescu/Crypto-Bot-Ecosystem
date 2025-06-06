"""
Data Extractor Module
This module provides a class to extract keywords from article headlines
and generate hashtags based on those keywords.
"""

import re


class DataExtractor:
    """
    DataExtractor class to handle keyword matching and hashtag generation
    for article headlines.
    """

    def __init__(self, keywords):
        """
        Initialize the extractor with a list of keywords.
        Args:
            keywords (list): List of keywords to search for in article headlines.
        """
        self.keywords = keywords

    def contains_keywords(self, headline):
        """
        Match only full words or phrases, allowing ending punctuation like . , ! ?
        Args:
            headline (str): The headline text to check for keywords.
        Returns:
            bool: True if any keyword is found in the headline, False otherwise.
        """
        headline_lower = headline.lower()

        for keyword in self.keywords:
            keyword_lower = keyword.lower()
            pattern = rf"\b{re.escape(keyword_lower)}\b[.,!?]?"
            if re.search(pattern, headline_lower):
                return True
        return False

    def extract_highlights(self, headline):
        """
        Return #hashtags for each matched keyword in the headline.
        Args:
            headline (str): The headline text to extract hashtags from.
        Returns:
            str: A string of hashtags corresponding to the matched keywords,
                 or "#GeneralNews" if no keywords are found.
        """
        headline_lower = headline.lower()
        found_keywords = [
            f"#{keyword.replace(' ', '')}"
            for keyword in self.keywords
            if keyword.lower() in headline_lower
        ]
        return " ".join(found_keywords) if found_keywords else "#GeneralNews"
