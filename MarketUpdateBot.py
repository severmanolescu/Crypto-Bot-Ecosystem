from datetime import datetime

from sdk.SendTelegramMessage import TelegramMessagesHandler

from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("Market Update Bot started")

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk import LoadVariables as LoadVariables

from sdk.PlotCryptoTrades import PlotTrades
from sdk.CheckUsers import check_if_special_user
from CryptoValue import CryptoValueBot

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🕒 Market Update", "⛽ ETH Gas Fees"],
        ["📊 Detailed Portfolio Update", "📊 Crypto Fear & Greed Index"],
        ["📈 Show plots for the entire portfolio", "🚨 Help"]
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)

class MarketUpdateBot:
    def __init__(self):
        self.cryptoValueBot = CryptoValueBot()

        self.telegram_message = TelegramMessagesHandler()

        self.plot_trades = PlotTrades()

        self.telegram_api_token = None

    def reload_the_data(self):
        variables = LoadVariables.load()

        self.telegram_api_token = variables.get("TELEGRAM_API_TOKEN_VALUE", "")

        self.cryptoValueBot.reload_the_data()

        self.telegram_message.reload_the_data()

        self.plot_trades.reload_the_data()

    # Command: /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 Welcome to the Market Update! Use the buttons below to get started:",
            reply_markup=NEWS_KEYBOARD,
        )

    async def send_market_update(self, update):
        logger.info(f" Requested: Market Update")

        self.cryptoValueBot.reload_the_data()

        self.cryptoValueBot.get_my_crypto()

        await self.cryptoValueBot.send_market_update(datetime.now(), update)

    async def send_eth_gas(self, update):
        logger.info(f" Requested: ETH Gas")

        self.cryptoValueBot.reload_the_data()

        await self.cryptoValueBot.send_eth_gas_fee(update)

    async def send_portfolio_value(self, update):
        logger.info(f" Requested: Portfolio Value")

        self.cryptoValueBot.reload_the_data()

        self.cryptoValueBot.get_my_crypto()

        await self.cryptoValueBot.send_portfolio_update(update, True)

    async def send_crypto_fear_and_greed(self, update):
        logger.info(f" Requested: Fear and Greed")

        self.cryptoValueBot.reload_the_data()

        await self.cryptoValueBot.show_fear_and_greed(update)

    async def send_crypto_plots(self, update):
        self.plot_trades.reload_the_data()

        await self.plot_trades.send_all_plots(update)

    async def send_crypto_plot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.plot_trades.reload_the_data()

        if not context.args:
            logger.error(f" Usage: /plot <symbol>")
            await update.message.reply_text("❌ Usage: /plot <symbol>")
            return

        action = context.args[0].lower()

        await self.plot_trades.plot_crypto_trades(action, update)

    # Handle `/help` command
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f" Requested: help")

        help_text = """
📢 *Crypto Bot Commands*:
/start - Show buttons
/plot <symbol> - Show the plot for the wanted symbol
/help - Show this help message
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")

    # Handle button presses
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        if text == "🕒 Market Update":
            await update.message.reply_text("🕒 Showing Market Update...")

            await self.send_market_update(update)
        elif text == "⛽ ETH Gas Fees":
            await update.message.reply_text("⛽ Showing ETH Gas Fees...")

            await self.send_eth_gas(update)
        elif text == "📊 Detailed Portfolio Update":
            user_id = update.effective_chat.id

            if check_if_special_user(user_id):
                await update.message.reply_text("📊 Calculating Portfolio Value...")

                await self.send_portfolio_value(update)
            else:
                logger.info(f" User {user_id} wants to check the portfolio without rights!")
                await update.message.reply_text("You don't have the rights for this action!")
        elif text == "📊 Crypto Fear & Greed Index":
            await update.message.reply_text("📊 Showing Crypto Fear & Greed Index...")

            await self.send_crypto_fear_and_greed(update)
        elif text == "📈 Show plots for the entire portfolio":
            await self.send_crypto_plots(update)
        elif text == "🚨 Help":
            await self.help_command(update, context)
        else:
            logger.error(f" Invalid command. Please use the buttons below.")
            await update.message.reply_text("❌ Invalid command. Please use the buttons below.")

    # Main function to start the bot
    def run_bot(self):
        variables = LoadVariables.load("ConfigurationFiles/variables.json")

        bot_token = variables.get('TELEGRAM_API_TOKEN_VALUE', '')

        app = Application.builder().token(bot_token).build()

        # Add command and message handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("plot", self.send_crypto_plot))

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_buttons))

        # Start the bot
        print("🤖 Market Update Bot is running...")
        app.run_polling()

# Run the bot
if __name__ == "__main__":
    updateBot = MarketUpdateBot()

    updateBot.run_bot()
