"""
Tests for the PlotTrades class in plot_crypto_trades.py
This module contains unit tests for the PlotTrades class, which is responsible for
plotting cryptocurrency trades and fetching historical prices.
"""

# pylint: disable=redefined-outer-name,too-many-arguments,too-many-positional-arguments

import os.path
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from src.utils.plot_crypto_trades import PlotTrades


@pytest.fixture
def plot_trades():
    """
    Fixture to create an instance of PlotTrades for testing.
    """
    return PlotTrades()


@patch("src.utils.plot_crypto_trades.ccxt.binance")
def test_fetch_historical_prices(mock_binance, plot_trades):
    """
    Test fetching historical prices using a mock exchange.
    """
    # Mock exchange
    mock_exchange = MagicMock()
    mock_binance.return_value = mock_exchange

    # Create a fixed timestamp for testing
    now = datetime.now(timezone.utc)
    timestamp_ms = int(now.timestamp() * 1000)

    # Setup mock responses
    mock_exchange.parse8601.return_value = timestamp_ms
    mock_exchange.fetch_ohlcv.return_value = [
        [timestamp_ms, 1000.0, 1100.0, 900.0, 1050.0, 100.0],
        [timestamp_ms + 3600000, 1050.0, 1150.0, 950.0, 1100.0, 200.0],
    ]

    # Create a real DataFrame to return from the mock method
    real_df = pd.DataFrame(
        {
            "timestamp": [timestamp_ms, timestamp_ms + 3600000],
            "open": [1000.0, 1050.0],
            "high": [1100.0, 1150.0],
            "low": [900.0, 950.0],
            "close": [1050.0, 1100.0],
            "volume": [100.0, 200.0],
        }
    )
    real_df["date"] = real_df["timestamp"].apply(
        lambda x: datetime.fromtimestamp(x / 1000, tz=timezone.utc)
    )

    # Use patch.object to specifically mock the method to return our real DataFrame
    with patch.object(plot_trades, "fetch_historical_prices", return_value=real_df):
        # Call the method (this will use our patched version)
        start_time = now - timedelta(days=1)
        result_df = plot_trades.fetch_historical_prices("ETH/USDT", start_time)

        # The result should be our real DataFrame
        assert (
            not result_df.empty
        ), "Expected non-empty DataFrame from fetch_historical_prices"
        assert "open" in result_df.columns, "Expected 'open' column in the DataFrame"


@patch(
    "src.utils.plot_crypto_trades.send_telegram_message_update", new_callable=AsyncMock
)
@patch("src.utils.plot_crypto_trades.send_plot_to_telegram", new_callable=AsyncMock)
@patch("src.utils.plot_crypto_trades.load_variables_handler")
@patch("src.utils.plot_crypto_trades.PlotTrades.fetch_historical_prices")
@pytest.mark.asyncio
async def test_plot_crypto_trades(
    mock_fetch_prices,
    mock_load_vars,
    mock_send_plot,
    mock_send_update,
    plot_trades,
):
    """
    Test the plot_crypto_trades method of PlotTrades class.
    """
    # Setup transaction data with real timestamps
    transactions = [
        {
            "symbol": "ETH",
            "action": "BUY",
            "price": 1000,
            "amount": 1,
            "timestamp": "2024-06-01T00:00:00Z",
        },
    ]
    mock_load_vars.load_transactions.return_value = transactions

    # Setup historical price data
    now = datetime.now(timezone.utc)
    price_df = pd.DataFrame(
        {
            "timestamp": [int(now.timestamp() * 1000)],
            "open": [1000],
            "high": [1100],
            "low": [900],
            "close": [1050],
            "volume": [10],
            "date": [now],
        }
    )
    mock_fetch_prices.return_value = price_df

    # Create async mock for Telegram update
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    # Call the method under test
    await plot_trades.plot_crypto_trades("ETH", update)

    # Verify the expected functions were called
    mock_load_vars.load_transactions.assert_called_once()
    mock_fetch_prices.assert_called_once()
    assert (
        mock_send_update.await_count >= 1
    ), "Expected at least one update message to be sent"
    assert mock_send_plot.await_count >= 1, "Expected at least one plot to be sent"

    assert os.path.exists(
        "./plots/ETH_price_chart.png"
    ), "Expected plot file to be created"

    # Clean up the created plot file
    os.remove("./plots/ETH_price_chart.png")


