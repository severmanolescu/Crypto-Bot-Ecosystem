from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("Crypto price Alerts bot started")

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk import LoadVariables as LoadVariables

from CryptoValue import CryptoValueBot

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Check for Alerts"]
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)

class PriceAlertBot:
    # Command: /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 Welcome to the Alert Bot! Use the buttons below to get started:",
            reply_markup=NEWS_KEYBOARD,
        )

    cryptoValueBot = CryptoValueBot()

    async def start_the_alerts_check(self, update = None):
        self.cryptoValueBot.reload_the_data()

        self.cryptoValueBot.get_my_crypto()

        return await self.cryptoValueBot.check_for_major_updates(None, update)

    # Handle button presses
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        logger.info(f" Check for Alerts")

        if text == "🚨 Check for Alerts":
            await update.message.reply_text("🚨 Searching for new alerts...")

            alert_available = await self.start_the_alerts_check(update)

            if alert_available is False:
                await update.message.reply_text("😔 No major price movement")
        else:
            logger.error(f" Invalid command. Please use the buttons below.")
            await update.message.reply_text("❌ Invalid command. Please use the buttons below.")

    # Main function to start the bot
    def run_bot(self):
        variables = LoadVariables.load("ConfigurationFiles/variables.json")

        bot_token = variables.get('TELEGRAM_API_TOKEN_ALERTS', '')

        app = Application.builder().token(bot_token).build()

        # Add command and message handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_buttons))

        # Start the bot
        print("🤖 Alert Bot is running...")
        app.run_polling()

if __name__ == "__main__":
    price_alert_bot =  PriceAlertBot()

    price_alert_bot.run_bot()