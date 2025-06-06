"""
News Check Bot
This bot checks for crypto news articles and provides market sentiment analysis.
"""

import logging

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import sdk.load_variables_handler
from news_check_handler import CryptoNewsCheck
from sdk.data_base.data_base_handler import DataBaseHandler
from sdk.logger_handler import setup_logger
from sdk.market_sentiment_handler import get_market_sentiment
from sdk.send_telegram_message import send_telegram_message_update

setup_logger("news_check_bot")
logger = logging.getLogger(__name__)
logger.info("News Check started")

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Check for Articles", "🔢 Show statistics"],
        ["📊 Market Sentiment", "🚨 Help"],
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)


class NewsBot:
    """
    NewsBot class to handle news checking and market sentiment analysis.
    """

    def __init__(self):
        """
        Initializes the NewsBot with necessary components.
        """
        self.crypto_news_check = CryptoNewsCheck()

        self.db = DataBaseHandler()

    # Command: /start
    # pylint:disable=unused-argument
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command to initialize the bot and show buttons.
        """
        await send_telegram_message_update(
            "🤖 Welcome to the News Bot! Use the buttons below to get started:", update
        )

    async def start_the_articles_check(self, update):
        """
        Starts the article check process and sends a message to the user.
        Args:
            update (Update): The update object containing the message.
        """
        logger.info(" Requested: Article Check")

        self.crypto_news_check.reload_the_data()

        await self.crypto_news_check.run_from_bot(update)

    async def market_sentiment(self, update):
        """
        Handles the market sentiment command to calculate and send market sentiment.
        Args:
            update (Update): The update object containing the message.
        """
        message = await get_market_sentiment()

        await send_telegram_message_update(message, update)

    # Handle button presses
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles button presses and executes the corresponding command.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        text = update.message.text

        text_lower = text.lower()

        if text == "🚨 Check for Articles" or text_lower == "check":
            await send_telegram_message_update("🚨 Check for articles...", update)

            await self.start_the_articles_check(update)
        elif text == "🔢 Show statistics" or text_lower == "statistics":
            await send_telegram_message_update("🔢 Showing the statistics...", update)

            await self.db.show_stats(update)
        elif text == "📊 Market Sentiment" or text_lower == "sentiment":
            await send_telegram_message_update(
                "🧮 Calculating the sentiment...", update
            )

            await self.market_sentiment(update)
        elif text == "🚨 Help" or text.lower() == "help":
            await self.help_command(update, context)
        else:
            logger.error(" Invalid command. Please use the buttons below.")
            await send_telegram_message_update(
                "❌ Invalid command. Please use the buttons below.", update
            )

    # Command: /start
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /search command to search for articles by tags.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if not context.args:
            await send_telegram_message_update("❌ Usage: /search <tags>", update)
            return

        articles = await self.db.search_articles_by_tags(context.args)

        print(
            f"\nFound {len(articles)} articles with {context.args} tags in the data base!\n"
        )

        if len(articles) == 0:
            message = f"No articles found with{context.args} found!"

            await send_telegram_message_update(message, update)

            return

        for article in articles:
            message = (
                f"📰 Article Found!\n"
                f"📌 {article[1]}\n"
                f"🔗 {article[2]}\n"
                f"🤖 {article[4]}\n"
                f"🔍 Highlights: {article[3]}\n"
            )

            await send_telegram_message_update(message, update)

    # Handle `/help` command
    # pylint:disable=unused-argument
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /help command to provide information about the bot's commands.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        logger.info(" Requested: help")

        help_text = """
📢 <b>Crypto Bot Commands</>:
/start - Show buttons
/search <b>tags</b> - Search articles with tags
/help - Show this help message

Example:
/search BTC Crypto
        """
        await send_telegram_message_update(help_text, update)

    # Main function to start the bot
    def run_bot(self):
        """
        Initializes the bot and starts polling for updates.
        """
        variables = sdk.load_variables_handler.load("ConfigurationFiles/variables.json")

        bot_token = variables.get("TELEGRAM_API_TOKEN_ARTICLES", "")

        app = Application.builder().token(bot_token).build()

        # Add command and message handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_buttons)
        )

        # Start the bot
        print("🤖 News Bot is running...")
        app.run_polling()


if __name__ == "__main__":
    news_bot = NewsBot()

    news_bot.run_bot()