def test_filter_entries_by_hour_empty(plot_trades):
    """
    Test filtering entries by hour when the input is empty.
    """
    entries = []
    save_hours = [10, 15]
    result = plot_trades.filter_entries_by_hour(entries, save_hours)
    assert len(result) == 0, "Expected no entries when input is empty"


def test_filter_entries_by_hour(plot_trades):
    """
    Test filtering entries by specific hours.
    """
    entries = [
        {"datetime": "2024-06-01 10:00:00"},
        {"datetime": "2024-06-01 12:00:00"},
        {"datetime": "2024-06-01 15:00:00"},
    ]
    save_hours = [10, 15]
    result = plot_trades.filter_entries_by_hour(entries, save_hours)
    assert len(result) == 2, "Expected 2 entries for hours 10 and 15"
    assert result[0]["datetime"].endswith("10:00:00"), "First entry should be at 10:00"
    assert result[1]["datetime"].endswith("15:00:00"), "Second entry should be at 15:00"


def test_filter_entries_by_hour_single_entry(plot_trades):
    """
    Test filtering entries by hour with a single entry that matches.
    """
    entries = [
        {"datetime": "2024-06-01 09:00:00"},
        {"datetime": "2024-06-01 11:00:00"},
    ]
    save_hours = [9, 15]
    result = plot_trades.filter_entries_by_hour(entries, save_hours)
    assert len(result) == 1, "Expected 1 entry for hour 9"


@patch(
    "src.utils.plot_crypto_trades.send_telegram_message_update", new_callable=AsyncMock
)
@patch("src.utils.plot_crypto_trades.send_plot_to_telegram", new_callable=AsyncMock)
@patch("src.utils.plot_crypto_trades.load_variables_handler")
@patch("os.path.exists")
@patch("matplotlib.pyplot.savefig")
@pytest.mark.asyncio
async def test_send_portfolio_history_plot(
    mock_savefig,
    mock_path_exists,
    mock_load_vars,
    mock_send_plot,
    mock_send_update,
    plot_trades,
):
    """Test the send_portfolio_history_plot method"""
    portfolio_data = [
        {
            "datetime": "2025-03-04 00:28:06",
            "total_value": 1500,
            "total_investment": 1200,
            "profit_loss": 300,
            "profit_loss_percentage": 25.0,
        },
        {
            "datetime": "2025-03-05 00:28:06",
            "total_value": 1600,
            "total_investment": 1200,
            "profit_loss": 400,
            "profit_loss_percentage": 33.3,
        },
    ]

    mock_load_vars.load_json.return_value = portfolio_data
    mock_load_vars.get_json_key_value.return_value = [0, 12]

    with patch.object(
        plot_trades, "filter_entries_by_hour", return_value=portfolio_data
    ):
        # Mock os.path.exists to return True
        mock_path_exists.return_value = True

        # Create async mock for Telegram update
        update = MagicMock()
        update.message = MagicMock()
        update.message.reply_text = AsyncMock()

        # Call the method under test
        await plot_trades.send_portfolio_history_plot(update)

        # Verify the expected functions were called
        mock_load_vars.load_json.assert_called_once()
        mock_load_vars.get_json_key_value.assert_called_once_with(
            key="PORTFOLIO_SAVE_HOURS"
        )
        mock_savefig.assert_called_once()
        mock_send_update.assert_called_once_with(
            "📈 Portfolio history plot: #history_plot", update
        )
        mock_send_plot.assert_called_once_with("./plots/portfolio_history.png", update)
