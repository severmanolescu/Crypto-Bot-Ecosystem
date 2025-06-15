"""
Data Extractor Test Module
"""

# pylint: disable=redefined-outer-name

import pytest

from src.scrapers.data_extractor import DataExtractor


@pytest.fixture
def get_data_extractor():
    """
    Fixture to create an instance of DataExtractor for testing.
    """
    keywords = ["Bitcoin", "Ethereum", "Crypto"]
    return DataExtractor(keywords)


def test_contains_keywords(get_data_extractor):
    """
    Test the contains_keywords method of DataExtractor.
    """
    extractor = get_data_extractor

    assert extractor.contains_keywords("Bitcoin hits new highs!") is True
    assert extractor.contains_keywords("Ethereum is on the rise.") is True
    assert extractor.contains_keywords("Crypto market analysis.") is True
    assert extractor.contains_keywords("No relevant keywords here.") is False
    assert extractor.contains_keywords("Bitcoin, Ethereum, and Crypto!") is True


def test_extract_highlights(get_data_extractor):
    """
    Test the extract_highlights method of DataExtractor.
    """
    extractor = get_data_extractor

    assert extractor.extract_highlights("Bitcoin hits new highs!") == "#Bitcoin"
    assert extractor.extract_highlights("Ethereum is on the rise.") == "#Ethereum"
    assert extractor.extract_highlights("Crypto market analysis.") == "#Crypto"
    assert extractor.extract_highlights("No relevant keywords here.") == "#GeneralNews"
    assert (
        extractor.extract_highlights("Bitcoin, Ethereum, and Crypto!")
        == "#Bitcoin #Ethereum #Crypto"
    )
