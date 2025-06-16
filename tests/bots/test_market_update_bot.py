"""
Market Update Bot Tests
"""

# pylint: disable=redefined-outer-name, duplicate-code

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bots.market_update_bot import NEWS_KEYBOARD, MarketUpdateBot


@pytest.fixture
def market_bot():
    """Fixture that creates a MarketUpdateBot with mocked dependencies"""
    with patch(
        "src.bots.market_update_bot.CryptoValueBot"
    ) as mock_crypto_bot_class, patch(
        "src.bots.market_update_bot.TelegramMessagesHandler"
    ) as mock_telegram_class, patch(
        "src.bots.market_update_bot.PlotTrades"
    ) as mock_plot_trades_class, patch(
        "src.bots.market_update_bot.LoadVariables.load"
    ) as mock_load_vars:
        # Create mock instances
        mock_crypto_bot = MagicMock()
        mock_crypto_bot_class.return_value = mock_crypto_bot

        # Set up async methods for crypto_value_bot
        mock_crypto_bot.send_market_update = AsyncMock()
        mock_crypto_bot.send_eth_gas_fee = AsyncMock()
        mock_crypto_bot.send_portfolio_update = AsyncMock()
        mock_crypto_bot.show_fear_and_greed = AsyncMock()

        # Set up regular methods
        mock_crypto_bot.reload_the_data = MagicMock()
        mock_crypto_bot.get_my_crypto = MagicMock()

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram
        mock_telegram.reload_the_data = MagicMock()

        mock_plot_trades = MagicMock()
        mock_plot_trades_class.return_value = mock_plot_trades
        mock_plot_trades.send_all_plots = AsyncMock()
        mock_plot_trades.send_portfolio_history_plot = AsyncMock()
        mock_plot_trades.plot_crypto_trades = AsyncMock()

        # Configure mock variables
        mock_load_vars.return_value = {"TELEGRAM_API_TOKEN_VALUE": "test_token_value"}

        # Create the bot
        bot = MarketUpdateBot()

        # Provide the mocked objects to the test
        yield bot, {
            "crypto_bot": mock_crypto_bot,
            "telegram": mock_telegram,
            "plot_trades": mock_plot_trades,
        }


@pytest.mark.asyncio
async def test_start_command(market_bot):
    """Test the start command sends welcome message with keyboard"""
    bot, _ = market_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()
    mock_context = MagicMock()

    # Call the method
    await bot.start(mock_update, mock_context)

    # Verify welcome message was sent with correct keyboard
    mock_update.message.reply_text.assert_called_once_with(
        "🤖 Welcome to the Market Update! Use the buttons below to get started:",
        reply_markup=NEWS_KEYBOARD,
    )


@pytest.mark.asyncio
async def test_send_market_update(market_bot):
    """Test send_market_update method fetches and sends market data"""
    bot, mocks = market_bot

    # Create mock update
    mock_update = MagicMock()

    # Call the method
    await bot.send_market_update(mock_update)

    # Verify interactions
    mocks["crypto_bot"].reload_the_data.assert_called_once()
    mocks["crypto_bot"].get_my_crypto.assert_called_once()
    mocks["crypto_bot"].send_market_update.assert_called_once()
    # Verify datetime.now is passed to send_market_update
    args, _ = mocks["crypto_bot"].send_market_update.call_args
    assert isinstance(args[0], datetime)
    assert args[1] == mock_update


@pytest.mark.asyncio
async def test_send_eth_gas(market_bot):
    """Test send_eth_gas method fetches and sends ETH gas fees"""
    bot, mocks = market_bot

    # Create mock update
    mock_update = MagicMock()

    # Call the method
    await bot.send_eth_gas(mock_update)

    # Verify interactions
    mocks["crypto_bot"].reload_the_data.assert_called_once()
    mocks["crypto_bot"].send_eth_gas_fee.assert_called_once_with(mock_update)


@pytest.mark.asyncio
async def test_send_portfolio_value(market_bot):
    """Test send_portfolio_value method fetches and sends portfolio data"""
    bot, mocks = market_bot

    # Create mock update
    mock_update = MagicMock()

    # Call the method
    await bot.send_portfolio_value(mock_update)

    # Verify interactions
    mocks["crypto_bot"].reload_the_data.assert_called_once()
    mocks["crypto_bot"].get_my_crypto.assert_called_once()
    mocks["crypto_bot"].send_portfolio_update.assert_called_once_with(mock_update, True)


