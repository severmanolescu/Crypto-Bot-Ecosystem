"""
CryptoRSIHandler class to handle RSI calculations for different timeframes.
"""

import logging
from datetime import datetime, timedelta, timezone

from src.handlers.crypto_rsi_calculator import CryptoRSICalculator
from src.handlers.load_variables_handler import load_json
from src.handlers.save_data_handler import save_new_rsi_data
from src.handlers.send_telegram_message import TelegramMessagesHandler

logger = logging.getLogger(__name__)
logger.info("Crypto RSI handler started")


class CryptoRSIHandler:
    """
    CryptoRSIHandler class to handle RSI calculations for different timeframes.
    """

    def __init__(self):
        """
        Initializes the CryptoRSIHandler with necessary components.
        """
        self.telegram_handler = TelegramMessagesHandler()
        self.should_calculate_rsi = True

        self.json = {}
        self.message = None

        self.new_data = None

    def reload_data(self):
        """
        Reload the data from the configuration file and update the Telegram chat IDs
        """
        self.telegram_handler.reload_the_data()

    def prepare_message_for_timeframes_parallel(self, timeframe="1h"):
        """
        Calculate RSI for the specified timeframe using the CryptoRSIHandler.
        Args:
            timeframe (str): The timeframe for which to calculate RSI.
        Returns:
            dict: The RSI data for the specified timeframe.
        """
        try:
            rsi_handler = CryptoRSICalculator()
            rsi_data = rsi_handler.calculate_rsi_for_timeframes_parallel(timeframe)

            if rsi_data:
                logger.info("RSI data calculated and updated for %s", timeframe)
                return rsi_data

            logger.warning("No RSI data available for %s", timeframe)
        # pylint:disable=broad-exception-caught
        except Exception as e:
            logger.error("Error calculating RSI for %s: %s", timeframe, e)

        return {}

    def send_new_rsi_to_telegram(self, rsi_data):
        """
        Prepare RSI data for sending via Telegram.
        Args:
            rsi_data (dict): The RSI data to prepare.
        """
        if not rsi_data:
            logger.error("No RSI data available.")

            self.message = "An error occurred while fetching RSI data."
            return

        rsi_value = rsi_data.get("values")
        if rsi_value is None:
            logger.error("RSI value is not available.")

            self.message = "An error occurred while fetching RSI data."
            return

        self.message = "RSI Data: \n"

        for key, value in rsi_value.items():
            if value > 70:
                self.message += f"{key}: <b>{value:.2f}</b>\n"
            elif value < 30:
                self.message += f"{key}: <b>{value:.2f}</b>\n"

    def send_json_rsi_to_telegram(self, timeframe="1h"):
        """
        Send RSI data to Telegram using the TelegramMessagesHandler.
        Args:
            timeframe (str): The timeframe for which the RSI data is sent.
        """
        rsi_data = self.json.get(timeframe, {}).get("values", {})

        if not rsi_data:
            logger.warning("No RSI data available for %s", timeframe)
            self.message = "An error occurred while fetching RSI data."
            return

        self.message = "RSI Data:\n"
        for symbol, value in rsi_data.items():
            self.message += f"{symbol}: <b>{value:.2f}</b>\n"

    async def send_rsi_to_telegram(self, bot, is_important=False, update=None):
        """
        Send RSI data to Telegram for the specified timeframe.
        Args:
            bot (Bot): The Telegram bot instance to send messages.
            is_important (bool): Flag to indicate if the message is important.
            update (Update, optional): The update object containing the message context.
        """
        if not self.message:
            logger.error("Failed to calculate or send RSI data.")
            self.message = "An error occurred while fetching RSI data."

        telegram_handler = TelegramMessagesHandler()
        await telegram_handler.send_telegram_message(
            self.message, bot, is_important, update
        )

    def check_if_should_calculate_rsi(self, timeframe):
        """
        Check if RSI should be calculated based on the last check time.
        Args:
            timeframe (str): The timeframe for which to check the last calculation.
        Returns:
            bool: True if RSI should be calculated, False otherwise.
        """
        try:
            date_str = self.json[timeframe]["date"]
            last_check = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )

            now = datetime.now(timezone.utc)
            diff = now - last_check

            self.should_calculate_rsi = diff > timedelta(minutes=5)

            if self.should_calculate_rsi:
                logger.info(
                    "RSI should be calculated for %s, last check was %s ago",
                    timeframe,
                    diff,
                )
            else:
                logger.info(
                    "RSI does not need to be calculated for %s, last check was %s ago",
                    timeframe,
                    diff,
                )
        # pylint:disable=broad-exception-caught
        except Exception as e:
            logger.error("Error parsing date: %s", e)
            self.should_calculate_rsi = True

    async def send_rsi_for_timeframe(
        self, timeframe, bot, is_important=False, update=None
    ):
        """
        Calculate RSI for the specified timeframe using the CryptoRSIHandler.
        Args:
            timeframe (str): The timeframe for which to calculate RSI.
            bot (Bot): The Telegram bot instance to send messages.
            is_important (bool): Flag to indicate if the message is important.
            update (Update, optional): The update object containing the message context.
        """
        self.reload_data()

        self.json = load_json("./config/rsi_data.json")

        await self.telegram_handler.send_telegram_message(
            "Calculating RSI...", bot, is_important, update
        )

        if isinstance(self.json, dict) and timeframe in self.json:
            self.check_if_should_calculate_rsi(timeframe)

        if self.should_calculate_rsi:
            rsi_data = self.prepare_message_for_timeframes_parallel(timeframe)

            self.send_new_rsi_to_telegram(rsi_data)

            save_new_rsi_data(self.json, timeframe, rsi_data)
        else:
            self.send_json_rsi_to_telegram(timeframe)

        await self.send_rsi_to_telegram(bot, is_important, update)
