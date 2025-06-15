"""
Alert handler tests.
"""

# pylint: disable=redefined-outer-name

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.alerts_handler import AlertsHandler


@pytest.fixture
def alerts_handler():
    """Fixture to create a mocked AlertsHandler for testing."""
    with patch("src.handlers.alerts_handler.LoadVariables") as mock_load_vars:
        # Mock the variables that would be loaded from LoadVariables
        mock_load_vars.load.return_value = {
            "TELEGRAM_API_TOKEN_ALERTS": "test_token",
            "ALERT_THRESHOLD_1H": 2.5,
            "ALERT_THRESHOLD_24H": 5,
            "ALERT_THRESHOLD_7D": 10,
            "ALERT_THRESHOLD_30D": 10,
            "24H_ALERTS_SEND_HOURS": [8, 16],
            "7D_ALERTS_SEND_HOURS": [8],
            "30D_ALERTS_SEND_HOURS": [8],
        }

        # Create handler instance with mocked reload_the_data
        handler = AlertsHandler()

        # Mock the TelegramMessagesHandler
        handler.telegram_message = MagicMock()
        handler.telegram_message.send_telegram_message = AsyncMock()

        yield handler


@pytest.mark.asyncio
async def test_check_for_major_updates_1h_with_alerts(alerts_handler):
    """Test check_for_major_updates_1h when significant price changes are detected."""
    # Mock data with significant price changes
    mock_crypto_data = {
        "BTC": {"change_1h": 3.5},  # Above threshold
        "ETH": {"change_1h": -4.0},  # Above threshold
        "XRP": {"change_1h": 1.0},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_1h(mock_crypto_data)

    # Verify results
    assert result is True

    # Verify the telegram message was sent with appropriate content
    alerts_handler.telegram_message.send_telegram_message.assert_called_once()

    # Verify the message contains the cryptocurrencies with significant changes
    call_args = alerts_handler.telegram_message.send_telegram_message.call_args[0]
    message = call_args[0]
    assert "BTC" in message
    assert "ETH" in message
    assert "XRP" not in message


@pytest.mark.asyncio
async def test_check_for_major_updates_1h_without_alerts(alerts_handler):
    """Test check_for_major_updates_1h when no significant price changes are detected."""
    # Mock data with no significant price changes
    mock_crypto_data = {
        "BTC": {"change_1h": 1.0},  # Below threshold
        "ETH": {"change_1h": -2.0},  # Below threshold
        "XRP": {"change_1h": 0.5},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_1h(mock_crypto_data)

    # Verify results
    assert result is False

    # Verify no telegram message was sent
    alerts_handler.telegram_message.send_telegram_message.assert_not_called()


@pytest.mark.asyncio
async def test_check_for_major_updates_24h_with_alerts(alerts_handler):
    """Test check_for_major_updates_24h when significant price changes are detected."""
    # Mock data with significant price changes
    mock_crypto_data = {
        "BTC": {"change_24h": 6.0},  # Above threshold
        "ETH": {"change_24h": -7.0},  # Above threshold
        "XRP": {"change_24h": 2.0},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_24h(mock_crypto_data)

    # Verify results
    assert result is True

    # Verify the telegram message was sent with appropriate content
    alerts_handler.telegram_message.send_telegram_message.assert_called_once()

    # Verify the message contains the cryptocurrencies with significant changes
    call_args = alerts_handler.telegram_message.send_telegram_message.call_args[0]
    message = call_args[0]
    assert "BTC" in message
    assert "ETH" in message
    assert "XRP" not in message


@pytest.mark.asyncio
async def test_check_for_major_updates_24h_without_alerts(alerts_handler):
    """Test check_for_major_updates_24h when no significant price changes are detected."""
    # Mock data with no significant price changes
    mock_crypto_data = {
        "BTC": {"change_24h": 3.0},  # Below threshold
        "ETH": {"change_24h": -4.0},  # Below threshold
        "XRP": {"change_24h": 1.5},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_24h(mock_crypto_data)

    # Verify results
    assert result is False

    # Verify no telegram message was sent
    alerts_handler.telegram_message.send_telegram_message.assert_not_called()


@pytest.mark.asyncio
async def test_check_for_major_updates_7d_with_alerts(alerts_handler):
    """Test check_for_major_updates_7d when significant price changes are detected."""
    # Mock data with significant price changes
    mock_crypto_data = {
        "BTC": {"change_7d": 12.0},  # Above threshold
        "ETH": {"change_7d": -15.0},  # Above threshold
        "XRP": {"change_7d": 3.0},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_7d(mock_crypto_data)

    # Verify results
    assert result is True

    # Verify the telegram message was sent with appropriate content
    alerts_handler.telegram_message.send_telegram_message.assert_called_once()

    # Verify the message contains the cryptocurrencies with significant changes
    call_args = alerts_handler.telegram_message.send_telegram_message.call_args[0]
    message = call_args[0]
    assert "BTC" in message
    assert "ETH" in message
    assert "XRP" not in message


@pytest.mark.asyncio
async def test_check_for_major_updates_7d_without_alerts(alerts_handler):
    """Test check_for_major_updates_7d when no significant price changes are detected."""
    # Mock data with no significant price changes
    mock_crypto_data = {
        "BTC": {"change_7d": 5.0},  # Below threshold
        "ETH": {"change_7d": -6.0},  # Below threshold
        "XRP": {"change_7d": 2.0},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_7d(mock_crypto_data)

    # Verify results
    assert result is False

    # Verify no telegram message was sent
    alerts_handler.telegram_message.send_telegram_message.assert_not_called()


@pytest.mark.asyncio
async def test_check_for_major_updates_30d_with_alerts(alerts_handler):
    """Test check_for_major_updates_30d when significant price changes are detected."""
    # Mock data with significant price changes
    mock_crypto_data = {
        "BTC": {"change_30d": 20.0},  # Above threshold
        "ETH": {"change_30d": -25.0},  # Above threshold
        "XRP": {"change_30d": 4.0},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_30d(mock_crypto_data)

    # Verify results
    assert result is True

    # Verify the telegram message was sent with appropriate content
    alerts_handler.telegram_message.send_telegram_message.assert_called_once()

    # Verify the message contains the cryptocurrencies with significant changes
    call_args = alerts_handler.telegram_message.send_telegram_message.call_args[0]
    message = call_args[0]
    assert "BTC" in message
    assert "ETH" in message
    assert "XRP" not in message


@pytest.mark.asyncio
async def test_check_for_major_updates_30d_without_alerts(alerts_handler):
    """Test check_for_major_updates_30d when no significant price changes are detected."""
    # Mock data with no significant price changes
    mock_crypto_data = {
        "BTC": {"change_30d": 4.0},  # Below threshold
        "ETH": {"change_30d": -7.0},  # Below threshold
        "XRP": {"change_30d": 3.0},  # Below threshold
    }

    # Call the method under test
    result = await alerts_handler.check_for_major_updates_30d(mock_crypto_data)

    # Verify results
    assert result is False

    # Verify no telegram message was sent
    alerts_handler.telegram_message.send_telegram_message.assert_not_called()


@pytest.mark.asyncio
async def test_check_for_alerts(alerts_handler):
    """Test check_for_alerts method with various timeframes."""
    # Mock data with significant price changes
    mock_crypto_data = {
        "BTC": {
            "change_1h": 3.5,
            "change_24h": 6.0,
            "change_7d": 12.0,
            "change_30d": 20.0,
        },
        "ETH": {
            "change_1h": -4.0,
            "change_24h": -7.0,
            "change_7d": -15.0,
            "change_30d": -25.0,
        },
        "XRP": {
            "change_1h": 1.0,
            "change_24h": 2.0,
            "change_7d": 3.0,
            "change_30d": 4.0,
        },
    }

    # Call the method under test
    now_date = None
    result = await alerts_handler.check_for_alerts(now_date, mock_crypto_data)

    # Verify results
    assert result is True

    # Verify the telegram message was sent for all significant changes
    alerts_handler.telegram_message.send_telegram_message.assert_called()
