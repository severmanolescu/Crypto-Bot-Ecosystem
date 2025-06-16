"""
Test suite for the PortfolioManager class in the src.handlers.portfolio_manager module.
This suite tests portfolio initialization, value calculations, and update functionality.
"""

# pylint: disable=redefined-outer-name, unused-variable

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.handlers.portfolio_manager import PortfolioManager


@pytest.fixture
def portfolio_manager():
    """Fixture to create a PortfolioManager instance for testing."""
    with patch("src.handlers.send_telegram_message.TelegramMessagesHandler"):
        manager = PortfolioManager()
        manager.telegram_message = AsyncMock()
        return manager


@pytest.fixture
def sample_portfolio():
    """Fixture to provide a sample portfolio for testing."""
    return {
        "BTC": {"quantity": 0.5, "average_price": 40000},
        "ETH": {"quantity": 5, "average_price": 2000},
    }


@pytest.fixture
def sample_crypto_prices():
    """Fixture to provide sample cryptocurrency prices for testing."""
    return {
        "BTC": {"price": 50000, "change_24h": 5.0},
        "ETH": {"price": 3000, "change_24h": 2.5},
    }


def test_init(portfolio_manager):
    """Test the initialization of PortfolioManager."""
    assert portfolio_manager.file_path == "config/portfolio.json"
    assert portfolio_manager.portfolio is None
    assert portfolio_manager.telegram_api_token is None


def test_reload_the_data(portfolio_manager):
    """Test reloading data from configuration files."""
    mock_variables = {"TELEGRAM_API_TOKEN_VALUE": "test_token"}
    mock_portfolio = {"BTC": {"quantity": 0.5, "average_price": 40000}}

    with patch(
        "src.handlers.portfolio_manager.load", return_value=mock_variables
    ), patch(
        "src.handlers.portfolio_manager.load_portfolio_from_file",
        return_value=mock_portfolio,
    ):
        portfolio_manager.reload_the_data()

        assert portfolio_manager.telegram_api_token == "test_token"
        assert portfolio_manager.portfolio == mock_portfolio
        portfolio_manager.telegram_message.reload_the_data.assert_called_once()


def test_save_portfolio_to_file(portfolio_manager, sample_portfolio):
    """Test saving the portfolio to a file."""
    portfolio_manager.portfolio = sample_portfolio

    # Mock the open function
    mock_open = MagicMock()
    with patch("builtins.open", mock_open), patch("json.dump") as mock_json_dump:
        portfolio_manager.save_portfolio_to_file()

        # Check file was opened correctly
        mock_open.assert_called_once_with(
            portfolio_manager.file_path, "w", encoding="utf-8"
        )

        # Check json.dump was called with the right arguments
        mock_json_dump.assert_called_once()
        assert mock_json_dump.call_args[0][0] == sample_portfolio


def test_save_portfolio_to_file_file_not_found(portfolio_manager, sample_portfolio):
    """Test handling FileNotFoundError when saving portfolio."""
    portfolio_manager.portfolio = sample_portfolio

    # Mock the open function to raise FileNotFoundError
    with patch("builtins.open", side_effect=FileNotFoundError), patch(
        "builtins.print"
    ) as mock_print:
        portfolio_manager.save_portfolio_to_file()

        # Check error message was printed
        mock_print.assert_called_once()
        error_message = mock_print.call_args[0][0]
        assert "not found" in error_message


def test_calculate_portfolio_value(
    portfolio_manager, sample_portfolio, sample_crypto_prices
):
    """Test calculating the basic portfolio value."""
    portfolio_manager.portfolio = sample_portfolio

    result = portfolio_manager.calculate_portfolio_value(sample_crypto_prices)

    # Check that the result contains expected values
    assert "Portfolio Value Update" in result
    assert "BTC" in result
    assert "ETH" in result
    assert "$25,000.00" in result  # BTC value
    assert "$15,000.00" in result  # ETH value
    assert "$40,000.00" in result  # Total value


