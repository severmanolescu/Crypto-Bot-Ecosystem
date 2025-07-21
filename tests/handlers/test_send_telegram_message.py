"""
Test suite for the send_telegram_message module in the src.handlers package.
This suite tests the sending of messages to Telegram.
"""

# pylint: disable=unused-variable

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest

from src.handlers.send_telegram_message import (
    TelegramMessagesHandler,
    send_plot_to_telegram,
    send_telegram_message_update,
)


@pytest.mark.asyncio
async def test_send_telegram_message_update():
    """
    Test sending a message using the update object.
    """
    # Create a mock update object
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()

    # Call the function
    test_message = "Test message"
    await send_telegram_message_update(test_message, mock_update)

    # Verify the message was sent
    mock_update.message.reply_text.assert_called_once_with(
        test_message, parse_mode="HTML"
    )


@pytest.mark.asyncio
async def test_send_plot_to_telegram():
    """
    Test sending a plot image to Telegram.
    """
    # Create a mock update object
    mock_update = MagicMock()
    mock_update.message.reply_photo = AsyncMock()

    # Mock file opening
    test_image_path = "test_image.png"
    mock_file = MagicMock()

    with patch("builtins.open", mock_open(read_data=b"image_data")) as mock_file_open:
        await send_plot_to_telegram(test_image_path, mock_update)

        # Verify the file was opened
        mock_file_open.assert_called_once_with(test_image_path, "rb")

        # Verify the photo was sent
        mock_update.message.reply_photo.assert_called_once()


@pytest.mark.asyncio
async def test_telegram_messages_handler_init():
    """
    Test the initialization of the TelegramMessagesHandler class.
    """
    with patch("src.handlers.send_telegram_message.load_json") as mock_load:
        # Setup mock return value for load_variables
        mock_load.return_value = {
            "TELEGRAM_CHAT_ID_FULL_DETAILS": ["id1", "id2"],
            "TELEGRAM_CHAT_ID_PARTIAL_DATA": ["id3"],
            "ETHERSCAN_GAS_API_URL": "https://api.etherscan.io/api?",
            "ETHERSCAN_API_KEY": "test_key",
        }

        # Initialize the handler
        handler = TelegramMessagesHandler()

        # Verify the variables were loaded correctly
        assert handler.telegram_important_chat_id == ["id1", "id2"]
        assert handler.telegram_not_important_chat_id == ["id3"]
        assert handler.etherscan_api_url == "https://api.etherscan.io/api?test_key"


@pytest.mark.asyncio
async def test_send_telegram_message_with_update():
    """
    Test sending a Telegram message with an update object.
    """
    # Create handler and mock update
    handler = TelegramMessagesHandler()
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()

    # Call the function
    test_message = "Test message with update"
    await handler.send_telegram_message(
        test_message, "test_bot_token", False, mock_update
    )

    # Verify update.message.reply_text was called
    mock_update.message.reply_text.assert_called_once_with(
        test_message, parse_mode="HTML"
    )


@pytest.mark.asyncio
async def test_send_telegram_message_without_update():
    """
    Test sending a Telegram message without an update object.
    """
    # Create handler
    handler = TelegramMessagesHandler()
    mock_bot = AsyncMock()

    # This is the correct way to patch the Bot constructor
    with patch(
        "src.handlers.send_telegram_message.Bot", return_value=mock_bot
    ) as mock_bot_class:
        # Setup chat IDs
        handler.telegram_important_chat_id = ["id1", "id2"]
        handler.telegram_not_important_chat_id = ["id3"]

        # Call the function for non-important message
        test_message = "Test message without update"
        await handler.send_telegram_message(test_message, "test_bot_token", False)

        # Verify Bot was initialized with the token
        mock_bot_class.assert_called_once_with(token="test_bot_token")

        # Verify messages were sent to all chats
        assert mock_bot.send_message.call_count == 3

        # Reset mocks for the next test
        mock_bot.reset_mock()
        mock_bot_class.reset_mock()

        # Test important message
        await handler.send_telegram_message(test_message, "test_bot_token", True)
        mock_bot_class.assert_called_once_with(token="test_bot_token")

        # Only important chats should receive it
        assert mock_bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_send_eth_gas_fee():
    """
    Test fetching and sending Ethereum gas fees.
    """
    # Create handler
    handler = TelegramMessagesHandler()
    handler.send_telegram_message = AsyncMock()

    # Mock the gas fee retrieval
    gas_values = (10, 20, 30)  # (safe, propose, fast)

    with patch(
        "src.handlers.send_telegram_message.get_eth_gas_fee", return_value=gas_values
    ):
        # Call the function
        await handler.send_eth_gas_fee("test_token")

        # Verify send_telegram_message was called with expected message
        expected_message = (
            "⛽ <b>ETH Gas Fees (Gwei)</b>:\n"
            "🐢 Safe: 10\n"
            "🚗 Propose: 20\n"
            "🚀 Fast: 30\n\n"
            "#GasFee"
        )
        handler.send_telegram_message.assert_called_once_with(
            expected_message, "test_token", False, None
        )


@pytest.mark.asyncio
async def test_send_market_update():
    """
    Test sending market updates.
    """
    # Create handler
    handler = TelegramMessagesHandler()
    handler.send_telegram_message = AsyncMock()
    handler.open_ai_prompt = MagicMock()
    handler.open_ai_prompt.get_response = AsyncMock(return_value="AI summary text")

    now_date = datetime(2023, 1, 1, 12, 0)

    my_crypto = {
        "BTC": {
            "price": 50000.0,
            "change_1h": 1.5,
            "change_24h": 2.0,
            "change_7d": -0.5,
            "change_30d": 10.0,
        },
        "ETH": {
            "price": 3000.0,
            "change_1h": -0.5,
            "change_24h": 1.0,
            "change_7d": 5.0,
            "change_30d": 15.0,
        },
    }

    await handler.send_market_update("test_token", now_date, my_crypto)

    # Verify send_telegram_message was called
    handler.send_telegram_message.assert_called_once()

    handler.send_telegram_message.reset_mock()

    await handler.send_market_update("test_token", now_date, my_crypto)

    # Verify send_telegram_message was still called
    handler.send_telegram_message.assert_called_once()