@pytest.mark.asyncio
async def test_send_crypto_fear_and_greed(market_bot):
    """Test send_crypto_fear_and_greed method fetches and sends fear and greed index"""
    bot, mocks = market_bot

    # Create mock update
    mock_update = MagicMock()

    # Call the method
    await bot.send_crypto_fear_and_greed(mock_update)

    # Verify interactions
    mocks["crypto_bot"].reload_the_data.assert_called_once()
    mocks["crypto_bot"].show_fear_and_greed.assert_called_once_with(mock_update)


@pytest.mark.asyncio
async def test_send_crypto_plots(market_bot):
    """Test send_crypto_plots method sends all plots"""
    bot, mocks = market_bot

    # Create mock update
    mock_update = MagicMock()

    # Call the method
    await bot.send_crypto_plots(mock_update)

    # Verify interactions
    mocks["plot_trades"].send_all_plots.assert_called_once_with(mock_update)


@pytest.mark.asyncio
async def test_send_portfolio_history(market_bot):
    """Test send_portfolio_history method creates and sends history plot"""
    bot, mocks = market_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()
    mock_context = MagicMock()

    # Call the method
    await bot.send_portfolio_history(mock_update, mock_context)

    # Verify interactions
    mock_update.message.reply_text.assert_called_once_with("Creating the plot...")
    mocks["plot_trades"].send_portfolio_history_plot.assert_called_once_with(
        mock_update
    )


@pytest.mark.asyncio
async def test_send_crypto_plot_valid(market_bot):
    """Test send_crypto_plot method with valid symbol"""
    bot, mocks = market_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()
    mock_context = MagicMock()
    mock_context.args = ["btc"]

    # Call the method
    await bot.send_crypto_plot(mock_update, mock_context)

    # Verify interactions
    mock_update.message.reply_text.assert_called_once_with("Creating the plot...")
    mocks["plot_trades"].plot_crypto_trades.assert_called_once_with("btc", mock_update)


@pytest.mark.asyncio
async def test_send_crypto_plot_invalid(market_bot):
    """Test send_crypto_plot method with missing symbol"""
    bot, mocks = market_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()
    mock_context = MagicMock()
    mock_context.args = []

    # Call the method
    await bot.send_crypto_plot(mock_update, mock_context)

    # Verify interactions
    mock_update.message.reply_text.assert_called_with("❌ Usage: /plot <symbol>")
    mocks["plot_trades"].plot_crypto_trades.assert_not_called()


@pytest.mark.asyncio
async def test_help_command(market_bot):
    """Test help_command sends help message"""
    bot, _ = market_bot

    # Create mock update and context
    mock_update = MagicMock()
    mock_update.message.reply_text = AsyncMock()
    mock_context = MagicMock()

    # Call the method
    await bot.help_command(mock_update, mock_context)

    # Verify help message was sent
    mock_update.message.reply_text.assert_called_once()
    args, kwargs = mock_update.message.reply_text.call_args
    assert "Crypto Bot Commands" in args[0]
    assert kwargs["parse_mode"] == "Markdown"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "button_text,expected_method",
    [
        ("🕒 Market Update", "send_market_update"),
        ("update", "send_market_update"),
        ("market", "send_market_update"),
        ("⛽ ETH Gas Fees", "send_eth_gas"),
        ("gas", "send_eth_gas"),
        ("fee", "send_eth_gas"),
        ("📊 Crypto Fear & Greed Index", "send_crypto_fear_and_greed"),
        ("index", "send_crypto_fear_and_greed"),
        ("📈 Show plots for the entire portfolio", "send_crypto_plots"),
        ("📈 Plot portfolio history", "send_portfolio_history"),
        ("history", "send_portfolio_history"),
        ("🚨 Help", "help_command"),
        ("help", "help_command"),
    ],
)
async def test_handle_buttons(market_bot, button_text, expected_method):
    """Test handle_buttons method routes to correct method based on button text"""
    bot, _ = market_bot

    # Create mock methods to track calls
    with patch.object(
        bot, "send_market_update", AsyncMock()
    ) as mock_market_update, patch.object(
        bot, "send_eth_gas", AsyncMock()
    ) as mock_eth_gas, patch.object(
        bot, "send_portfolio_value", AsyncMock()
    ) as mock_portfolio_value, patch.object(
        bot, "send_crypto_fear_and_greed", AsyncMock()
    ) as mock_fear_greed, patch.object(
        bot, "send_crypto_plots", AsyncMock()
    ) as mock_crypto_plots, patch.object(
        bot, "send_portfolio_history", AsyncMock()
    ) as mock_portfolio_history, patch.object(
        bot, "help_command", AsyncMock()
    ) as mock_help_command, patch(
        "src.bots.market_update_bot.check_if_special_user", return_value=True
    ):
        # Create mock update
        mock_update = MagicMock()
        mock_update.message.text = button_text
        mock_update.message.reply_text = AsyncMock()
        mock_context = MagicMock()

        # Call the method
        await bot.handle_buttons(mock_update, mock_context)

        # Verify the correct method was called
        method_map = {
            "send_market_update": mock_market_update,
            "send_eth_gas": mock_eth_gas,
            "send_portfolio_value": mock_portfolio_value,
            "send_crypto_fear_and_greed": mock_fear_greed,
            "send_crypto_plots": mock_crypto_plots,
            "send_portfolio_history": mock_portfolio_history,
            "help_command": mock_help_command,
        }

        expected_mock = method_map[expected_method]
        assert expected_mock.called
        if expected_method == "send_portfolio_history":
            expected_mock.assert_called_once_with(mock_update, None)