def test_calculate_portfolio_value_detailed(
    portfolio_manager, sample_portfolio, sample_crypto_prices
):
    """Test calculating the detailed portfolio value."""
    portfolio_manager.portfolio = sample_portfolio

    result = portfolio_manager.calculate_portfolio_value_detailed(sample_crypto_prices)

    # Check that the result contains expected values
    assert "Portfolio Value Update" in result
    assert "BTC" in result
    assert "ETH" in result
    assert "Quantity: <b>0.5000</b>" in result
    assert "Average Price: <b>$40,000.0000</b>" in result
    assert "Total Investment: <b>$20,000.00</b>" in result
    assert "Current Value: <b>$25,000.00</b>" in result
    assert "<b>P/L: $5,000.00</b>" in result
    assert "<b>+25.00%</b>" in result  # BTC profit percentage

    assert "Total Portfolio Value: $40,000.00" in result
    assert "Total Investment: $30,000.00" in result
    assert "Total P/L: $10,000.00" in result
    assert "+33.33%" in result  # Total profit percentage

    # Check for UTC timestamp
    assert "Last Update:" in result
    assert "UTC" in result


def test_calculate_portfolio_value_detailed_with_save(
    portfolio_manager, sample_portfolio, sample_crypto_prices
):
    """Test calculating the detailed portfolio value with history saving."""
    portfolio_manager.portfolio = sample_portfolio

    # Mock the save_portfolio_history method
    with patch.object(portfolio_manager, "save_portfolio_history") as mock_save:
        portfolio_manager.calculate_portfolio_value_detailed(
            sample_crypto_prices, save_data=True
        )

        # Check that save_portfolio_history was called with the correct arguments
        mock_save.assert_called_once()
        args = mock_save.call_args[0]
        assert args[0] == 40000.00  # total_value
        assert args[1] == 30000.00  # total_investment
        assert args[2] == 10000.00  # total_profit_loss
        assert args[3] == 33.33333333333333  # total_profit_loss_percentage


def test_save_portfolio_history(portfolio_manager):
    """Test saving portfolio history to a file."""
    # Test values
    total_value = 40000.0
    total_investment = 30000.0
    total_profit_loss = 10000.0
    total_profit_loss_percentage = 33.33

    # Set up a proper mock for datetime with a specific return value for strftime
    mock_now = MagicMock()
    mock_now.strftime.return_value = "2023-01-01 12:00:00"

    mock_datetime = MagicMock()
    mock_datetime.now.return_value = mock_now

    mock_timezone = MagicMock()
    mock_pytz = MagicMock()
    mock_pytz.timezone.return_value = mock_timezone

    # Mock existing history file
    mock_history_data = [{"datetime": "2022-12-31 12:00:00", "total_value": 38000.0}]

    with patch("src.handlers.portfolio_manager.datetime", mock_datetime), patch(
        "src.handlers.portfolio_manager.pytz", mock_pytz
    ), patch("os.path.exists", return_value=True), patch(
        "builtins.open", MagicMock()
    ), patch(
        "json.load", return_value=mock_history_data
    ), patch(
        "json.dump"
    ) as mock_json_dump, patch(
        "builtins.print"
    ) as mock_print:
        portfolio_manager.save_portfolio_history(
            total_value,
            total_investment,
            total_profit_loss,
            total_profit_loss_percentage,
        )

        # Check that json.dump was called with updated history data
        mock_json_dump.assert_called_once()
        updated_history = mock_json_dump.call_args[0][0]

        # Check the original entry is preserved
        assert updated_history[0] == mock_history_data[0]

        # Check the new entry was added with correct values
        new_entry = updated_history[1]
        assert new_entry["total_value"] == total_value
        assert new_entry["total_investment"] == total_investment
        assert new_entry["profit_loss"] == total_profit_loss
        assert new_entry["profit_loss_percentage"] == total_profit_loss_percentage


