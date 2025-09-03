"""
News Check Bot
This bot checks for crypto news articles and provides market sentiment analysis.
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

import src.handlers.load_variables_handler
from src.handlers import load_variables_handler
from src.handlers.logger_handler import setup_logger
from src.handlers.news_check_buttons import NewsCheckButtons
from src.handlers.news_check_handler import CryptoNewsCheck

# pylint: disable=wrong-import-position,duplicate-code

setup_logger(file_name="news_check_bot.log")
logger = logging.getLogger(__name__)
logger.info("News Check started")


class NewsBot:
    """
    NewsBot class to handle news checking and market sentiment analysis.
    """

    def __init__(self):
        """
        Initializes the NewsBot with necessary components and configurations.
        """
        self.buttons_handler = NewsCheckButtons()
        self.crypto_news_check = CryptoNewsCheck()

    # Main function to start the bot
    async def run_bot(self):
        """
        Initializes the bot and starts polling for updates.
        """
        variables = src.handlers.load_variables_handler.load_json()

        bot_token = variables.get("TELEGRAM_API_TOKEN_ARTICLES", "")

        app = Application.builder().token(bot_token).build()

        # Add command and message handlers
        app.add_handler(CommandHandler("help", self.buttons_handler.help_command))
        app.add_handler(CommandHandler("start", self.buttons_handler.start))
        app.add_handler(CommandHandler("cancel", self.buttons_handler.cancel_command))

        app.add_handler(CommandHandler("search", self.buttons_handler.search))
        app.add_handler(
            CommandHandler("sentiment", self.buttons_handler.market_sentiment_command)
        )
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, self.buttons_handler.handle_buttons
            )
        )

        # Start the bot
        print("🤖 News Bot is running...")

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
            self.crypto_news_check.reload_the_data()

            print("\n🧐 Check for new articles!")
            await self.crypto_news_check.run()

            sleep_time = load_variables_handler.get_int_variable("SLEEP_DURATION", 1800)
            logger.info("Waiting for %.2f minutes", sleep_time / 60)

            print(f"\n⏳ Waiting {sleep_time / 60:.2f} minutes!\n\n")
            await asyncio.sleep(sleep_time)

    async def main(self):
        """
        Main function to run the NewsBot and its loop concurrently.
        """
        await asyncio.gather(self.run_loop(), self.run_bot())


if __name__ == "__main__":
    news_bot = NewsBot()
    asyncio.run(news_bot.main())
