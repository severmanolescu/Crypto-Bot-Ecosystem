"""
Test suite for the data_fetcher_handler module.
Tests fetching Ethereum gas fees and Crypto Fear & Greed Index data.
"""

from unittest.mock import patch

import pytest

from src.handlers.data_fetcher_handler import (
    get_eth_gas_fee,
    get_fear_and_greed,
    get_fear_and_greed_message,
)


@pytest.mark.parametrize(
    "mock_data,expected_result",
    [
        (
            {
                "status": "1",
                "result": {
                    "SafeGasPrice": "20",
                    "ProposeGasPrice": "25",
                    "FastGasPrice": "30",
                },
            },
            ("20", "25", "30"),
        ),
        ({"status": "0", "message": "Error"}, (None, None, None)),
        (None, (None, None, None)),
    ],
)
def test_get_eth_gas_fee(mock_data, expected_result):
    """
    Test the get_eth_gas_fee function with various API responses.
    """
    with patch(
        "src.handlers.data_fetcher_handler.check_requests", return_value=mock_data
    ):
        result = get_eth_gas_fee("https://api.etherscan.io/api")
        assert result == expected_result


def test_get_eth_gas_fee_key_error():
    """
    Test the get_eth_gas_fee function when a KeyError occurs.
    """
    # Missing required keys in the response
    mock_data = {"status": "1", "result": {"IncompleteData": "value"}}

    with patch(
        "src.handlers.data_fetcher_handler.check_requests", return_value=mock_data
    ):
        result = get_eth_gas_fee("https://api.etherscan.io/api")
        assert result == (None, None, None)


@pytest.mark.asyncio
@patch("src.handlers.data_fetcher_handler.check_requests")
async def test_get_fear_and_greed_message_success(mock_check_requests):
    """
    Test the get_fear_and_greed_message function with a successful API response.
    """
    # Mock timestamp that translates to "2023-05-15 12:00:00"
    timestamp = 1684152000
    mock_data = {
        "data": [
            {"value": "25", "value_classification": "Fear", "timestamp": str(timestamp)}
        ]
    }

    mock_check_requests.return_value = mock_data

    result = await get_fear_and_greed_message()

    # Verify the message contains expected information
    assert "Crypto Fear & Greed Index" in result, "Expected title in the message"
    assert "<b>Score</b>: 25" in result, "Expected score to be '25'"
    assert "<b>Sentiment</b>: Fear" in result, "Expected sentiment to be 'Fear'"
    assert (
        "2023-05-15 12:00:00" in result
    ), "Expected last update date to be '2023-05-15 12:00:00'"
    assert "#FearAndGreed" in result, "Expected hashtag #FearAndGreed in the message"


@pytest.mark.asyncio
@patch("src.handlers.data_fetcher_handler.check_requests")
async def test_get_fear_and_greed_message_failure(mock_check_requests):
    """
    Test the get_fear_and_greed_message function when the API request fails.
    """
    mock_check_requests.return_value = None

    result = await get_fear_and_greed_message()

    assert (
        result == "❌ Error during the data request"
    ), "Expected error message when API request fails"


@pytest.mark.asyncio
@patch("src.handlers.data_fetcher_handler.check_requests")
async def test_get_fear_and_greed_success(mock_check_requests):
    """
    Test the get_fear_and_greed function with a successful API response.
    """
    # Mock timestamp that translates to "2023-05-15 12:00:00"
    timestamp = 1684152000
    mock_data = {
        "data": [
            {
                "value": "75",
                "value_classification": "Greed",
                "timestamp": str(timestamp),
            }
        ]
    }

    mock_check_requests.return_value = mock_data

    index_value, index_text, last_update_date = await get_fear_and_greed()

    assert index_value == "75", "Expected index value to be '75'"
    assert index_text == "Greed", "Expected index text to be 'Greed'"
    assert (
        last_update_date == "2023-05-15 12:00:00"
    ), "Expected last update date to be '2023-05-15 12:00:00'"


@pytest.mark.asyncio
@patch("src.handlers.data_fetcher_handler.check_requests")
async def test_get_fear_and_greed_failure(mock_check_requests):
    """
    Test the get_fear_and_greed function when the API request fails.
    """
    mock_check_requests.return_value = None

    index_value, index_text, last_update_date = await get_fear_and_greed()

    assert index_value is None
    assert index_text is None
    assert last_update_date is None
