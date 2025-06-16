"""
Test suite for the data_fetcher module in the src package.
This suite tests the fetching of the Crypto Fear & Greed Index.
"""

import pytest

from src.handlers.data_fetcher_handler import (
    get_fear_and_greed,
    get_fear_and_greed_message,
)


@pytest.mark.asyncio
async def test_get_fear_and_greed_message():
    """
    Test the fetching of the Crypto Fear & Greed Index.
    """
    print("Testing the fetching of the Crypto Fear & Greed Index...")

    message = await get_fear_and_greed_message()

    assert (
        "Crypto Fear & Greed Index" in message
    ), "The message should contain 'Fear & Greed Index'."
    assert "Score" in message, "The message should contain 'Score'."
    assert "Sentiment" in message, "The message should contain 'Sentiment'."
    assert "Last Updated" in message, "The message should contain 'Last Updated'."


@pytest.mark.asyncio
async def test_get_fear_and_greed():
    """
    Test the fetching of the Crypto Fear & Greed Index data.
    """
    print("Testing the fetching of the Crypto Fear & Greed Index data...")

    score, sentiment, last_update = await get_fear_and_greed()

    assert score is not None, "The score should not be None."
    assert sentiment is not None, "The sentiment should not be None."
    assert last_update is not None, "The last update date should not be None."
    assert isinstance(score, str), "The score should be a string."
    assert isinstance(sentiment, str), "The sentiment should be a string."
    assert isinstance(last_update, str), "The last update date should be a string."
