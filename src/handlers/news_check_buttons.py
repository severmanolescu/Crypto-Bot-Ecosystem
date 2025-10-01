import logging

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.data_base.data_base_handler import DataBaseHandler
from src.handlers.load_variables_handler import load_json
from src.handlers.market_sentiment_handler import get_market_sentiment
from src.handlers.news_check_handler import CryptoNewsCheck
from src.handlers.save_data_handler import save_variables_json
from src.handlers.send_telegram_message import TelegramMessagesHandler

logger = logging.getLogger(__name__)
logger.info("News Check started")

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🔢 Show statistics", "📊 Market Sentiment"],
        ["🚨 Help"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


class NewsCheckButtons:
    def __init__(self):
        """
        Initializes the NewsCheckButtons with necessary components.
        """
        self.crypto_news_check = CryptoNewsCheck()

        self.db = DataBaseHandler()

        self.message_handler = TelegramMessagesHandler()

    # Command: /start
    # pylint:disable=unused-argument
    async def start(self, update, context: ContextTypes.DEFAULT_TYPE):
        """
        Start command handler for the bot.
        Args:
            update: The update object from Telegram.
            context: The context object from Telegram.
        """
        json_data = load_json()

        if json_data:
            users_id = json_data.get("TELEGRAM_CHAT_ID_NEWS_CHECK", [])
            if str(update.effective_user.id) in users_id:
                logger.info(
                    "User %s is already registered in the bot.",
                    update.effective_user.id,
                )
                await update.message.reply_text(
                    "🤖 Welcome to the Alert Bot! Use the buttons below to get started!",
                    reply_markup=NEWS_KEYBOARD,
                )
            else:
                logger.info(
                    "User %s is not registered in the bot. Adding to the list.",
                    update.effective_user.id,
                )

                users_id.append(str(update.effective_user.id))
                json_data["TELEGRAM_CHAT_ID_NEWS_CHECK"] = users_id
                save_variables_json(json_data)

                await update.message.reply_text(
                    "🤖 Welcome to the Alert Bot! You have been registered successfully. Use the buttons below to get started!",
                    reply_markup=NEWS_KEYBOARD,
                )
        else:
            logger.info(
                "No users registered in the bot. Initializing with current user."
            )
            users_id = [str(update.effective_user.id)]
            json_data = {
                "TELEGRAM_CHAT_ID_NEWS_CHECK": users_id,
            }
            save_variables_json(json_data)

            await update.message.reply_text(
                "🤖 Welcome to the News Bot! You have been registered successfully. Use the buttons below to get started!",
                reply_markup=NEWS_KEYBOARD,
            )

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /cancel command to stop any ongoing operations.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        logger.info("Requested: cancel")

        json_data = load_json()
        if json_data:
            users_id = json_data.get("TELEGRAM_CHAT_ID_NEWS_CHECK", [])
            if str(update.effective_user.id) in users_id:
                users_id.remove(str(update.effective_user.id))
                json_data["TELEGRAM_CHAT_ID_NEWS_CHECK"] = users_id
                save_variables_json(json_data)
        else:
            logger.info("No users registered in the bot. Nothing to cancel.")
        await update.message.reply_text(
            "✅ You have been removed from the bot. You can start again with /start command.",
        )

    async def market_sentiment_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handles the market sentiment command to calculate and send market sentiment.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        message = await get_market_sentiment()

        self.message_handler.reload_the_data()

        await self.message_handler.send_telegram_message_news_check(
            message, None, update
        )

    async def market_sentiment_loop(self, bot_token):
        """
        Periodically calculates and sends market sentiment.
        This function is intended to be run in a loop.
        """
        while True:
            logger.info("Calculating market sentiment...")
            message = await get_market_sentiment()

            self.message_handler.reload_the_data()

            await self.message_handler.send_telegram_message_news_check(
                message, bot_token
            )

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

        if text == "🔢 Show statistics" or text_lower == "statistics":
            await self.message_handler.send_telegram_message_news_check(
                "🔢 Showing the statistics...", None, update
            )

            await self.db.show_stats(update)
        elif text == "📊 Market Sentiment" or text_lower == "sentiment":
            await self.message_handler.send_telegram_message_news_check(
                "🧮 Calculating the sentiment...", None, update
            )
            await self.market_sentiment_command(update, None)
        elif text == "🚨 Help" or text.lower() == "help":
            await self.help_command(update, context)
        else:
            logger.error(" Invalid command. Please use the buttons below.")
            await self.message_handler.send_telegram_message_news_check(
                "❌ Invalid command. Please use the buttons below.", None, update
            )

    # Command: /start
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /search command to search for articles by tags.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if len(context.args) < 1:
            await self.message_handler.send_telegram_message_news_check(
                "❌ Usage: /search <b>tags</b>", None, update
            )
            return

        articles = await self.db.search_articles_by_tags(context.args)

        print(
            f"\nFound {len(articles)} articles with {context.args} tags in the data base!\n"
        )

        if len(articles) == 0:
            message = f"No articles found with {context.args} found!"

            await self.message_handler.send_telegram_message_news_check(
                message, None, update
            )

            return

        for article in articles:
            if article[4] is None:
                message = (
                    f"📰 Article Found!\n"
                    f"📌 {article[1]}\n"
                    f"🔗 {article[2]}\n"
                    f"🔍 Highlights: {article[3]}\n"
                )
            else:
                message = (
                    f"📰 Article Found!\n"
                    f"📌 {article[1]}\n"
                    f"🔗 {article[2]}\n"
                    f"🧠 Summary: {article[4]}\n"
                    f"🔍 Highlights: {article[3]}\n"
                )

            await self.message_handler.send_telegram_message_news_check(
                message, None, update
            )

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
📢 <b>News Check Bot Commands</>:
/help - Show this help message
/start - Start the bot and register
/cancel - Cancel any ongoing operations and unregister
/search <b>tags</b> - Search last 10 articles with the specified tags
/sentiment - Get market sentiment analysis

Example:
/search BTC Crypto
        """
        await self.message_handler.send_telegram_message_news_check(
            help_text, None, update
        )
