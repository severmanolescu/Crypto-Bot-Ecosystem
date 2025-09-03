"""
CryptoRSIHandler class to handle RSI calculations for different timeframes.
"""

import logging
from datetime import datetime, timedelta, timezone

from src.handlers.crypto_rsi_calculator import CryptoRSICalculator
from src.handlers.load_variables_handler import load_json, load_rsi_categories
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

    def reload_the_data(self):
        """
        Reload the data from the configuration file and update the Telegram chat IDs
        """
        self.telegram_handler.reload_the_data()
        self.should_calculate_rsi = True

    async def prepare_rsi_timeframes_parallel(self, timeframe="1h"):
        """
        Calculate RSI for the specified timeframe using the CryptoRSIHandler.
        Args:
            timeframe (str): The timeframe for which to calculate RSI.
        Returns:
            dict: The RSI data for the specified timeframe.
        """
        try:
            rsi_handler = CryptoRSICalculator()
            rsi_data = await rsi_handler.calculate_rsi_for_timeframes_parallel(
                timeframe
            )

            if rsi_data:
                logger.info("RSI data calculated and updated for %s", timeframe)
                return rsi_data

            logger.warning("No RSI data available for %s", timeframe)
        # pylint:disable=broad-exception-caught
        except Exception as e:
            logger.error("Error calculating RSI for %s: %s", timeframe, e)

        return {}

    def prepare_rsi_message_for_telegram(self, timeframe, rsi_data):
        """
        Prepare the RSI message for Telegram based on the calculated RSI data.
        Args:
            timeframe (str): The timeframe for which the RSI data is calculated.
            rsi_data (dict): The RSI data for the specified timeframe.
        """
        if not rsi_data:
            logger.error("No RSI data available.")
            self.message = "An error occurred while fetching RSI data."
            return

        lines = [f"📊 <b>RSI Data for {timeframe}:</b>\n"]
        any_found = False

        rsi_categories = load_rsi_categories()

        # Bucket each symbol into the right category
        buckets = {cat["name"]: [] for cat in rsi_categories}
        for symbol, value in rsi_data.items():
            for cat in rsi_categories:
                if cat["test"](value):
                    buckets[cat["name"]].append((symbol, value))
                    break

        # Build the message
        for cat in rsi_categories:
            entries = buckets[cat["name"]]
            if not entries:
                continue
            any_found = True

            # Header
            lines.append(f"{cat['emoji']} <b>{cat['name']} ({cat['label']}):</b>")
            # Entries
            for symbol, value in sorted(entries, key=lambda x: -x[1]):
                lines.append(f"- <i>{symbol}</i> — <b>{value:.2f}</b>")
            lines.append(
                "---------------------------------------------------------------"
            )

        if not any_found:
            lines.append("<i>No significant RSI values found.</i>")

        lines.append("#RSI")
        self.message = "\n".join(lines)

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
        await telegram_handler.send_telegram_message_price_alerts(
            self.message, bot, update
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
            if self.json is None or not isinstance(self.json, dict):
                logger.error("JSON data is not loaded or is not a dictionary.")
                self.should_calculate_rsi = True
                return

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
        logger.info("Sending RSI for timeframe: %s", timeframe)
        self.json = load_json("./config/rsi_data.json")

        if isinstance(self.json, dict) and timeframe in self.json:
            self.check_if_should_calculate_rsi(timeframe)
        else:
            logger.info("No RSI data found for %s, will calculate new data", timeframe)
            self.should_calculate_rsi = True

        if self.should_calculate_rsi:
            rsi_data = await self.prepare_rsi_timeframes_parallel(timeframe)

            self.prepare_rsi_message_for_telegram(timeframe, rsi_data.get("values"))

            save_new_rsi_data(self.json, timeframe, rsi_data)
        else:
            self.prepare_rsi_message_for_telegram(
                timeframe, self.json.get(timeframe, {}).get("values", {})
            )

        await self.send_rsi_to_telegram(bot, is_important, update)

    async def send_rsi_for_all_timeframes(self, bot, is_important=False, update=None):
        """
        Calculate RSI for all timeframes using the CryptoRSIHandler.
        Args:
            bot (Bot): The Telegram bot instance to send messages.
            is_important (bool): Flag to indicate if the message is important.
            update (Update, optional): The update object containing the message context.
        """
        logger.info("Starting to send RSI for all timeframes...")
        timeframes = ["1h", "4h", "1d", "1w"]

        for timeframe in timeframes:
            await self.send_rsi_for_timeframe(timeframe, bot, is_important, update)
