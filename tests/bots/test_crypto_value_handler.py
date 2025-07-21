"""
Crypto Value Handler Test Suite
"""

# pylint: disable=redefined-outer-name, line-too-long

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bots.crypto_value_handler import CryptoValueBot


@pytest.fixture
def crypto_bot():
    """Fixture that creates a CryptoValueBot with mocked dependencies"""
    with patch("src.bots.crypto_value_handler.DataBaseHandler") as mock_db_class, patch(
        "src.bots.crypto_value_handler.AlertsHandler"
    ) as mock_alerts_class, patch(
        "src.bots.crypto_value_handler.PortfolioManager"
    ) as mock_portfolio_class, patch(
        "src.bots.crypto_value_handler.TelegramMessagesHandler"
    ) as mock_telegram_class, patch(
        "src.bots.crypto_value_handler.CryptoNewsCheck"
    ) as mock_news_class, patch(
        "src.bots.crypto_value_handler.src.handlers.load_variables_handler.load_json"
    ) as mock_load_vars:
        # Create mock instances
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.store_fear_greed = AsyncMock()
        mock_db.store_eth_gas_fee = AsyncMock()
        mock_db.store_daily_stats = AsyncMock()

        mock_alerts = MagicMock()
        mock_alerts_class.return_value = mock_alerts
        mock_alerts.check_for_alerts = AsyncMock()
        mock_alerts.check_for_major_updates_1h = AsyncMock(return_value=True)
        mock_alerts.check_for_major_updates_24h = AsyncMock(return_value=True)
        mock_alerts.check_for_major_updates_7d = AsyncMock(return_value=True)
        mock_alerts.check_for_major_updates_30d = AsyncMock(return_value=True)

        mock_portfolio = MagicMock()
        mock_portfolio_class.return_value = mock_portfolio
        mock_portfolio.send_portfolio_update = AsyncMock()
        mock_portfolio.save_portfolio_history_hourly = AsyncMock()
        mock_portfolio.reload_the_data = MagicMock()

        mock_alerts.rsi_check = AsyncMock()

        mock_telegram = MagicMock()
        mock_telegram_class.return_value = mock_telegram
        mock_telegram.send_telegram_message = AsyncMock()
        mock_telegram.send_market_update = AsyncMock()
        mock_telegram.send_eth_gas_fee = AsyncMock()
        mock_telegram.reload_the_data = MagicMock()

        mock_news = MagicMock()
        mock_news_class.return_value = mock_news
        mock_news.send_today_summary = AsyncMock()
        mock_news.reload_the_data = MagicMock()

        # Configure mock variables
        mock_load_vars.return_value = {
            "TELEGRAM_API_TOKEN_VALUE": "test_token_value",
            "TELEGRAM_API_TOKEN_ARTICLES": "test_token_articles",
            "TODAY_AI_SUMMARY": [12],
            "ETHERSCAN_GAS_API_URL": "https://api.etherscan.io/api",
            "ETHERSCAN_API_KEY": "test_etherscan_key",
            "SEND_HOURS_VALUES": [8, 16],
            "PORTFOLIO_SAVE_HOURS": [9, 17],
            "SENTIMENT_HOURS": [10, 18],
            "SAVE_HOURS": [23],
            "CRYPTOCURRENCIES": ["BTC", "ETH", "XRP"],
            "CMC_API_KEY": "test_cmc_key",
            "CMC_URL_LISTINGS": "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
        }

        bot = CryptoValueBot()

        # Provide the mocked objects to the test
        yield bot, {
            "db": mock_db,
            "alerts": mock_alerts,
            "portfolio": mock_portfolio,
            "telegram": mock_telegram,
            "news": mock_news,
        }


@pytest.mark.asyncio
async def test_reload_the_data(crypto_bot):
    """Test reload_the_data method properly initializes the bot"""
    bot, mocks = crypto_bot

    # Reload the data
    bot.reload_the_data()

    # Verify dependencies were reloaded
    mocks["alerts"].reload_the_data.assert_called_once()
    mocks["portfolio"].reload_the_data.assert_called_once()
    mocks["telegram"].reload_the_data.assert_called_once()

    # Verify variables were loaded correctly
    assert bot.market_update_api_token == "test_token_value"
    assert bot.articles_alert_api_token == "test_token_articles"
    assert bot.today_ai_summary == [12]
    assert bot.etherscan_api_url == "https://api.etherscan.io/apitest_etherscan_key"
    assert bot.send_hours == [8, 16]
    assert bot.crypto_currencies == ["BTC", "ETH", "XRP"]
    assert bot.my_crypto == {}


