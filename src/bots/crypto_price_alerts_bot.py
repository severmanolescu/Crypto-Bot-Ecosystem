"""
Price Alert Bot for Telegram
This bot checks for significant price movements in cryptocurrencies
"""

# pylint: disable=wrong-import-position

import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.bots.crypto_value_handler import CryptoValueBot
from src.handlers import load_variables_handler as LoadVariables
from src.handlers.logger_handler import setup_logger

setup_logger("crypto_price_alerts_bot")
logger = logging.getLogger(__name__)
logger.info("Crypto price Alerts bot started")

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Check for 1h Alerts", "🚨 Check for 24h Alerts"],
        ["🚨 Check for 7d Alerts", "🚨 Check for 30d Alerts"],
        ["🚨 Check for all timeframes Alerts"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


class PriceAlertBot:
    """
    Price Alert Bot for Telegram
    """

    def __init__(self):
        """
        Initializes the Price Alert Bot with necessary components.
        """
        self.crypto_value_bot = CryptoValueBot()

    # Command: /start
    # pylint:disable=unused-argument
    async def start(self, update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start command handler for the bot.
        Args:
            update: The update object from Telegram.
            context: The context object from Telegram.
        """
        await update.message.reply_text(
            "🤖 Welcome to the Alert Bot! Use the buttons below to get started:",
            reply_markup=NEWS_KEYBOARD,
        )

    async def start_the_alerts_check_1h(self, update=None):
        """
        Start the alerts check for 1-hour timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        self.crypto_value_bot.reload_the_data()

        self.crypto_value_bot.get_my_crypto()

        return await self.crypto_value_bot.check_for_major_updates_1h(update)

    async def start_the_alerts_check_24h(self, update=None):
        """
        Start the alerts check for 24-hour timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        self.crypto_value_bot.reload_the_data()

        self.crypto_value_bot.get_my_crypto()

        return await self.crypto_value_bot.check_for_major_updates_24h(update)

    async def start_the_alerts_check_7d(self, update=None):
        """
        Start the alerts check for 7-day timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        self.crypto_value_bot.reload_the_data()

        self.crypto_value_bot.get_my_crypto()

        return await self.crypto_value_bot.check_for_major_updates_7d(update)

    async def start_the_alerts_check_30d(self, update=None):
        """
        Start the alerts check for 30-day timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        self.crypto_value_bot.reload_the_data()

        self.crypto_value_bot.get_my_crypto()

        return await self.crypto_value_bot.check_for_major_updates_30d(update)

    async def start_the_alerts_check_all_timeframes(self, update=None):
        """
        Start the alerts check for all timeframes.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        self.crypto_value_bot.reload_the_data()

        self.crypto_value_bot.get_my_crypto()

        return await self.crypto_value_bot.check_for_major_updates(None, update)

    # Handle button presses
    # pylint:disable=unused-argument
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle button presses for checking alerts.
        Args:
            update: The update object from Telegram.
            context: The context object from Telegram.
        """
        text = update.message.text

        logger.info(" Check for Alerts")

        if text == "🚨 Check for 1h Alerts" or text.lower() == "1h":
            await update.message.reply_text(
                "🚨 Searching for new alerts for 1h update..."
            )

            alert_available = await self.start_the_alerts_check_1h(update)

            if alert_available is False:
                await update.message.reply_text(
                    "😔 No major price movement for 1h timeframe"
                )

        elif text == "🚨 Check for 24h Alerts" or text.lower() == "24h":
            await update.message.reply_text(
                "🚨 Searching for new alerts for 24h update..."
            )

            alert_available = await self.start_the_alerts_check_24h(update)

            if alert_available is False:
                await update.message.reply_text(
                    "😔 No major price movement for 24h timeframe"
                )

        elif text == "🚨 Check for 7d Alerts" or text.lower() == "7d":
            await update.message.reply_text(
                "🚨 Searching for new alerts for 7d update..."
            )

            alert_available = await self.start_the_alerts_check_7d(update)

            if alert_available is False:
                await update.message.reply_text(
                    "😔 No major price movement for 7d timeframe"
                )

        elif text == "🚨 Check for 30d Alerts" or text.lower() == "30d":
            await update.message.reply_text(
                "🚨 Searching for new alerts for 30d update..."
            )

            alert_available = await self.start_the_alerts_check_30d(update)

            if alert_available is False:
                await update.message.reply_text(
                    "😔 No major price movement for 30d timeframe"
                )

        elif text == "🚨 Check for all timeframes Alerts" or text.lower() == "all":
            await update.message.reply_text(
                "🚨 Searching for new alerts for all timeframes..."
            )

            alert_available = await self.start_the_alerts_check_all_timeframes(update)

            if alert_available is False:
                await update.message.reply_text(
                    "😔 No major price movement for 30d timeframe"
                )
        else:
            logger.error(" Invalid command. Please use the buttons below.")
            await update.message.reply_text(
                "❌ Invalid command. Please use the buttons below."
            )

    # Main function to start the bot
    def run_bot(self):
        """
        Main function to start the Price Alert Bot.
        This function initializes the bot, sets up command and message handlers,
        """
        variables = LoadVariables.load()

        bot_token = variables.get("TELEGRAM_API_TOKEN_ALERTS", "")

        app = Application.builder().token(bot_token).build()

        # Add command and message handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_buttons)
        )

        # Start the bot
        print("🤖 Alert Bot is running...")
        app.run_polling()


if __name__ == "__main__":
    price_alert_bot = PriceAlertBot()

    price_alert_bot.run_bot()
