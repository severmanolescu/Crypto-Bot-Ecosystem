"""
Test suite for the market_sentiment_handler module.
"""

import pytest

import src.handlers.market_sentiment_handler


@pytest.mark.asyncio
async def test_extract_sentiment_from_summary():
    """
    Test the extract_sentiment_from_summary function.
    """
    assert (
        await src.handlers.market_sentiment_handler.extract_sentiment_from_summary(
            "Bullish news"
        )
        == "Positive"
    )
    assert (
        await src.handlers.market_sentiment_handler.extract_sentiment_from_summary(
            "Bearish news"
        )
        == "Negative"
    )
    assert (
        await src.handlers.market_sentiment_handler.extract_sentiment_from_summary(
            "Neutral news"
        )
        == "Neutral"
    )
    assert (
        await src.handlers.market_sentiment_handler.extract_sentiment_from_summary(
            "Mixed news with bullish and bearish"
        )
        == "Unknown"
    )
    assert (
        await src.handlers.market_sentiment_handler.extract_sentiment_from_summary(
            "No sentiment here"
        )
        == "Unknown"
    )


@pytest.mark.asyncio
async def test_calculate_sentiment_trend():
    """
    Test the calculate_sentiment_trend function.
    """
    news_items = [
        (None, None, None, None, "Bullish news"),
        (None, None, None, None, "Bearish news"),
        (None, None, None, None, "Neutral news"),
        (None, None, None, None, "Bullish and bearish news"),
        (None, None, None, None, "No sentiment here"),
    ]

    result = await src.handlers.market_sentiment_handler.calculate_sentiment_trend(
        news_items
    )
    assert "Crypto sentiment for today" in result
    assert "Positive" in result or "Negative" in result or "Neutral" in result
