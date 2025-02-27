import requests
import json
import time

from datetime import datetime

from sdk import LoadVariables as LoadVariables

from sdk.Alerts import AlertsHandler
from sdk.DataFetcher import get_fear_and_greed
from sdk.PortfolioManager import PortfolioManager
from sdk.SendTelegramMessage import TelegramMessagesHandler

class CryptoValueBot:
    def __init__(self):
        self.lastSentHour = None
        self.my_crypto = None
        self.top_100_crypto = None

        self.cryptoCurrencies = None

        self.coinmarketcap_api_key = None
        self.coinmarketcap_api_url = None

        self.send_hours = None

        self.telegram_api_token = None

        self.last_api_call = 0
        self.cache_duration = 60

        self.alert_handler = AlertsHandler()
        self.portfolio = PortfolioManager()
        self.telegram_message = TelegramMessagesHandler()

    def reload_the_data(self):
        variables = LoadVariables.load()

        self.telegram_api_token = variables.get("TELEGRAM_API_TOKEN_VALUE", "")

        self.send_hours = variables.get("SEND_HOURS", "")

        self.my_crypto = {}
        self.top_100_crypto = {}

        # Reload alerts thresholds
        self.alert_handler.reload_the_data()

        # Reload portfolio from file
        self.portfolio.reload_the_data()

        # Reload telegram message handler variables
        self.telegram_message.reload_the_data()

        self.cryptoCurrencies = variables.get("CRYPTOCURRENCIES", "")

        # CoinMarketCap API credentials
        self.coinmarketcap_api_key = variables.get("CMC_API_KEY", "")
        self.coinmarketcap_api_url = variables.get("CMC_URL_LISTINGS", "")

    # Function to fetch cryptocurrency prices and price changes
    def get_my_crypto(self):
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
        response = requests.get(self.coinmarketcap_api_url, headers=headers, params=parameters)
        data = json.loads(response.text)

        for crypto in data["data"]:
            symbol = crypto["symbol"]
            if symbol in self.cryptoCurrencies:
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

    async def show_fear_and_greed(self, update = None):
        message = await get_fear_and_greed()

        await self.telegram_message.send_telegram_message(message, self.telegram_api_token, False, update)

    async def send_market_update(self, now_date, update = None):
        await self.telegram_message.send_market_update(self.telegram_api_token, now_date, self.my_crypto, update)

    async def send_portfolio_update(self, update = None):
        await self.portfolio.send_portfolio_update(self.my_crypto, update)

    async def send_eth_gas_fee(self, update = None):
        await self.telegram_message.send_eth_gas_fee(self.telegram_api_token, update)

    # Scheduled market updates
    async def send_all_the_messages(self, now_date):
        if self.lastSentHour != now_date.hour:
            self.lastSentHour = now_date.hour

            if now_date.hour in self.send_hours:
                await self.send_market_update(now_date)

                await self.send_eth_gas_fee()

                if now_date.hour == sorted(self.send_hours)[0]:
                    await self.show_fear_and_greed()

                await self.send_portfolio_update()

            await self.check_for_major_updates(now_date)

    async def check_for_major_updates(self, now_date, update = None):
        await self.alert_handler.check_for_alerts(now_date, self.top_100_crypto, update)

    async def fetch_data(self):
        self.get_my_crypto()

        now_date = datetime.now()

        await self.send_all_the_messages(now_date)
