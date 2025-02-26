from datetime import datetime

import logging

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('bot.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

from NewsCheck import CryptoNewsCheck
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk.DataBase.DataBaseHandler import DataBaseHandler
from sdk.CheckUsers import check_if_special_user
from sdk import LoadVariables as load_variables

cryptoNewsCheck = CryptoNewsCheck()

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Check for Articles", "🔢 Show statistics"]
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

async def start_the_articles_check():
    logging.info(f" Requested: Article Check")

    cryptoNewsCheck.reload_the_data()

    await cryptoNewsCheck.run()

async def start_all_articles(user_id, webpage):
    logging.info(f" Requested: All Articles from {webpage}")

    cryptoNewsCheck.reload_the_data()

    special_user = check_if_special_user(user_id)

    await cryptoNewsCheck.reload_the_news(webpage, user_id, special_user)

    return special_user

# Handle button presses
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🚨 Check for Articles":
        await update.message.reply_text("🚨 Check for articles...")

        await start_the_articles_check()
    elif text == "🔢 Show statistics":
        await update.message.reply_text("🔢 Showing the statistics...")

        db = DataBaseHandler()

        await db.show_stats(update)
    else:
        logging.error(f" Invalid command. Please use the buttons below.")
        await update.message.reply_text("❌ Invalid command. Please use the buttons below.")

# Main function to start the bot
def run_bot():
    variables = load_variables.load("ConfigurationFiles/variables.json")

    bot_token = variables.get('TELEGRAM_API_TOKEN_ARTICLES', '')

    app = Application.builder().token(bot_token).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # Start the bot
    print("🤖 News Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()