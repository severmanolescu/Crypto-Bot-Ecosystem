"""
News Check Bot Test Suite
"""

# pylint: disable=redefined-outer-name, unused-variable, duplicate-code

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bots.news_check_bot import NEWS_KEYBOARD, NewsBot


@pytest.fixture
def news_bot():
    """Fixture that creates a NewsBot with mocked dependencies"""
    with patch(
        "src.bots.news_check_bot.CryptoNewsCheck"
    ) as mock_news_check_class, patch(
        "src.bots.news_check_bot.DataBaseHandler"
    ) as mock_db_class, patch(
        "src.bots.news_check_bot.send_telegram_message_update"
    ) as mock_send_message:

        # Create mock instances
        mock_news_check = MagicMock()
        mock_news_check_class.return_value = mock_news_check
        mock_news_check.reload_the_data = MagicMock()
        mock_news_check.run_from_bot = AsyncMock()

        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.show_stats = AsyncMock()
        mock_db.search_articles_by_tags = AsyncMock()

        # Mock the send_telegram_message_update function
        mock_send_message.side_effect = AsyncMock()

        # Create the bot
        bot = NewsBot()

        # Provide the mocked objects to the test
        yield bot, {
            "news_check": mock_news_check,
            "db": mock_db,
            "send_message": mock_send_message,
        }


@pytest.mark.asyncio
async def test_start_command(news_bot):
    """Test the start command sends welcome message with keyboard"""
    bot, mocks = news_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()
    mock_context = MagicMock()

    # Call the method
    await bot.start(mock_update, mock_context)

    # Verify welcome message was sent with correct keyboard
    mock_update.message.reply_text.assert_called_once_with(
        "🤖 Welcome to the News Bot! Use the buttons below to get started:",
        reply_markup=NEWS_KEYBOARD,
    )


@pytest.mark.asyncio
async def test_start_the_articles_check(news_bot):
    """Test start_the_articles_check method initiates article check"""
    bot, mocks = news_bot

    # Create mock update
    mock_update = MagicMock()

    # Call the method
    await bot.start_the_articles_check(mock_update)

    # _check"].reload_the_data.assert_called_once()
    mocks["news_check"].run_from_bot.assert_called_once_with(mock_update)


@pytest.mark.asyncio
async def test_market_sentiment(news_bot):
    """Test market_sentiment method calculates and sends sentiment"""
    bot, mocks = news_bot  # Unpack the fixture to get bot and mocks

    # Create mock update
    mock_update = MagicMock()

    # Mock get_market_sentiment
    sample_sentiment = "Market sentiment: Neutral (53%)"
    with patch(
        "src.bots.news_check_bot.get_market_sentiment",
        AsyncMock(return_value=sample_sentiment),
    ):
        # Call the method
        await bot.market_sentiment(mock_update)

    # Verify sentiment was sent
    mocks["send_message"].assert_called_once_with(sample_sentiment, mock_update)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "button_text,expected_method",
    [
        ("🚨 Check for Articles", "start_the_articles_check"),
        ("check", "start_the_articles_check"),
        ("🔢 Show statistics", "show_stats"),
        ("statistics", "show_stats"),
        ("📊 Market Sentiment", "market_sentiment"),
        ("sentiment", "market_sentiment"),
        ("🚨 Help", "help_command"),
        ("help", "help_command"),
    ],
)
async def test_handle_buttons(news_bot, button_text, expected_method):
    """Test handle_buttons method routes to correct method based on button text"""
    bot, mocks = news_bot

    # Create mock methods to track calls
    with patch.object(
        bot, "start_the_articles_check", AsyncMock()
    ) as mock_articles_check, patch.object(
        bot, "market_sentiment", AsyncMock()
    ) as mock_market_sentiment, patch.object(
        bot, "help_command", AsyncMock()
    ) as mock_help_command:

        # Create mock update and context
        mock_update = MagicMock()
        mock_update.message.text = button_text
        mock_context = MagicMock()

        # Call the method
        await bot.handle_buttons(mock_update, mock_context)

        # Verify the correct messages and methods were called
        if expected_method == "start_the_articles_check":
            mocks["send_message"].assert_called_with(
                "🚨 Check for articles...", mock_update
            )
            mock_articles_check.assert_called_once_with(mock_update)
        elif expected_method == "show_stats":
            mocks["send_message"].assert_called_with(
                "🔢 Showing the statistics...", mock_update
            )
            mocks["db"].show_stats.assert_called_once_with(mock_update)
        elif expected_method == "market_sentiment":
            mocks["send_message"].assert_called_with(
                "🧮 Calculating the sentiment...", mock_update
            )
            mock_market_sentiment.assert_called_once_with(mock_update)
        elif expected_method == "help_command":
            mock_help_command.assert_called_once_with(mock_update, mock_context)