@pytest.mark.asyncio
async def test_portfolio_update_unauthorized(market_bot):
    """Test portfolio update when user is not authorized"""
    bot, _ = market_bot

    # Create mock update
    mock_update = MagicMock()
    mock_update.message.text = "📊 Detailed Portfolio Update"
    mock_update.message.reply_text = AsyncMock()
    mock_update.effective_chat.id = 12345
    mock_context = MagicMock()

    # Mock check_if_special_user to return False (unauthorized)
    with patch(
        "src.bots.market_update_bot.check_if_special_user", return_value=False
    ), patch.object(bot, "send_portfolio_value", AsyncMock()) as mock_portfolio_value:
        # Call the method
        await bot.handle_buttons(mock_update, mock_context)

        # Verify portfolio value method was not called
        mock_portfolio_value.assert_not_called()
        # Verify unauthorized message was sent
        mock_update.message.reply_text.assert_called_with(
            "You don't have the rights for this action!"
        )


@pytest.mark.asyncio
async def test_invalid_button(market_bot):
    """Test handling of invalid button press"""
    bot, _ = market_bot

    # Create mock update
    mock_update = MagicMock()
    mock_update.message.text = "Invalid Button"
    mock_update.message.reply_text = AsyncMock()
    mock_context = MagicMock()

    # Call the method
    await bot.handle_buttons(mock_update, mock_context)

    # Verify error message was sent
    mock_update.message.reply_text.assert_called_with(
        "❌ Invalid command. Please use the buttons below."
    )


def test_reload_the_data(market_bot):
    """Test reload_the_data method correctly initializes the bot"""
    bot, mocks = market_bot

    # Call the method
    bot.reload_the_data()

    # Verify dependencies were reloaded
    mocks["crypto_bot"].reload_the_data.assert_called_once()
    mocks["telegram"].reload_the_data.assert_called_once()

    # Verify token was loaded
    assert bot.telegram_api_token == "test_token_value"


def test_run_bot(market_bot):
    """Test run_bot method sets up application with correct handlers"""
    bot, _ = market_bot

    # Ensure the token is set correctly
    bot.telegram_api_token = "test_token_value"

    # Create mock application
    mock_app = MagicMock()
    mock_app_builder = MagicMock()
    mock_app_builder.token.return_value = mock_app_builder
    mock_app_builder.build.return_value = mock_app

    # Mock Application.builder() to return our mock
    with patch(
        "src.bots.market_update_bot.Application.builder", return_value=mock_app_builder
    ), patch.object(bot, "reload_the_data") as mock_reload, patch.object(
        mock_app, "run_polling"
    ) as mock_run_polling:
        # Call the method
        bot.run_bot()

        # Verify application was initialized with token
        mock_app_builder.token.assert_called_once_with("test_token_value")

        # Verify handlers were added
        assert mock_app.add_handler.call_count >= 5

        # Verify data was reloaded
        mock_reload.assert_called_once()

        # Verify polling was started
        mock_run_polling.assert_called_once()