def test_save_portfolio_history_new_file(portfolio_manager):
    """Test saving portfolio history when file doesn't exist yet."""
    # Test values
    total_value = 40000.0
    total_investment = 30000.0
    total_profit_loss = 10000.0
    total_profit_loss_percentage = 33.33

    # Mock the datetime, pytz, and file operations
    mock_datetime = MagicMock()
    mock_datetime.now.return_value.strftime.return_value = "2023-01-01 12:00:00"

    mock_timezone = MagicMock()
    mock_pytz = MagicMock()
    mock_pytz.timezone.return_value = mock_timezone

    with patch("src.handlers.portfolio_manager.datetime", mock_datetime), patch(
        "src.handlers.portfolio_manager.pytz", mock_pytz
    ), patch("os.path.exists", return_value=False), patch(
        "builtins.open", MagicMock()
    ), patch(
        "json.dump"
    ) as mock_json_dump:
        portfolio_manager.save_portfolio_history(
            total_value,
            total_investment,
            total_profit_loss,
            total_profit_loss_percentage,
        )

        # Check that json.dump was called with new history data
        mock_json_dump.assert_called_once()
        new_history = mock_json_dump.call_args[0][0]

        # Should contain only one entry
        assert len(new_history) == 1

        # Check the entry has correct values
        entry = new_history[0]
        assert entry["total_value"] == total_value
        assert entry["total_investment"] == total_investment
        assert entry["profit_loss"] == total_profit_loss
        assert entry["profit_loss_percentage"] == total_profit_loss_percentage


@pytest.mark.asyncio
async def test_send_portfolio_update_basic(
    portfolio_manager, sample_portfolio, sample_crypto_prices
):
    """Test sending a basic portfolio update via Telegram."""
    portfolio_manager.portfolio = sample_portfolio
    portfolio_manager.telegram_api_token = "test_token"
    mock_update = MagicMock()

    # Mock the calculate_portfolio_value method
    with patch.object(
        portfolio_manager,
        "calculate_portfolio_value",
        return_value="Basic portfolio message",
    ) as mock_calculate:
        await portfolio_manager.send_portfolio_update(
            sample_crypto_prices, mock_update, detailed=False
        )

        # Check that calculate_portfolio_value was called
        mock_calculate.assert_called_once_with(sample_crypto_prices)

        # Check that send_telegram_message was called with the right message
        portfolio_manager.telegram_message.send_telegram_message.assert_called_once()
        message = portfolio_manager.telegram_message.send_telegram_message.call_args[0][
            0
        ]
        assert "Basic portfolio message" in message
        assert "#Portfolio" in message


@pytest.mark.asyncio
async def test_send_portfolio_update_detailed(
    portfolio_manager, sample_portfolio, sample_crypto_prices
):
    """Test sending a detailed portfolio update via Telegram."""
    portfolio_manager.portfolio = sample_portfolio
    portfolio_manager.telegram_api_token = "test_token"
    mock_update = MagicMock()

    # Mock the calculate_portfolio_value_detailed method
    with patch.object(
        portfolio_manager,
        "calculate_portfolio_value_detailed",
        return_value="Detailed portfolio message",
    ) as mock_calculate:
        await portfolio_manager.send_portfolio_update(
            sample_crypto_prices, mock_update, detailed=True, save_data=True
        )

        # Check that calculate_portfolio_value_detailed was called with save_data=True
        mock_calculate.assert_called_once_with(sample_crypto_prices, save_data=True)

        # Check that send_telegram_message was called with the right message
        portfolio_manager.telegram_message.send_telegram_message.assert_called_once()
        message = portfolio_manager.telegram_message.send_telegram_message.call_args[0][
            0
        ]
        assert "Detailed portfolio message" in message
        assert "#DetailedPortfolio" in message


@pytest.mark.asyncio
async def test_save_portfolio_history_hourly(portfolio_manager, sample_crypto_prices):
    """Test the hourly portfolio history saving functionality."""
    # Mock the calculate_portfolio_value_detailed method
    with patch.object(
        portfolio_manager, "calculate_portfolio_value_detailed"
    ) as mock_calculate:
        await portfolio_manager.save_portfolio_history_hourly(sample_crypto_prices)

        # Check that calculate_portfolio_value_detailed was called with save_data=True
        mock_calculate.assert_called_once_with(sample_crypto_prices, save_data=True)
