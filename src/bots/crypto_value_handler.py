"""
Crypto Price Alerts Bot
This bot fetches cryptocurrency prices, market sentiment, and other data,
and sends updates via Telegram. It also checks for major price changes and
alerts users based on predefined thresholds.
"""

import json
import logging
import os
import time
from datetime import datetime

import requests

import src.handlers.load_variables_handler
from src.data_base.data_base_handler import DataBaseHandler
from src.handlers.alerts_handler import AlertsHandler
from src.handlers.crypto_rsi_handler import CryptoRSIHandler
from src.handlers.data_fetcher_handler import (
    get_eth_gas_fee,
    get_fear_and_greed,
    get_fear_and_greed_message,
)
from src.handlers.market_sentiment_handler import get_market_sentiment
from src.handlers.news_check_handler import CryptoNewsCheck
from src.handlers.portfolio_manager import PortfolioManager
from src.handlers.send_telegram_message import TelegramMessagesHandler

logger = logging.getLogger(__name__)
logger.info("Load variables started")


# pylint: disable=too-many-instance-attributes
class CryptoValueBot:
    """
    CryptoValueBot is a class that manages cryptocurrency data,
    """

    def __init__(self):
        """
        Initializes the CryptoValueBot with default values and loads necessary configurations.
        """
        self.last_sent_hour = None
        self.my_crypto = None
        self.top_100_crypto = None

        self.crypto_currencies = None

        self.coinmarketcap_api_key = None
        self.coinmarketcap_api_url = None

        self.etherscan_api_url = None

        self.send_hours = None

        self.save_portfolio_hours = None

        self.sentiment_hours = None

        self.save_hours = None

        self.market_update_api_token = None
        self.articles_alert_api_token = None

        self.today_ai_summary = None

        self.send_rsi_alerts = None

        self.last_api_call = 0
        self.cache_duration = 60

        self.db = DataBaseHandler()
        self.alert_handler = AlertsHandler()
        self.portfolio = PortfolioManager()
        self.telegram_message = TelegramMessagesHandler()
        self.rsi_handler = CryptoRSIHandler()

        self.news_check = CryptoNewsCheck()

    def reload_the_data(self):
        """
        Reloads the configuration data and initializes the bot's variables.
        This includes API tokens, cryptocurrency lists, and other settings.
        """
        variables = src.handlers.load_variables_handler.load_json()

        self.market_update_api_token = variables.get("TELEGRAM_API_TOKEN_VALUE", "")
        self.articles_alert_api_token = variables.get("TELEGRAM_API_TOKEN_ARTICLES", "")

        self.today_ai_summary = variables.get("TODAY_AI_SUMMARY", "")

        self.etherscan_api_url = variables.get(
            "ETHERSCAN_GAS_API_URL", ""
        ) + variables.get("ETHERSCAN_API_KEY", "")

        self.send_hours = variables.get("SEND_HOURS_VALUES", "")
        self.save_portfolio_hours = variables.get("PORTFOLIO_SAVE_HOURS", "")
        self.sentiment_hours = variables.get("SENTIMENT_HOURS", "")
        self.save_hours = variables.get("SAVE_HOURS", "")
        self.send_rsi_alerts = variables.get("SEND_RSI_ALERTS", False)

        self.my_crypto = {}
        self.top_100_crypto = {}

        # Reload alerts thresholds
        self.alert_handler.reload_the_data()

        # Reload portfolio from file
        self.portfolio.reload_the_data()

        # Reload telegram message handler variables
        self.telegram_message.reload_the_data()

        self.rsi_handler.reload_the_data()

        self.crypto_currencies = variables.get("CRYPTOCURRENCIES", "")

        # CoinMarketCap API credentials
        self.coinmarketcap_api_key = variables.get("CMC_API_KEY", "")
        self.coinmarketcap_api_url = variables.get("CMC_URL_LISTINGS", "")

    # Function to fetch cryptocurrency prices and price changes
    def get_my_crypto(self):
        """
        Fetches the latest cryptocurrency prices and changes from CoinMarketCap API.
        """
        current_time = time.time()
        if current_time - self.last_api_call < self.cache_duration:
            return

        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.coinmarketcap_api_key,
        }
        parameters = {
            "start": "1",
            "limit": "100",
            "convert": "USD",
        }
        response = requests.get(
            self.coinmarketcap_api_url, headers=headers, params=parameters, timeout=30
        )
        data = json.loads(response.text)

        if not data:
            logger.error(
                "Error fetching data from CoinMarketCap API: %s", data.get("status", {})
            )
            return

        for crypto in data["data"]:
            symbol = crypto["symbol"]
            if symbol in self.crypto_currencies:
                self.my_crypto[symbol] = {
                    "price": crypto["quote"]["USD"]["price"],
                    "change_1h": crypto["quote"]["USD"]["percent_change_1h"],
                    "change_24h": crypto["quote"]["USD"]["percent_change_24h"],
                    "change_7d": crypto["quote"]["USD"]["percent_change_7d"],
                    "change_30d": crypto["quote"]["USD"]["percent_change_30d"],
                }
            self.top_100_crypto[symbol] = {
                "price": crypto["quote"]["USD"]["price"],
                "change_1h": crypto["quote"]["USD"]["percent_change_1h"],
                "change_24h": crypto["quote"]["USD"]["percent_change_24h"],
                "change_7d": crypto["quote"]["USD"]["percent_change_7d"],
                "change_30d": crypto["quote"]["USD"]["percent_change_30d"],
            }

    async def show_fear_and_greed(self, update=None):
        """
        Fetches the current Fear and Greed Index and sends it as a Telegram message.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        message = await get_fear_and_greed_message()

        await self.telegram_message.send_telegram_message(
            message, self.market_update_api_token, False, update
        )

    async def send_market_update(self, now_date, update=None):
        """
        Sends a market update message containing the current cryptocurrency prices and changes.
        Args:
            now_date: The current date and time.
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        await self.telegram_message.send_market_update(
            self.market_update_api_token, now_date, self.my_crypto, update
        )

    async def send_portfolio_update(self, update=None, detailed=False, save_data=False):
        """
        Sends a portfolio update message containing the user's cryptocurrency holdings
        and their current values.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
            detailed: Optional; if True, sends a detailed portfolio update.
            save_data: Optional; if True, saves the portfolio data to the database.
        """
        await self.portfolio.send_portfolio_update(
            self.my_crypto, update, detailed, save_data
        )

    async def save_portfolio(self):
        """
        Saves the current portfolio data to the database.
        """
        await self.portfolio.save_portfolio_history_hourly(self.my_crypto)

    async def send_eth_gas_fee(self, update=None):
        """
        Fetches the current Ethereum gas fees and sends them as a Telegram message.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        await self.telegram_message.send_eth_gas_fee(
            self.market_update_api_token, update
        )

    async def send_market_sentiment(self, update=None):
        """
        Fetches the current market sentiment and sends it as a Telegram message.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        message = await get_market_sentiment()

        await self.telegram_message.send_telegram_message(
            message, self.articles_alert_api_token, False, update
        )

    async def send_today_ai_summary(self):
        """
        Sends today's AI-generated summary of cryptocurrency news.
        """
        self.news_check.reload_the_data()

        await self.news_check.send_today_summary()

    async def save_today_data(self):
        """
        Saves today's data, including Fear and Greed Index, Ethereum gas fees,
        """
        base_path = os.path.join(os.path.dirname(__file__), "../../data_bases")
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        print("Saving the fear and greed values...")
        index_value, index_text, last_updated = await get_fear_and_greed()
        await self.db.store_fear_greed(index_value, index_text, last_updated)

        print("Saving the ETH gas fee...")
        safe_gas, propose_gas, fast_gas = get_eth_gas_fee(self.etherscan_api_url)
        await self.db.store_eth_gas_fee(safe_gas, propose_gas, fast_gas)

        print("Saving the market sentiment...")
        await get_market_sentiment(save_data=True)

        print("Saving the daily stats...")
        await self.db.store_daily_stats()

    async def send_all_the_messages(self, now_date):
        """
        Sends all scheduled messages based on the current hour.
        Args:
            now_date: The current date and time.
        """
        if self.last_sent_hour != now_date.hour:
            self.last_sent_hour = now_date.hour

            await self.save_portfolio()

            if now_date.hour in self.send_hours:
                await self.send_market_update(now_date)

                await self.send_eth_gas_fee()

                if now_date.hour == sorted(self.send_hours)[0]:
                    await self.show_fear_and_greed()

                await self.send_portfolio_update()

            await self.check_for_major_updates(now_date)

            if now_date.hour in self.save_portfolio_hours:
                await self.send_portfolio_update(detailed=True, save_data=True)

            if now_date.hour in self.sentiment_hours:
                await self.send_market_sentiment()

            if now_date.hour in self.today_ai_summary:
                await self.send_today_ai_summary()

            if now_date.hour in self.save_hours:
                print("\nSaving the data...")
                await self.save_today_data()

            if self.send_rsi_alerts:
                await self.rsi_handler.send_rsi_for_all_timeframes(
                    bot=self.market_update_api_token
                )

    async def check_for_major_updates(self, now_date, update=None):
        """
        Checks for major price changes in the top 100 cryptocurrencies and
        sends alerts if any are found.
        Args:
            now_date: The current date and time.
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        return await self.alert_handler.check_for_alerts(
            now_date, self.top_100_crypto, update
        )

    async def check_for_major_updates_1h(self, update=None):
        """
        Checks for major price changes in the top 100 cryptocurrencies over the last hour
        and sends alerts if any are found.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        return await self.alert_handler.check_for_major_updates_1h(
            self.top_100_crypto, update
        )

    async def check_for_major_updates_24h(self, update=None):
        """
        Checks for major price changes in the top 100 cryptocurrencies over the last 24 hours
        and sends alerts if any are found.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        return await self.alert_handler.check_for_major_updates_24h(
            self.top_100_crypto, update
        )

    async def check_for_major_updates_7d(self, update=None):
        """
        Checks for major price changes in the top 100 cryptocurrencies over the last 7 days
        and sends alerts if any are found.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        return await self.alert_handler.check_for_major_updates_7d(
            self.top_100_crypto, update
        )

    async def check_for_major_updates_30d(self, update=None):
        """
        Checks for major price changes in the top 100 cryptocurrencies over the last 30 days
        and sends alerts if any are found.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        return await self.alert_handler.check_for_major_updates_30d(
            self.top_100_crypto, update
        )

    async def fetch_data(self):
        """
        Fetches the latest cryptocurrency data, including prices, market sentiment,
        and Ethereum gas fees, and sends updates via Telegram.
        """
        self.get_my_crypto()

        now_date = datetime.now()

        await self.send_all_the_messages(now_date)
