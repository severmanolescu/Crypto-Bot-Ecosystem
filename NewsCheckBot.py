from NewsCheck import CryptoNewsCheck
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk.DataBase.DataBaseHandler import DataBaseHandler
from sdk.MarketSentiment import get_market_sentiment
from sdk import LoadVariables as LoadVariables

from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("News Check started")

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Check for Articles", "🔢 Show statistics"],
        ["📊 Market Sentiment", "🚨 Help"]
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)

class NewsBot:
    def __init__(self):

        self.cryptoNewsCheck = CryptoNewsCheck()

        self.db = DataBaseHandler()

    # Command: /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 Welcome to the News Bot! Use the buttons below to get started:",
            reply_markup=NEWS_KEYBOARD,
        )

    async def start_the_articles_check(self,update):
        logger.info(f" Requested: Article Check")

        self.cryptoNewsCheck.reload_the_data()

        await self.cryptoNewsCheck.run_from_bot(update)

    async def market_sentiment(self, update):
        message = await get_market_sentiment()

        await update.message.reply_text(message)

    # Handle button presses
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        text_lower = text.lower()

        if text == "🚨 Check for Articles" or text_lower == "check":
            await update.message.reply_text("🚨 Check for articles...")

            await self.start_the_articles_check(update)
        elif text == "🔢 Show statistics" or text_lower == "statistics":
            await update.message.reply_text("🔢 Showing the statistics...")

            await self.db.show_stats(update)
        elif text == "📊 Market Sentiment" or text_lower == "sentiment":
            await update.message.reply_text("🧮 Calculating the sentiment...")

            await self.market_sentiment(update)
        elif text == "🚨 Help" or text.lower() == "help":
            await self.help_command(update, context)
        else:
            logger.error(f" Invalid command. Please use the buttons below.")
            await update.message.reply_text("❌ Invalid command. Please use the buttons below.")

    # Command: /start
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Usage: /search <tags>")
            return

        articles = await self.db.search_articles_by_tags(context.args)

        print(f"\nFound {len(articles)} articles with {context.args} tags in the data base!\n")

        if len(articles) == 0:
            message = f"No articles found with{context.args} found!"

            await update.message.reply_text(message)

            return

        for article in articles:
            message = (
                f"📰 Article Found!\n"
                f"📌 {article[1]}\n"
                f"🔗 {article[2]}\n"
                f"🤖 {article[4]}\n"
                f"🔍 Highlights: {article[3]}\n"
            )

            await update.message.reply_text(message)

    # Handle `/help` command
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f" Requested: help")

        help_text = """
📢 *Crypto Bot Commands*:
/start - Show buttons
/search <tags> - Search articles with tags
/help - Show this help message

Example:
/search BTC Crypto
        """
        await update.message.reply_text(help_text, parse_mode="Markdown")

    # Main function to start the bot
    def run_bot(self):
        variables = LoadVariables.load("ConfigurationFiles/variables.json")

        bot_token = variables.get('TELEGRAM_API_TOKEN_ARTICLES', '')

        app = Application.builder().token(bot_token).build()

        # Add command and message handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_buttons))

        # Start the bot
        print("🤖 News Bot is running...")
        app.run_polling()

if __name__ == "__main__":
    news_bot = NewsBot()

    news_bot.run_bot()