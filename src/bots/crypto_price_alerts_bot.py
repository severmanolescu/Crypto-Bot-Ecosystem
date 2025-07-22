"""
Price Alert Bot for Telegram
This bot checks for significant price movements in cryptocurrencies
"""

import asyncio
import logging
import os
import sys

# pylint: disable=wrong-import-position,broad-exception-caught


sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.bots.crypto_value_handler import CryptoValueBot
from src.handlers import load_variables_handler
from src.handlers.crypto_rsi_handler import CryptoRSIHandler
from src.handlers.logger_handler import setup_logger

setup_logger(file_name="crypto_price_alerts_bot.log")
logger = logging.getLogger(__name__)
logger.info("Crypto price Alerts bot started")

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📈 RSI", "📊 Value Check"],
        ["🔙 Help"],
    ],
    resize_keyboard=True,
)

RSI_MENU = ReplyKeyboardMarkup(
    [
        ["RSI 1H", "RSI 4H", "RSI 1D", "RSI 1W"],
        ["RSI all timeframes", "🔙 Back to Menu"],
    ],
    resize_keyboard=True,
)

VALUE_MENU = ReplyKeyboardMarkup(
    [
        ["Value 1H", "Value 1D", "Value 1W", "Value 1M"],
        ["Value all timeframes", "🔙 Back to Menu"],
    ],
    resize_keyboard=True,
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
        self.rsi_handler = CryptoRSIHandler()

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
            reply_markup=MAIN_MENU,
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

    async def handle_alerts_buttons(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle the buttons for checking alerts based on user input.
        """
        text = update.message.text

        if text.lower() == "value 1h" or text.lower() == "alerth":
            await update.message.reply_text(
                "🚨 Searching for new alerts for 1h update..."
            )

            alert_available = await self.start_the_alerts_check_1h(update)

            if not alert_available:
                await update.message.reply_text(
                    "😔 No major price movement for 1h timeframe"
                )

        elif text.lower() == "value 1d" or text.lower() == "alertd":
            await update.message.reply_text(
                "🔔 Searching for new alerts for 24h update..."
            )

            alert_available = await self.start_the_alerts_check_24h(update)

            if not alert_available:
                await update.message.reply_text(
                    "😔 No major price movement for 24h timeframe"
                )

        elif text.lower() == "value 1w" or text.lower() == "alertw":
            await update.message.reply_text(
                "⚠️ Searching for new alerts for 7d update..."
            )

            alert_available = await self.start_the_alerts_check_7d(update)

            if not alert_available:
                await update.message.reply_text(
                    "😔 No major price movement for 7d timeframe"
                )

        elif text.lower() == "value 1m" or text.lower() == "alertm":
            await update.message.reply_text(
                "📢 Searching for new alerts for 30d update..."
            )

            alert_available = await self.start_the_alerts_check_30d(update)

            if not alert_available:
                await update.message.reply_text(
                    "😔 No major price movement for 30d timeframe"
                )

        elif text.lower() == "value all timeframes" or text.lower() == "alertall":
            await update.message.reply_text(
                "🌐 Searching for new alerts for all timeframes..."
            )

            alert_available = await self.start_the_alerts_check_all_timeframes(update)

            if not alert_available:
                await update.message.reply_text(
                    "😔 No major price movement for 30d timeframe"
                )
        else:
            logger.error(" Invalid command. Please use the buttons below.")
            await update.message.reply_text(
                "❌ Invalid command. Please use the buttons below."
            )

    async def handle_rsi_buttons(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle the buttons for checking RSI based on user input.
        """
        text = update.message.text

        self.rsi_handler.reload_the_data()

        timeframe = None

        if text.lower() == "rsi 1h" or text == "1h":
            await update.message.reply_text("⚡ Checking RSI for 1h timeframe...")

            timeframe = "1h"

        elif text.lower() == "rsi 4h" or text == "4h":
            await update.message.reply_text("🔥 Checking RSI for 4h timeframe...")

            timeframe = "4h"

        elif text.lower() == "rsi 1d" or text == "1d":
            await update.message.reply_text("⚠️ Checking RSI for 1d timeframe...")

            timeframe = "1d"

        elif text.lower() == "rsi 1w" or text == "1w":
            await update.message.reply_text("🚨 Checking RSI for 1w timeframe...")

            timeframe = "1w"

        elif text == " rsi all timeframes" or text.lower() == "all":

            await update.message.reply_text("📊 Checking RSI for all timeframes...")

            timeframe = "all"

        if timeframe:
            try:
                if timeframe == "all":
                    # Send RSI data to Telegram
                    logger.info("Starting to send RSI for all timeframes...")
                    timeframes = ["1h", "4h", "1d", "1w"]

                    for timeframe in timeframes:
                        await asyncio.wait_for(
                            self.rsi_handler.send_rsi_for_timeframe(
                                timeframe=timeframe, bot=None, update=update
                            ),
                            timeout=180,  # 3 minutes timeout
                        )
                else:
                    # Send RSI data to Telegram
                    await asyncio.wait_for(
                        self.rsi_handler.send_rsi_for_timeframe(
                            timeframe=timeframe, bot=None, update=update
                        ),
                        timeout=180,  # 3 minutes timeout
                    )
            except asyncio.TimeoutError:
                logger.error("Timeout occurred while sending RSI data.")
                await update.message.reply_text(
                    "⏳ Timeout occurred while processing your request. Please try again."
                )
            except Exception as e:
                logger.error("An error occurred while sending RSI data: %s", e)
                await update.message.reply_text(
                    "❌ An error occurred while processing your request. Please try again."
                )
        else:
            logger.error(" Invalid timeframe specified.")
            await update.message.reply_text(
                "❌ Invalid timeframe specified. Please use the buttons below."
            )

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

        if text == "📈 RSI":
            await update.message.reply_text(
                "Choose RSI timeframe:", reply_markup=RSI_MENU
            )
            return

        elif text == "📊 Value Check":
            await update.message.reply_text(
                "Choose Value timeframe:", reply_markup=VALUE_MENU
            )
            return

        elif text == "🔙 Back to Menu":
            await update.message.reply_text(
                "Back to main menu.", reply_markup=MAIN_MENU
            )
            return

        logger.info(" Check for Alerts")

        if "value" in text.lower():
            await self.handle_alerts_buttons(update, context)
        elif "rsi" in text.lower():
            await self.handle_rsi_buttons(update, context)
        else:
            logger.error("Invalid command. Please use the buttons below.")
            await update.message.reply_text(
                "❌ Invalid command. Please use the buttons below."
            )

    # Main function to start the bot
    def run_bot(self):
        """
        Main function to start the Price Alert Bot.
        This function initializes the bot, sets up command and message handlers,
        """
        variables = load_variables_handler.load_json()

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
