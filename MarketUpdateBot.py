import logging

from datetime import datetime

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('bot.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk import LoadVariables as load_variables

from sdk.CheckUsers import check_if_special_user

from CryptoValue import CryptoValueBot

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🕒 Market Update", "⛽ ETH Gas Fees"],
        ["📊 Portfolio Value Update", "📊 Crypto Fear & Greed Index"]
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)

cryptoValueBot = CryptoValueBot()

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Welcome to the Market Update! Use the buttons below to get started:",
        reply_markup=NEWS_KEYBOARD,
    )

async def market_update():
    logging.info(f" Requested: Market Update")

    cryptoValueBot.reload_the_data()

    cryptoValueBot.get_my_crypto()

    await cryptoValueBot.send_market_update(datetime.now())

async def eth_gas():
    logging.info(f" Requested: ETH Gas")

    cryptoValueBot.reload_the_data()

    await cryptoValueBot.send_eth_gas_fee()

async def portfolio_value():
    logging.info(f" Requested: Portfolio Value")

    cryptoValueBot.reload_the_data()

    cryptoValueBot.get_my_crypto()

    await cryptoValueBot.send_portfolio_update()

async def crypto_fear_and_greed():
    logging.info(f" Requested: Fear and Greed")

    cryptoValueBot.reload_the_data()

    await cryptoValueBot.show_fear_and_greed()

# Handle button presses
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🕒 Market Update":
        await update.message.reply_text("🕒 Showing Market Update...")

        await market_update()
    elif text == "⛽ ETH Gas Fees":
        await update.message.reply_text("⛽ Showing ETH Gas Fees...")

        await eth_gas()
    elif text == "📊 Portfolio Value Update":
        user_id = update.effective_chat.id

        if check_if_special_user(user_id):
            await update.message.reply_text("📊 Calculating Portfolio Value...")

            await portfolio_value()
        else:
            logging.info(f" User {user_id} wants to check the portfolio without rights!")
            await update.message.reply_text("You don't have the rights for this action!")
    elif text == "📊 Crypto Fear & Greed Index":
        await update.message.reply_text("📊 Showing Crypto Fear & Greed Index...")

        await crypto_fear_and_greed()
    else:
        logging.error(f" Invalid command. Please use the buttons below.")
        await update.message.reply_text("❌ Invalid command. Please use the buttons below.")

# Main function to start the bot
def run_bot():
    variables = load_variables.load("ConfigurationFiles/variables.json")

    bot_token = variables.get('TELEGRAM_API_TOKEN_VALUE', '')

    app = Application.builder().token(bot_token).build()

    # Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # Start the bot
    print("🤖 Market Update Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()