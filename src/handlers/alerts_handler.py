"""
Alerts module for monitoring significant price changes in cryptocurrencies.
"""

import asyncio
import logging
from datetime import datetime

from src.handlers import load_variables_handler as LoadVariables
from src.handlers.crypto_rsi_handler import CryptoRSIHandler
from src.handlers.send_telegram_message import TelegramMessagesHandler
from src.utils.utils import format_change

logger = logging.getLogger(__name__)
logger.info("Alerts script started")


# pylint:disable=too-many-instance-attributes, broad-exception-caught
class AlertsHandler:
    """
    Handles alerts for significant price changes in cryptocurrencies.
    """

    def __init__(self):
        """
        Initializes the AlertsHandler with default values and loads configuration.
        """
        self.alert_threshold_1h = None
        self.alert_threshold_24h = None
        self.alert_threshold_7d = None
        self.alert_threshold_30d = None

        self.alert_send_hours_24h = None
        self.alert_send_hours_7d = None
        self.alert_send_hours_30d = None

        self.telegram_api_token_alerts = None

        self.last_hour_sent = None

        self.send_rsi_alerts = None

        self.telegram_message = TelegramMessagesHandler()
        self.rsi_handler = CryptoRSIHandler()

        self.reload_the_data()

    def reload_the_data(self):
        """
        Reloads the configuration data for alerts from the variables file.
        """
        variables = LoadVariables.load_json()

        self.telegram_api_token_alerts = variables.get("TELEGRAM_API_TOKEN_ALERTS", "")

        self.alert_threshold_1h = variables.get("ALERT_THRESHOLD_1H", 2.5)
        self.alert_threshold_24h = variables.get("ALERT_THRESHOLD_24H", 5)
        self.alert_threshold_7d = variables.get("ALERT_THRESHOLD_7D", 10)
        self.alert_threshold_30d = variables.get("ALERT_THRESHOLD_30D", 10)

        self.alert_send_hours_24h = variables.get("24H_ALERTS_SEND_HOURS", "")
        self.alert_send_hours_7d = variables.get("7D_ALERTS_SEND_HOURS", "")
        self.alert_send_hours_30d = variables.get("30D_ALERTS_SEND_HOURS", "")

        self.send_rsi_alerts = variables.get("SEND_RSI_ALERTS", False)

        self.telegram_message.reload_the_data()
        self.rsi_handler.reload_the_data()

    # Check for alerts every 30 minutes
    async def check_for_major_updates_1h(self, top_100_crypto, update=None):
        """
        Checks for significant price changes in the last hour for the top 100 cryptocurrencies.
        """
        alert_message = (
            "🚨 <b>Crypto Alert!</b> Significant 1-hour change detected:\n\n"
        )
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_1h = data["change_1h"]

            if abs(change_1h) >= self.alert_threshold_1h:
                alerts_found = True
                alert_message += f"<b>{symbol}</b> → {format_change(change_1h)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(
                alert_message, self.telegram_api_token_alerts, False, update
            )

            return True

        logger.error("No major price movement for 1h!")
        print("\nNo major 1h price movement at ", datetime.now(), "\n")

        return False

    async def check_for_major_updates_24h(self, top_100_crypto, update=None):
        """
        Checks for significant price changes in the last 24 hours for the top 100 cryptocurrencies.
        """
        alert_message = (
            "🚨 <b>Crypto Alert!</b> Significant 24-hours change detected:\n\n"
        )
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_24h = data["change_24h"]

            if abs(change_24h) >= self.alert_threshold_24h:
                alerts_found = True
                alert_message += f"<b>{symbol}</b> → {format_change(change_24h)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(
                alert_message, self.telegram_api_token_alerts, False, update
            )

            return True

        logger.error(" No major price movement for 24h!")
        print("No major 24h price movement at ", datetime.now(), "\n")

        return False

    async def check_for_major_updates_7d(self, top_100_crypto, update=None):
        """
        Checks for significant price changes in the last 7 days for the top 100 cryptocurrencies.
        """
        alert_message = (
            "🚨 <b>Crypto Alert!</b> Significant 7-days change detected:\n\n"
        )
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_7d = data["change_7d"]

            if abs(change_7d) >= self.alert_threshold_7d:
                alerts_found = True
                alert_message += f"<b>{symbol}</b> → {format_change(change_7d)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(
                alert_message, self.telegram_api_token_alerts, False, update
            )

            return True
        logger.error(" No major price movement for 7d!")
        print("\nNo major 7d price movement at ", datetime.now(), "\n")

        return False

    async def check_for_major_updates_30d(self, top_100_crypto, update=None):
        """
        Checks for significant price changes in the last 30 days for the top 100 cryptocurrencies.
        """
        alert_message = (
            "🚨 <b>Crypto Alert!</b> Significant 30-days change detected:\n\n"
        )
        alerts_found = False

        for symbol, data in top_100_crypto.items():
            change_30d = data["change_30d"]

            if abs(change_30d) >= self.alert_threshold_30d:
                alerts_found = True
                alert_message += f"<b>{symbol}</b> → {format_change(change_30d)}\n"

        if alerts_found:
            await self.telegram_message.send_telegram_message(
                alert_message, self.telegram_api_token_alerts, False, update
            )

            return True

        logger.error(" No major price movement for 30d!")
        print("\nNo major 30d price movement at: ", datetime.now(), "\n")

        return False

    async def check_for_alerts(self, now_date, top_100_crypto, update=None):
        """
        Checks for significant price changes in the top 100 cryptocurrencies
        """
        await self.check_for_major_updates_1h(top_100_crypto, update)

        found_alerts = False

        if now_date is None or self.last_hour_sent != now_date.hour:
            self.last_hour_sent = datetime.now()

            if now_date is None or now_date.hour in self.alert_send_hours_24h:
                found_alerts = await self.check_for_major_updates_24h(
                    top_100_crypto, update
                )
            if now_date is None or now_date.hour in self.alert_send_hours_7d:
                found_alerts = await self.check_for_major_updates_7d(
                    top_100_crypto, update
                )
            if now_date is None or now_date.hour in self.alert_send_hours_30d:
                found_alerts = await self.check_for_major_updates_30d(
                    top_100_crypto, update
                )

        return found_alerts

    async def rsi_check(self):
        """
        Checks and sends RSI alerts for all timeframes if enabled.
        """

        if not self.send_rsi_alerts:
            logger.info("RSI alerts are disabled.")
            return

        logger.info("Starting to send RSI for all timeframes...")
        timeframes = ["1h", "4h", "1d", "1w"]

        for timeframe in timeframes:
            try:
                # Send RSI data to Telegram
                await asyncio.wait_for(
                    self.rsi_handler.send_rsi_for_timeframe(
                        timeframe=timeframe, bot=self.telegram_api_token_alerts
                    ),
                    timeout=180,  # 3 minutes timeout
                )
            except asyncio.TimeoutError:
                logger.error("Timeout occurred while sending RSI data.")
                await self.telegram_message.send_telegram_message(
                    "⏳ Timeout occurred while sending RSI data for timeframe: "
                    + timeframe
                    + ". Please try again.",
                    self.telegram_api_token_alerts,
                )
            except Exception as e:
                logger.error("An error occurred while sending RSI data: %s", e)
                await self.telegram_message.send_telegram_message(
                    "❌ An error occurred while processing your request for timeframe: "
                    + timeframe
                    + ". Please try again.",
                    self.telegram_api_token_alerts,
                )
