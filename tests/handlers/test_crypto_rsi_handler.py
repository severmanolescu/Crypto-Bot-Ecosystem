"""
Test cases for CryptoRSIHandler
"""

# pylint:disable=unused-variable,redefined-outer-name

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.crypto_rsi_handler import CryptoRSIHandler


@pytest.fixture
def handler():
    """
    Fixture to create an instance of CryptoRSIHandler with mocked TelegramMessagesHandler.
    """
    with patch(
        "src.handlers.crypto_rsi_handler.TelegramMessagesHandler"
    ) as mock_telegram:
        return CryptoRSIHandler()


def test_prepare_message_for_timeframes_parallel_success(handler):
    """
    Test the prepare_message_for_timeframes_parallel method for successful RSI calculation.
    """
    with patch("src.handlers.crypto_rsi_handler.CryptoRSICalculator") as mock_calc:
        mock_calc.return_value.calculate_rsi_for_timeframes_parallel.return_value = {
            "values": {"BTC": 80}
        }
        result = handler.prepare_message_for_timeframes_parallel("1h")
        assert result == {"values": {"BTC": 80}}


def test_prepare_message_for_timeframes_parallel_exception(handler, caplog):
    """
    Test the prepare_message_for_timeframes_parallel method when an exception occurs.
    """
    with patch(
        "src.handlers.crypto_rsi_handler.CryptoRSICalculator",
        side_effect=Exception("fail"),
    ):
        result = handler.prepare_message_for_timeframes_parallel("1h")
        assert result == {}
        assert "Error calculating RSI" in caplog.text


def test_send_new_rsi_to_telegram_sets_message(handler):
    """
    Test the send_new_rsi_to_telegram method sets the message correctly
    when RSI data is provided.
    """
    rsi_data = {"values": {"BTC": 80, "ETH": 20, "XRP": 50}}
    handler.send_new_rsi_to_telegram(rsi_data)
    assert "BTC" in handler.message
    assert "ETH" in handler.message
    assert "XRP" not in handler.message


def test_send_new_rsi_to_telegram_no_data(handler):
    """
    Test the send_new_rsi_to_telegram method when no RSI data is provided.
    """
    handler.send_new_rsi_to_telegram({})
    assert "error" in handler.message.lower()


def test_send_json_rsi_to_telegram_sets_message(handler):
    """
    Test the send_json_rsi_to_telegram method sets the message correctly
    when RSI data is provided in JSON format.
    """
    handler.json = {"1h": {"values": {"BTC": 60}}}
    handler.send_json_rsi_to_telegram("1h")
    assert "BTC" in handler.message


def test_send_json_rsi_to_telegram_no_data(handler):
    """
    Test the send_json_rsi_to_telegram method when no RSI data is available.
    """
    handler.json = {}
    handler.send_json_rsi_to_telegram("1h")
    assert "error" in handler.message.lower()


@pytest.mark.asyncio
async def test_send_rsi_to_telegram_sends_message(handler):
    """
    Test the send_rsi_to_telegram method to ensure it sends a message via Telegram.
    """
    handler.message = "test"
    bot = MagicMock()
    with patch(
        "src.handlers.crypto_rsi_handler.TelegramMessagesHandler"
    ) as mock_telegram:
        mock_telegram.return_value.send_telegram_message = AsyncMock()
        await handler.send_rsi_to_telegram(bot)
        mock_telegram.return_value.send_telegram_message.assert_awaited()


def test_check_if_should_calculate_rsi_true(handler):
    """
    Test the check_if_should_calculate_rsi method to ensure
    it sets should_calculate_rsi to True
    when the last calculation was more than 10 minutes ago.
    """

    now = datetime.now(timezone.utc) - timedelta(minutes=10)
    handler.json = {"1h": {"date": now.strftime("%Y-%m-%dT%H:%M:%SZ")}}
    handler.check_if_should_calculate_rsi("1h")
    assert handler.should_calculate_rsi


def test_check_if_should_calculate_rsi_false(handler):
    """
    Test the check_if_should_calculate_rsi method to ensure
    """

    now = datetime.now(timezone.utc)
    handler.json = {"1h": {"date": now.strftime("%Y-%m-%dT%H:%M:%SZ")}}
    handler.check_if_should_calculate_rsi("1h")
    assert not handler.should_calculate_rsi


def test_check_if_should_calculate_rsi_exception(handler):
    """
    Test the check_if_should_calculate_rsi method to ensure it handles
    """
    handler.json = {"1h": {"date": "bad-date"}}
    handler.check_if_should_calculate_rsi("1h")
    assert handler.should_calculate_rsi


@pytest.mark.asyncio
async def test_send_rsi_for_timeframe_should_calculate(handler):
    """
    Test the send_rsi_for_timeframe method when RSI should be calculated.
    """
    handler.should_calculate_rsi = True
    with patch(
        "src.handlers.crypto_rsi_handler.load_json",
        return_value={"1h": {"date": "2020-01-01T00:00:00Z"}},
    ), patch.object(handler, "reload_data"), patch.object(
        handler, "check_if_should_calculate_rsi"
    ), patch.object(
        handler,
        "prepare_message_for_timeframes_parallel",
        return_value={"values": {"BTC": 80}},
    ), patch.object(
        handler, "send_new_rsi_to_telegram"
    ) as mock_send_new_rsi, patch(
        "src.handlers.crypto_rsi_handler.save_new_rsi_data"
    ), patch.object(
        handler, "send_rsi_to_telegram", new=AsyncMock()
    ), patch.object(
        handler.telegram_handler, "send_telegram_message", new=AsyncMock()
    ):
        await handler.send_rsi_for_timeframe("1h", MagicMock())
        mock_send_new_rsi.assert_called_once()


@pytest.mark.asyncio
async def test_send_rsi_for_timeframe_should_not_calculate(handler):
    """
    Test the send_rsi_for_timeframe method when RSI should not be calculated.
    """
    handler.should_calculate_rsi = False
    with patch(
        "src.handlers.crypto_rsi_handler.load_json",
        return_value={"1h": {"date": "2020-01-01T00:00:00Z"}},
    ), patch.object(handler, "reload_data"), patch.object(
        handler, "check_if_should_calculate_rsi"
    ), patch.object(
        handler, "send_json_rsi_to_telegram"
    ) as mock_send_json, patch.object(
        handler, "send_rsi_to_telegram", new=AsyncMock()
    ), patch.object(
        handler.telegram_handler, "send_telegram_message", new=AsyncMock()
    ):
        await handler.send_rsi_for_timeframe("1h", MagicMock())
        mock_send_json.assert_called_once()
