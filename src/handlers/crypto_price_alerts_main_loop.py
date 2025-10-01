from src.handlers.alerts_handler import AlertsHandler
from src.handlers.get_crypto_data import GetCryptoDataHandler


class PriceAlertMainLoop:
    def __init__(self):
        self.top_100_crypto = None
        self.get_crypto_data_handler = GetCryptoDataHandler()
        self.alert_handler = AlertsHandler()

    def reload_the_data(self):
        """
        Reloads the configuration data for the price alert handler.
        This includes updating the top 100 cryptocurrencies and alert thresholds.
        """
        self.alert_handler.reload_the_data()
        self.get_crypto_data_handler.reload_the_data()

        self.top_100_crypto = {}

        self.top_100_crypto, dummy = self.get_crypto_data_handler.get_crypto_data()

    async def check_for_major_updates(self, update=None):
        """
        Checks for major price changes in the top 100 cryptocurrencies and
        sends alerts if any are found.
        Args:
            update: Optional; if provided, the message will be sent as a reply to this update.
        """
        return await self.alert_handler.check_for_alerts(self.top_100_crypto, update)

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

    async def rsi_check(self):
        """
        Checks the Relative Strength Index (RSI) for Binance and sends alerts if any are found.
        """
        return await self.alert_handler.rsi_check()
