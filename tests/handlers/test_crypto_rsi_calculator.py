"""
Test suite for CryptoRSICalculator class
"""

# pylint:disable=unused-variable,redefined-outer-name

from unittest.mock import MagicMock, patch

import pytest

from src.handlers.crypto_rsi_calculator import CryptoRSICalculator


@pytest.fixture
def calculator():
    """
    Fixture to create an instance of CryptoRSICalculator with mocked exchange.
    """
    with patch("src.handlers.crypto_rsi_calculator.get_exchange") as mock_get_exchange:
        mock_exchange = MagicMock()
        mock_get_exchange.return_value = mock_exchange
        return CryptoRSICalculator(load_markets=False)


def test_init_loads_markets():
    """
    Test that CryptoRSICalculator initializes and loads markets if specified.
    """
    with patch(
        "src.handlers.crypto_rsi_calculator.get_exchange"
    ) as mock_get_exchange, patch.object(
        CryptoRSICalculator, "_load_markets"
    ) as mock_load_markets:
        CryptoRSICalculator(load_markets=True)
        mock_load_markets.assert_called_once()


def test_fetch_ohlcv_uses_cache(calculator):
    """
    Test that fetch_ohlcv uses cache if available and use_cache is True.
    """
    calculator.ohlcv_cache["BTC/USDT_1h_100"] = ([1, 2, 3], calculator.last_cache_clear)
    result = calculator.fetch_ohlcv("BTC/USDT", "1h", 100, use_cache=True)
    assert result == [1, 2, 3]


def test_fetch_ohlcv_calls_exchange(calculator):
    """
    Test that fetch_ohlcv calls the exchange when cache is not used or cache is stale.
    """
    calculator.exchange.fetch_ohlcv.return_value = [[0, 0, 0, 0, 1]] * 20
    result = calculator.fetch_ohlcv("BTC/USDT", "1h", 20, use_cache=False)
    calculator.exchange.fetch_ohlcv.assert_called_once_with("BTC/USDT", "1h", limit=20)
    assert result == [[0, 0, 0, 0, 1]] * 20


def test_calculate_rsi_returns_none_for_short_data(calculator):
    """
    Test that calculate_rsi returns None if there is not enough data to calculate RSI.
    """
    assert calculator.calculate_rsi([[0, 0, 0, 0, 1]] * 5) is None


def test_calculate_rsi_returns_value(calculator):
    """
    Test that calculate_rsi returns a float value when there is enough data.
    """
    # Simulate a rising close price
    ohlcv = [[0, 0, 0, 0, float(i)] for i in range(16)]
    rsi = calculator.calculate_rsi(ohlcv)
    assert isinstance(rsi, float)


def test_get_rsi_for_pairs_calls_methods(calculator):
    """
    Test that get_rsi_for_pairs calls fetch_ohlcv and calculate_rsi for each pair.
    """
    calculator.tradable_pairs = ["BTC/USDT", "ETH/USDT"]
    calculator.fetch_ohlcv = MagicMock(return_value=[[0, 0, 0, 0, 1]] * 20)
    calculator.calculate_rsi = MagicMock(return_value=55.0)
    result = calculator.get_rsi_for_pairs("1h", use_cache=True)
    assert result == {"BTC/USDT": 55.0, "ETH/USDT": 55.0}


def test_get_overbought_oversold_pairs(calculator):
    """
    Test that get_overbought_oversold_pairs correctly categorizes pairs based on RSI values.
    """
    rsi_values = {"BTC/USDT": 80, "ETH/USDT": 20, "XRP/USDT": 50}
    overbought, oversold = calculator.get_overbought_oversold_pairs(rsi_values)
    assert ("BTC/USDT", 80) in overbought
    assert ("ETH/USDT", 20) in oversold
    assert all(pair[0] != "XRP/USDT" for pair in overbought + oversold)


def test_calculate_rsi_for_timeframes(calculator):
    """
    Test that calculate_rsi_for_timeframes returns a summary with overbought and oversold pairs.
    """
    calculator.tradable_pairs = ["BTC/USDT"]
    calculator.get_rsi_for_pairs = MagicMock(return_value={"BTC/USDT": 75})
    summary = calculator.calculate_rsi_for_timeframes("1h")
    assert summary["overbought"] == [("BTC/USDT", 75)]
    assert summary["oversold"] == []
    assert summary["rsi_values"] == {"BTC/USDT": 75}


@pytest.mark.asyncio
async def test_calculate_rsi_for_timeframes_parallel(calculator):
    """
    Test that calculate_rsi_for_timeframes_parallel returns RSI values for multiple pairs.
    """
    expected = {"values": {"BTC/USDT": 80, "ETH/USDT": 25}}
    with patch.object(
        calculator, "_calculate_rsi_for_timeframes", return_value=expected
    ):
        result = await calculator.calculate_rsi_for_timeframes_parallel("1h")
        assert result["values"] == {"BTC/USDT": 80, "ETH/USDT": 25}