@pytest.mark.asyncio
async def test_get_my_crypto(crypto_bot):
    """Test get_my_crypto method fetches crypto data"""
    bot, _ = crypto_bot

    # Initialize my_crypto as an empty dictionary
    bot.my_crypto = {}
    bot.top_100_crypto = {}

    # Set cryptocurrencies list
    bot.crypto_currencies = ["BTC", "ETH", "XRP"]

    # Set API credentials
    bot.coinmarketcap_api_key = "test_api_key"
    bot.coinmarketcap_api_url = "https://test-api-url.com"

    # Reset the last API call time to ensure we make a new call
    bot.last_api_call = 0
    bot.cache_duration = 0

    # Mock requests.get for CoinMarketCap API
    sample_response = {
        "data": [
            {
                "symbol": "BTC",
                "quote": {
                    "USD": {
                        "price": 50000,
                        "percent_change_1h": 1.5,
                        "percent_change_24h": 2.5,
                        "percent_change_7d": 10.0,
                        "percent_change_30d": 20.0,
                    }
                },
            },
            {
                "symbol": "ETH",
                "quote": {
                    "USD": {
                        "price": 3000,
                        "percent_change_1h": 1.2,
                        "percent_change_24h": 2.2,
                        "percent_change_7d": 8.0,
                        "percent_change_30d": 15.0,
                    }
                },
            },
            {
                "symbol": "XRP",
                "quote": {
                    "USD": {
                        "price": 0.5,
                        "percent_change_1h": 0.5,
                        "percent_change_24h": 1.5,
                        "percent_change_7d": 5.0,
                        "percent_change_30d": 10.0,
                    }
                },
            },
            {
                "symbol": "DOGE",
                "quote": {
                    "USD": {
                        "price": 0.1,
                        "percent_change_1h": 0.1,
                        "percent_change_24h": 0.2,
                        "percent_change_7d": 0.5,
                        "percent_change_30d": 1.0,
                    }
                },
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=sample_response)
    mock_response.text = json.dumps(sample_response)

    with patch(
        "src.bots.crypto_value_handler.requests.get", return_value=mock_response
    ) as mock_get:
        # Call the method
        bot.get_my_crypto()

        # Verify API call was made
        mock_get.assert_called_once()

        # Verify data was processed correctly
        assert len(bot.my_crypto) == 3
        assert "BTC" in bot.my_crypto
        assert "ETH" in bot.my_crypto
        assert "XRP" in bot.my_crypto
        assert bot.my_crypto["BTC"]["price"] == 50000

        # Verify top_100_crypto contains all coins from the response
        assert len(bot.top_100_crypto) == 4
        assert "DOGE" in bot.top_100_crypto


@pytest.mark.asyncio
async def test_show_fear_and_greed(crypto_bot):
    """Test show_fear_and_greed method sends a message with the fear and greed index"""
    bot, mocks = crypto_bot

    # Mock the get_fear_and_greed_message function
    with patch(
        "src.bots.crypto_value_handler.get_fear_and_greed_message",
        AsyncMock(return_value="Fear and Greed Index: 60 (Greed)"),
    ):
        # Call the method
        mock_update = MagicMock()
        await bot.show_fear_and_greed(mock_update)

        # Verify telegram message was sent
        mocks["telegram"].send_telegram_message.assert_called_once_with(
            "Fear and Greed Index: 60 (Greed)",
            bot.market_update_api_token,
            False,
            mock_update,
        )


@pytest.mark.asyncio
async def test_send_market_update(crypto_bot):
    """Test send_market_update method sends a market update message"""
    bot, mocks = crypto_bot

    # Call the method
    mock_update = MagicMock()
    now_date = datetime.now()
    await bot.send_market_update(now_date, mock_update)

    # Verify telegram message was sent
    mocks["telegram"].send_market_update.assert_called_once_with(
        bot.market_update_api_token, now_date, bot.my_crypto, mock_update
    )


@pytest.mark.asyncio
async def test_save_today_data(crypto_bot):
    """Test save_today_data method saves all required data"""
    bot, mocks = crypto_bot

    # Mock the required functions
    with patch(
        "src.bots.crypto_value_handler.get_fear_and_greed",
        AsyncMock(return_value=(60, "Greed", "2023-05-01")),
    ), patch(
        "src.bots.crypto_value_handler.get_eth_gas_fee", return_value=(50, 60, 70)
    ), patch(
        "src.bots.crypto_value_handler.get_market_sentiment", AsyncMock()
    ), patch(
        "src.bots.crypto_value_handler.os.path.exists", return_value=True
    ):
        # Call the method
        await bot.save_today_data()

        # Verify database calls were made
        mocks["db"].store_fear_greed.assert_called_once_with(60, "Greed", "2023-05-01")
        mocks["db"].store_eth_gas_fee.assert_called_once_with(50, 60, 70)
        mocks["db"].store_daily_stats.assert_called_once()


@pytest.mark.asyncio
async def test_check_for_major_updates_1h(crypto_bot):
    """Test check_for_major_updates_1h method checks for hourly alerts"""
    bot, mocks = crypto_bot

    # Prepare test data
    bot.top_100_crypto = {
        "BTC": {"price": 50000, "change_1h": 5.0},
        "ETH": {"price": 3000, "change_1h": -8.0},
    }

    # Set up mock to return True (found alerts)
    mocks["alerts"].check_for_major_updates_1h.return_value = True

    # Call the method
    mock_update = MagicMock()
    result = await bot.check_for_major_updates_1h(mock_update)

    # Verify alert handler was called
    mocks["alerts"].check_for_major_updates_1h.assert_called_once_with(
        bot.top_100_crypto, mock_update
    )

    # Verify result
    assert result is True


@pytest.mark.asyncio
async def test_send_all_the_messages_normal_hour(crypto_bot):
    """Test send_all_the_messages method during a regular hour"""
    bot, mocks = crypto_bot

    # Set up test data
    bot.send_hours = [8, 16]
    bot.save_portfolio_hours = [9, 17]
    bot.sentiment_hours = [10, 18]
    bot.today_ai_summary = [12]
    bot.save_hours = [23]

    # Create a datetime for a regular hour (not in any special hours)
    now_date = datetime(2023, 5, 1, 14, 0, 0)  # 2pm

    # Call the method
    await bot.send_all_the_messages(now_date)

    # Verify portfolio was saved
    mocks["portfolio"].save_portfolio_history_hourly.assert_called_once()

    # Verify no market update sent (not in send_hours)
    mocks["telegram"].send_market_update.assert_not_called()

    # Verify no portfolio update sent (not in save_portfolio_hours)
    mocks["portfolio"].send_portfolio_update.assert_not_called()

    # Verify alerts were checked
    mocks["alerts"].check_for_alerts.assert_called_once()


@pytest.mark.asyncio
async def test_send_all_the_messages_send_hour(crypto_bot):
    """Test send_all_the_messages method during a send hour"""
    bot, mocks = crypto_bot

    # Set up test data
    bot.send_hours = [8, 16]
    bot.save_portfolio_hours = [9, 17]
    bot.sentiment_hours = [10, 18]
    bot.today_ai_summary = [12]
    bot.save_hours = [23]

    # Create a datetime for a send hour (8am)
    now_date = datetime(2023, 5, 1, 8, 0, 0)

    # Call the method
    await bot.send_all_the_messages(now_date)

    # Verify portfolio was saved
    mocks["portfolio"].save_portfolio_history_hourly.assert_called_once()

    # Verify market update was sent
    mocks["telegram"].send_market_update.assert_called_once()

    # Verify gas fee was sent
    mocks["telegram"].send_eth_gas_fee.assert_called_once()

    # Verify fear and greed index was sent (first send hour)
    assert mocks["telegram"].send_telegram_message.call_count >= 1

    # Verify portfolio update was sent - accepting any arguments
    assert mocks["portfolio"].send_portfolio_update.called


@pytest.mark.asyncio
async def test_fetch_data(crypto_bot):
    """Test fetch_data method fetches and processes data"""
    bot, _ = crypto_bot

    # Mock the methods that fetch_data calls
    with patch.object(bot, "get_my_crypto") as mock_get_crypto, patch.object(
        bot, "send_all_the_messages", AsyncMock()
    ) as mock_send_messages:
        # Call the method
        await bot.fetch_data()

        # Verify data was fetched
        mock_get_crypto.assert_called_once()

        # Verify messages were sent
        mock_send_messages.assert_called_once()
