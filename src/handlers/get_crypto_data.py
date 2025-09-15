import json
import logging
import time

import requests

from src.handlers.load_variables_handler import load_json

logger = logging.getLogger(__name__)
logger.info("GetCryptoDataHandler started")


class GetCryptoDataHandler:

    def __init__(self):
        """
        Initializes the GetCryptoDataHandler with necessary variables and API keys.
        """
        self.coinmarketcap_api_key = None
        self.coinmarketcap_api_url = None

        self.last_api_call = 0
        self.cache_duration = 60

        self.reload_the_data()

    def reload_the_data(self):
        """
        Reloads the configuration data for the CoinMarketCap API from the variables file.
        """
        variables = load_json()

        self.coinmarketcap_api_key = variables.get("CMC_API_KEY", "")
        self.coinmarketcap_api_url = variables.get(
            "CMC_URL_LISTINGS",
            "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
        )

    def get_crypto_data(self, wanted_coins=None):
        """
        Fetches the latest cryptocurrency prices and changes from CoinMarketCap API.
        """
        if wanted_coins is None:
            wanted_coins = []

        top_100_crypto = {}
        my_crypto = {}

        current_time = time.time()
        if current_time - self.last_api_call < self.cache_duration:
            return top_100_crypto, my_crypto

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
            return top_100_crypto, my_crypto

        for crypto in data["data"]:
            symbol = crypto["symbol"]
            if symbol in wanted_coins:
                my_crypto[symbol] = {
                    "price": crypto["quote"]["USD"]["price"],
                    "change_1h": crypto["quote"]["USD"]["percent_change_1h"],
                    "change_24h": crypto["quote"]["USD"]["percent_change_24h"],
                    "change_7d": crypto["quote"]["USD"]["percent_change_7d"],
                    "change_30d": crypto["quote"]["USD"]["percent_change_30d"],
                }
            top_100_crypto[symbol] = {
                "price": crypto["quote"]["USD"]["price"],
                "change_1h": crypto["quote"]["USD"]["percent_change_1h"],
                "change_24h": crypto["quote"]["USD"]["percent_change_24h"],
                "change_7d": crypto["quote"]["USD"]["percent_change_7d"],
                "change_30d": crypto["quote"]["USD"]["percent_change_30d"],
            }

        return top_100_crypto, my_crypto