@pytest.mark.asyncio
async def test_handle_buttons_invalid_command(news_bot):
    """Test handle_buttons with invalid command"""
    bot, mocks = news_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_update.message.text = "Invalid Command"
    mock_context = MagicMock()

    # Call the method
    await bot.handle_buttons(mock_update, mock_context)

    # Verify error message was sent
    mocks["send_message"].assert_called_with(
        "❌ Invalid command. Please use the buttons below.", mock_update
    )


@pytest.mark.asyncio
async def test_search_no_args(news_bot):
    """Test search command with no arguments"""
    bot, mocks = news_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_context.args = []

    # Call the method
    await bot.search(mock_update, mock_context)

    # Verify usage message was sent
    mocks["send_message"].assert_called_once_with(
        "❌ Usage: /search <tags>", mock_update
    )


@pytest.mark.asyncio
async def test_search_no_results(news_bot):
    """Test search command with no matching articles"""
    bot, mocks = news_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_context.args = ["BTC", "Crypto"]

    # Mock empty search results
    mocks["db"].search_articles_by_tags.return_value = []

    # Call the method
    await bot.search(mock_update, mock_context)

    # Verify correct message was sent
    mocks["send_message"].assert_called_once_with(
        "No articles found with ['BTC', 'Crypto'] found!", mock_update
    )


@pytest.mark.asyncio
async def test_search_with_results(news_bot):
    """Test search command with matching articles"""
    bot, mocks = news_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_context.args = ["BTC"]

    # Mock search results (ID, Title, Link, Highlights, Summary)
    mock_articles = [
        (1, "Bitcoin Surges", "http://example.com/1", "Key highlights", "BTC summary"),
        (
            2,
            "Crypto Market",
            "http://example.com/2",
            "More highlights",
            "Market summary",
        ),
    ]
    mocks["db"].search_articles_by_tags.return_value = mock_articles

    # Call the method
    await bot.search(mock_update, mock_context)

    # Verify messages were sent for each article
    assert mocks["send_message"].call_count == 2
    for i, article in enumerate(mock_articles):
        expected_message = (
            f"📰 Article Found!\n"
            f"📌 {article[1]}\n"
            f"🔗 {article[2]}\n"
            f"🤖 {article[4]}\n"
            f"🔍 Highlights: {article[3]}\n"
        )
        mocks["send_message"].assert_any_call(expected_message, mock_update)


@pytest.mark.asyncio
async def test_help_command(news_bot):
    """Test help_command sends help message"""
    bot, mocks = news_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_context = MagicMock()

    # Call the method
    await bot.help_command(mock_update, mock_context)

    # Verify help message was sent
    mocks["send_message"].assert_called_once()
    args = mocks["send_message"].call_args[0]
    assert "Crypto Bot Commands" in args[0]
    assert "/start" in args[0]
    assert "/search" in args[0]
    assert "/help" in args[0]


def test_run_bot(news_bot):
    """Test run_bot method sets up application with correct handlers"""
    bot, _ = news_bot

    # Create mock application
    mock_app = MagicMock()
    mock_app_builder = MagicMock()
    mock_app_builder.token.return_value = mock_app_builder
    mock_app_builder.build.return_value = mock_app

    # Mock variables.get to return test token
    mock_variables = {"TELEGRAM_API_TOKEN_ARTICLES": "test_token_value"}

    # Mock Application.builder() to return our mock
    with patch(
        "src.bots.news_check_bot.Application.builder", return_value=mock_app_builder
    ), patch(
        "src.bots.news_check_bot.src.handlers.load_variables_handler.load",
        return_value=mock_variables,
    ), patch.object(
        mock_app, "run_polling"
    ) as mock_run_polling:
        # Call the method
        bot.run_bot()

        # Verify application was initialized with token
        mock_app_builder.token.assert_called_once_with("test_token_value")

        # Verify handlers were added
        assert (
            mock_app.add_handler.call_count == 4
        )  # 3 command handlers + 1 message handler

        # Verify polling was started
        mock_run_polling.assert_called_once()
