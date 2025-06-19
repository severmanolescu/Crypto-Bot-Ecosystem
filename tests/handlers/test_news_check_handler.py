"""
News Check Handler Tests
"""

# pylint: disable=redefined-outer-name

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from src.handlers.news_check_handler import CryptoNewsCheck


@pytest.fixture
def news_check():
    """Fixture to create a CryptoNewsCheck instance for testing."""
    with patch("src.data_base.data_base_handler.DataBaseHandler"):
        news_check = CryptoNewsCheck(db_path=":memory:")
        # Mock the dependencies
        news_check.telegram_message = AsyncMock()
        news_check.open_ai_prompt = AsyncMock()
        return news_check


@pytest.mark.asyncio
async def test_reload_the_data(news_check):
    """Test that reload_the_data properly loads configuration."""
    mock_variables = {
        "TELEGRAM_API_TOKEN_ARTICLES": "test_token",
        "TELEGRAM_CHAT_ID_FULL_DETAILS": ["chat1", "chat2"],
        "TELEGRAM_CHAT_ID_PARTIAL_DATA": ["chat3"],
        "OPEN_AI_API": "openai_key",
        "SEND_AI_SUMMARY": "True",
    }

    mock_keywords = ["bitcoin", "ethereum"]

    with patch(
        "src.handlers.news_check_handler.load", return_value=mock_variables
    ), patch(
        "src.handlers.news_check_handler.load_keyword_list",
        return_value=mock_keywords,
    ), patch(
        "src.handlers.news_check_handler.OpenAIPrompt"
    ) as mock_openai, patch.object(
        news_check.telegram_message, "reload_the_data"
    ):
        news_check.reload_the_data()

        assert news_check.telegram_api_token == "test_token"
        assert news_check.telegram_important_chat_id == ["chat1", "chat2"]
        assert news_check.telegram_not_important_chat_id == ["chat3"]
        assert news_check.keywords == mock_keywords
        assert news_check.send_ai_summary == "True"
        mock_openai.assert_called_once_with("openai_key")
        news_check.telegram_message.reload_the_data.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_page_success(news_check):
    """Test successful page fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>Test content</html>"

    with patch.object(news_check.scraper, "get", return_value=mock_response):
        result = await news_check.fetch_page("https://example.com")

        assert result == "<html>Test content</html>"
        news_check.scraper.get.assert_called_once_with(
            "https://example.com", timeout=10
        )


@pytest.mark.asyncio
async def test_fetch_page_retry(news_check):
    """Test page fetch with retries."""
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 429

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.text = "<html>Test content</html>"

    with patch.object(
        news_check.scraper,
        "get",
        side_effect=[mock_response_fail, mock_response_success],
    ), patch("asyncio.sleep", return_value=None):

        result = await news_check.fetch_page("https://example.com")

        assert result == "<html>Test content</html>"
        assert news_check.scraper.get.call_count == 2


@pytest.mark.asyncio
async def test_scrape_articles_crypto_news(news_check):
    """Test scraping crypto.news articles."""
    mock_soup = BeautifulSoup("<html></html>", "html.parser")

    with patch(
        "src.handlers.news_check_handler.CryptoNewsScraper"
    ) as mock_scraper_class:
        mock_scraper = mock_scraper_class.return_value
        mock_scraper.scrape.return_value = [
            {
                "headline": "Test Article",
                "link": "https://example.com/article",
                "highlights": "Important news",
            }
        ]

        results = news_check.scrape_articles(mock_soup, "crypto.news")

        assert len(results) == 1
        assert results[0]["headline"] == "Test Article"
        mock_scraper.scrape.assert_called_once_with(mock_soup)


@pytest.mark.asyncio
async def test_generate_article_summary(news_check):
    """Test generating an article summary."""
    news_check.open_ai_prompt.generate_article_summary.return_value = (
        "This is a summary of the article."
    )

    result = await news_check.generate_summary("https://example.com/article")

    assert result == "This is a summary of the article."
    news_check.open_ai_prompt.generate_article_summary.assert_called_once_with(
        "https://example.com/article"
    )


@pytest.mark.asyncio
async def test_check_news_new_article(news_check):
    """Test checking news and finding a new article."""
    # Setup mocks
    news_check.fetch_page = AsyncMock(return_value="<html></html>")
    news_check.scrape_articles = MagicMock(
        return_value=[
            {
                "headline": "New Article",
                "link": "https://example.com/article",
                "highlights": "Important news",
            }
        ]
    )
    news_check.data_base.save_article_to_db = AsyncMock(
        return_value=1
    )  # 1 means new article
    news_check.data_base.update_article_summary_in_db = AsyncMock()
    news_check.generate_summary = AsyncMock(return_value="Article summary")
    news_check.send_ai_summary = "True"

    # Call the method
    result = await news_check.check_news("crypto.news")

    # Verify results
    assert result is True  # Found articles
    news_check.fetch_page.assert_called_once_with("https://crypto.news/")
    news_check.data_base.save_article_to_db.assert_called_once()
    news_check.generate_summary.assert_called_once()
    news_check.data_base.update_article_summary_in_db.assert_called_once()
    news_check.telegram_message.send_telegram_message.assert_called_once()


@pytest.mark.asyncio
async def test_check_news_existing_article(news_check):
    """Test checking news and finding only existing articles."""
    # Setup mocks
    news_check.fetch_page = AsyncMock(return_value="<html></html>")
    news_check.scrape_articles = MagicMock(
        return_value=[
            {
                "headline": "Old Article",
                "link": "https://example.com/article",
                "highlights": "Important news",
            }
        ]
    )
    news_check.data_base.save_article_to_db = AsyncMock(
        return_value=0
    )  # 0 means existing article

    # Call the method
    result = await news_check.check_news("crypto.news")

    # Verify results
    assert result is False  # No new articles
    news_check.fetch_page.assert_called_once_with("https://crypto.news/")
    news_check.data_base.save_article_to_db.assert_called_once()
    news_check.telegram_message.send_telegram_message.assert_not_called()


@pytest.mark.asyncio
async def test_run_from_bot(news_check):
    """Test running the news check from a Telegram bot command."""
    # Setup mocks
    news_check.data_base.init_db = AsyncMock()
    news_check.check_news = AsyncMock(side_effect=[True, False, False])
    mock_update = MagicMock()

    # Call the method
    await news_check.run_from_bot(mock_update)

    # Verify results
    news_check.data_base.init_db.assert_called_once()
    assert news_check.check_news.call_count == 3
    # Since one source returned True, no "didn't find" message should be sent
    news_check.telegram_message.send_telegram_message.assert_not_called()


@pytest.mark.asyncio
async def test_run_from_bot_no_articles(news_check):
    """Test running the news check from a bot with no new articles."""
    # Setup mocks
    news_check.data_base.init_db = AsyncMock()
    news_check.check_news = AsyncMock(return_value=False)
    mock_update = MagicMock()

    # Call the method
    await news_check.run_from_bot(mock_update)

    # Verify results
    news_check.data_base.init_db.assert_called_once()
    assert news_check.check_news.call_count == 3
    # Should send a "didn't find" message
    news_check.telegram_message.send_telegram_message.assert_called_once()
    assert (
        "Didn't find any new article"
        in news_check.telegram_message.send_telegram_message.call_args[0][0]
    )


@pytest.mark.asyncio
async def test_send_today_summary(news_check):
    """Test sending a daily summary of all articles."""
    # Setup mocks
    news_check.data_base.fetch_todays_news = AsyncMock(
        return_value=[
            (
                1,
                "Source",
                "Article 1",
                "link1",
                "highlights1",
                "summary1",
                datetime.now(),
            ),
            (
                2,
                "Source",
                "Article 2",
                "link2",
                "highlights2",
                "summary2",
                datetime.now(),
            ),
        ]
    )
    news_check.open_ai_prompt.get_response = AsyncMock(return_value="Daily summary")
    news_check.send_ai_summary = "True"

    # Call the method
    await news_check.send_today_summary()

    # Verify results
    news_check.data_base.fetch_todays_news.assert_called_once()
    news_check.open_ai_prompt.get_response.assert_called_once()
    news_check.telegram_message.send_telegram_message.assert_called_once()
    # Make sure the message includes the summary and the tag
    assert (
        "Daily summary"
        in news_check.telegram_message.send_telegram_message.call_args[0][0]
    )
    assert (
        "#DailyReport"
        in news_check.telegram_message.send_telegram_message.call_args[0][0]
    )
