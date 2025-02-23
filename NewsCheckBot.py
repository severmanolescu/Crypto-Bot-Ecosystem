from datetime import datetime

import logging

logger = logging.getLogger("NewsCheckBot.py")

logging.basicConfig(filename='./bot.log', level=logging.INFO)
logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Started!')

from NewsCheck import CryptoNewsCheck
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk.CheckUsers import check_if_special_user
from sdk import LoadVariables as load_variables

cryptoNewsCheck = CryptoNewsCheck()

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Check for Articles", "🔍 All Articles crypto.news"],
        ["🔍 All Articles CoinTelegraph", "🔍 All Articles Bitcoin Magazine"]
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
    logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Requested: Article Check")

    cryptoNewsCheck.reload_the_data()

    await cryptoNewsCheck.run()

async def start_all_articles(user_id, webpage):
    logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Requested: All Articles from {webpage}")

    cryptoNewsCheck.reload_the_data()

    special_user = check_if_special_user(user_id)

    await cryptoNewsCheck.reload_the_news(webpage, user_id, special_user)

    return special_user

# Handle button presses
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    special_user = True

    if text == "🚨 Check for Articles":
        await update.message.reply_text("🚨 Check for articles...")

        await start_the_articles_check()
    elif text == "🔍 All Articles crypto.news":
        await update.message.reply_text("🔍 Showing all the articles from crypto.news...")

        special_user = await start_all_articles(update.effective_chat.id, "crypto.news")
    elif text == "🔍 All Articles CoinTelegraph":
        await update.message.reply_text("🔍 Showing all the articles from CoinTelegraph...")

        special_user = await start_all_articles(update.effective_chat.id, "cointelegraph")
    elif text == "🔍 All Articles Bitcoin Magazine":
        await update.message.reply_text("🔍 Showing all the articles from Bitcoin Magazine...")

        special_user = await start_all_articles(update.effective_chat.id, "bitcoinmagazine")
    else:
        logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Invalid command. Please use the buttons below.")
        special_user = await update.message.reply_text("❌ Invalid command. Please use the buttons below.")

    if special_user is False:
        await update.message.reply_text("You don't have the needed rights, news sent without the AI summary!")

        print(f"User {update.effective_chat.id} wants to "
                    f"redo the articles for one of the pages, not special user send without the AI summary!")

        logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: User {update.effective_chat.id} wants to "
                    f"redo the articles for one of the pages, not special user send without the AI summary!")

    else:
        await update.message.reply_text("You have the needed rights, news sent with the AI summary!")

        print(f"User {update.effective_chat.id} wants to "
              f"redo the articles for one of the pages, special user send with the AI summary!")

        logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: User {update.effective_chat.id} wants to "
                    f"redo the articles for one of the pages, special user send with the AI summary!")


# Main function to start the bot
def run_bot():
    variables = load_variables.load("ConfigurationFiles/variables.json")

    BOT_TOKEN = variables.get('TELEGRAM_API_TOKEN_ARTICLES', '')

    app = Application.builder().token(BOT_TOKEN).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # Start the bot
    print("🤖 News Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()