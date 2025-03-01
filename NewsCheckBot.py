from NewsCheck import CryptoNewsCheck
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk.DataBase.DataBaseHandler import DataBaseHandler
from sdk import LoadVariables as LoadVariables

from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("News Check started")

cryptoNewsCheck = CryptoNewsCheck()

db = DataBaseHandler()

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Check for Articles", "🔢 Show statistics"],
        ["🚨 Help"]
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Welcome to the News Bot! Use the buttons below to get started:",
        reply_markup=NEWS_KEYBOARD,
    )

async def start_the_articles_check(update):
    logger.info(f" Requested: Article Check")

    cryptoNewsCheck.reload_the_data()

    await cryptoNewsCheck.run_from_bot(update)

# Handle button presses
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🚨 Check for Articles":
        await update.message.reply_text("🚨 Check for articles...")

        await start_the_articles_check(update)
    elif text == "🔢 Show statistics":
        await update.message.reply_text("🔢 Showing the statistics...")

        await db.show_stats(update)
    elif text == "🚨 Help" or text.lower() == "help":
        await help_command(update, context)
    else:
        logger.error(f" Invalid command. Please use the buttons below.")
        await update.message.reply_text("❌ Invalid command. Please use the buttons below.")

# Command: /start
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /search <tags>")
        return

    articles = await db.search_articles_by_tags(context.args)

    print(f"\nFound {len(articles)} articles with {context.args} tags in the data base!\n")

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
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
def run_bot():
    variables = LoadVariables.load("ConfigurationFiles/variables.json")

    bot_token = variables.get('TELEGRAM_API_TOKEN_ARTICLES', '')

    app = Application.builder().token(bot_token).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # Start the bot
    print("🤖 News Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()