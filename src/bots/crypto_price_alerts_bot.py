"""
Price Alert Bot for Telegram
This bot checks for significant price movements in cryptocurrencies
"""

import asyncio
import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.handlers import load_variables_handler
from src.handlers.crypto_price_alerts_buttons import CryptoPriceAlertsButtons
from src.handlers.crypto_price_alerts_main_loop import PriceAlertMainLoop
from src.handlers.logger_handler import setup_logger

# pylint: disable=wrong-import-position,broad-exception-caught


setup_logger(file_name="crypto_price_alerts_bot.log")
logger = logging.getLogger(__name__)
logger.info("Crypto price Alerts bot started")


class PriceAlertBot:
    """
    Price Alert Bot for Telegram
    """

    def __init__(self):
        """
        Initializes the Price Alert Bot with necessary components.
        """
        self.buttons_handler = CryptoPriceAlertsButtons()
        self.main_loop = PriceAlertMainLoop()

    # Main function to start the bot
    async def run_bot(self):
        """Start the bot without blocking"""
        variables = load_variables_handler.load_json()
        bot_token = variables.get("TELEGRAM_API_TOKEN_ALERTS", "")

        app = Application.builder().token(bot_token).build()

        app.add_handler(CommandHandler("help", self.buttons_handler.help_command))
        app.add_handler(CommandHandler("start", self.buttons_handler.start))
        app.add_handler(CommandHandler("cancel", self.buttons_handler.cancel_command))
        app.add_handler(
            CommandHandler("alert_1h", self.buttons_handler.alert_1h_command)
        )
        app.add_handler(
            CommandHandler("alert_24h", self.buttons_handler.alert_24h_command)
        )
        app.add_handler(
            CommandHandler("alert_7d", self.buttons_handler.alert_7d_command)
        )
        app.add_handler(
            CommandHandler("alert_30d", self.buttons_handler.alert_30d_command)
        )
        app.add_handler(
            CommandHandler("alert_all", self.buttons_handler.alert_all_command)
        )
        app.add_handler(CommandHandler("rsi_1h", self.buttons_handler.rsi_1h_command))
        app.add_handler(CommandHandler("rsi_4h", self.buttons_handler.rsi_4h_command))
        app.add_handler(CommandHandler("rsi_1d", self.buttons_handler.rsi_1d_command))
        app.add_handler(CommandHandler("rsi_w1", self.buttons_handler.rsi_1w_command))
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, self.buttons_handler.handle_buttons
            )
        )

        print("🤖 Alert Bot is running...")

        # Non-blocking way: initialize, start, and keep alive
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        # Keep this task alive until cancelled
        await asyncio.Event().wait()

    async def run_loop(self):
        """Main application loop"""
        logger.info("Starting main loop...")
        print("🧐 Starting main loop...")
        while True:
            self.main_loop.reload_the_data()

            logger.info("Checking for market major updates...")
            await self.main_loop.check_for_major_updates()

            logger.info("\nChecking RSI values...")
            await self.main_loop.rsi_check()

            sleep_time = load_variables_handler.get_int_variable("SLEEP_DURATION", 1800)
            logger.info("Waiting for %.2f minutes", sleep_time / 60)

            print(f"\n⏳ Waiting {sleep_time / 60:.2f} minutes!\n\n")
            await asyncio.sleep(sleep_time)

    async def main(self):
        await asyncio.gather(self.run_loop(), self.run_bot())


if __name__ == "__main__":
    bot = PriceAlertBot()
    asyncio.run(bot.main())
