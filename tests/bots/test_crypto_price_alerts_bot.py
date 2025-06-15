"""
Crypto Price Alerts Bot Tests
"""

# pylint: disable=redefined-outer-name

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Chat, Message, Update, User

from src.bots.crypto_price_alerts_bot import NEWS_KEYBOARD, PriceAlertBot


@pytest.fixture
def price_alert_bot():
    """Fixture to create a PriceAlertBot instance with a mocked CryptoValueBot."""
    with patch(
        "src.bots.crypto_price_alerts_bot.CryptoValueBot"
    ) as mock_crypto_value_bot_class:
        # Create a mock instance for cryptoValueBot
        mock_crypto_value_bot = MagicMock()
        mock_crypto_value_bot_class.return_value = mock_crypto_value_bot

        # Configure the mock to handle async methods
        mock_crypto_value_bot.check_for_major_updates_1h = AsyncMock(return_value=True)
        mock_crypto_value_bot.check_for_major_updates_24h = AsyncMock(return_value=True)
        mock_crypto_value_bot.check_for_major_updates_7d = AsyncMock(return_value=True)
        mock_crypto_value_bot.check_for_major_updates_30d = AsyncMock(return_value=True)
        mock_crypto_value_bot.check_for_major_updates = AsyncMock(return_value=True)

        # Create bot AFTER setting up the mock
        bot = PriceAlertBot()

        # Replace the class attribute with our mock
        bot.cryptoValueBot = mock_crypto_value_bot

        yield bot, mock_crypto_value_bot


@pytest.fixture
def mock_update():
    """Fixture to create a mock Update object for testing."""
    mock_user = MagicMock(spec=User)
    mock_chat = MagicMock(spec=Chat)
    mock_message = MagicMock(spec=Message)
    mock_update = MagicMock(spec=Update)

    mock_update.message = mock_message
    mock_message.chat = mock_chat
    mock_message.from_user = mock_user
    mock_message.reply_text = AsyncMock()

    return mock_update


@pytest.mark.asyncio
async def test_start_command(price_alert_bot, mock_update):
    """Test the start command handler"""
    bot, _ = price_alert_bot
    context = MagicMock()

    await bot.start(mock_update, context)

    mock_update.message.reply_text.assert_called_once_with(
        "🤖 Welcome to the Alert Bot! Use the buttons below to get started:",
        reply_markup=NEWS_KEYBOARD,
    )


@pytest.mark.asyncio
async def test_handle_buttons_1h_alert(price_alert_bot, mock_update):
    """Test handling the 1h alert button press"""
    bot, mock_crypto_bot = price_alert_bot
    mock_update.message.text = "🚨 Check for 1h Alerts"
    context = MagicMock()

    # Configure the mock to return True (alerts available)
    mock_crypto_bot.check_for_major_updates_1h.return_value = True

    await bot.handle_buttons(mock_update, context)

    # Verify correct interactions
    mock_crypto_bot.reload_the_data.assert_called_once()
    mock_crypto_bot.get_my_crypto.assert_called_once()
    mock_crypto_bot.check_for_major_updates_1h.assert_called_once_with(mock_update)

    # First message should be the "searching" message
    assert mock_update.message.reply_text.call_count == 1
    mock_update.message.reply_text.assert_called_with(
        "🚨 Searching for new alerts for 1h update..."
    )


@pytest.mark.asyncio
async def test_handle_buttons_1h_alert_no_alerts(price_alert_bot, mock_update):
    """Test handling the 1h alert button press when no alerts are available"""
    bot, mock_crypto_bot = price_alert_bot
    mock_update.message.text = "🚨 Check for 1h Alerts"
    context = MagicMock()

    # Configure the mock to return False (no alerts available)
    mock_crypto_bot.check_for_major_updates_1h.return_value = False

    await bot.handle_buttons(mock_update, context)

    # Verify correct interactions
    mock_crypto_bot.reload_the_data.assert_called_once()
    mock_crypto_bot.get_my_crypto.assert_called_once()
    mock_crypto_bot.check_for_major_updates_1h.assert_called_once_with(mock_update)

    # Should have two messages: "searching" and "no alerts"
    assert mock_update.message.reply_text.call_count == 2
    mock_update.message.reply_text.assert_called_with(
        "😔 No major price movement for 1h timeframe"
    )


@pytest.mark.asyncio
async def test_handle_buttons_all_timeframes(price_alert_bot, mock_update):
    """Test handling the all timeframes alert button press"""
    bot, mock_crypto_bot = price_alert_bot
    mock_update.message.text = "🚨 Check for all timeframes Alerts"
    context = MagicMock()

    await bot.handle_buttons(mock_update, context)

    # Verify correct interactions
    mock_crypto_bot.reload_the_data.assert_called_once()
    mock_crypto_bot.get_my_crypto.assert_called_once()
    mock_crypto_bot.check_for_major_updates.assert_called_once_with(None, mock_update)


@pytest.mark.asyncio
async def test_handle_buttons_invalid_command(price_alert_bot, mock_update):
    """Test handling an invalid button press"""
    bot, _ = price_alert_bot
    mock_update.message.text = "Invalid Command"
    context = MagicMock()

    await bot.handle_buttons(mock_update, context)

    mock_update.message.reply_text.assert_called_once_with(
        "❌ Invalid command. Please use the buttons below."
    )


def test_run_bot(price_alert_bot):
    """Test the run_bot method"""
    bot, _ = price_alert_bot

    with patch(
        "src.bots.crypto_price_alerts_bot.LoadVariables.load"
    ) as mock_load_vars, patch(
        "src.bots.crypto_price_alerts_bot.Application"
    ) as mock_application:
        # Mock the variables loading
        mock_load_vars.return_value = {"TELEGRAM_API_TOKEN_ALERTS": "test_token"}

        # Mock the application builder pattern
        mock_app = MagicMock()
        mock_application.builder.return_value.token.return_value.build.return_value = (
            mock_app
        )

        # Call the method
        bot.run_bot()

        # Verify application was built with correct token
        mock_application.builder.return_value.token.assert_called_once_with(
            "test_token"
        )

        # Verify handlers were added
        assert mock_app.add_handler.call_count == 2

        # Verify app was started
        mock_app.run_polling.assert_called_once()
