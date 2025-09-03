import asyncio
import logging

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.handlers.crypto_price_alerts_main_loop import PriceAlertMainLoop
from src.handlers.crypto_rsi_handler import CryptoRSIHandler
from src.handlers.load_variables_handler import load_json
from src.handlers.save_data_handler import (
    save_variables_json,
)
from src.handlers.send_telegram_message import send_telegram_message_update

logger = logging.getLogger(__name__)
logger.info("Crypto Price Alerts Buttons started")

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📈 RSI", "📊 Value Check"],
        ["🚨 Help"],
    ],
    resize_keyboard=True,
)

RSI_MENU = ReplyKeyboardMarkup(
    [
        ["RSI 1H", "RSI 4H", "RSI 1D", "RSI 1W"],
        ["RSI all timeframes", "🔙 Back to Menu"],
    ],
    resize_keyboard=True,
)

VALUE_MENU = ReplyKeyboardMarkup(
    [
        ["Value 1H", "Value 1D", "Value 1W", "Value 1M"],
        ["Value all timeframes", "🔙 Back to Menu"],
    ],
    resize_keyboard=True,
)


class CryptoPriceAlertsButtons:
    """
    Class to handle the creation of Telegram reply keyboard buttons for crypto price alerts.
    """

    def __init__(self):
        """
        Initializes the CryptoPriceAlertsButtons with predefined menus.
        """
        self.crypto_value_bot = PriceAlertMainLoop()
        self.rsi_handler = CryptoRSIHandler()

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
            users_id = json_data.get("TELEGRAM_CHAT_ID_PRICE_ALERTS", [])
            if str(update.effective_user.id) in users_id:
                logger.info(
                    "User %s is already registered in the bot.",
                    update.effective_user.id,
                )
                await update.message.reply_text(
                    "🤖 Welcome to the Alert Bot! Use the buttons below to get started!",
                    reply_markup=MAIN_MENU,
                )
            else:
                logger.info(
                    "User %s is not registered in the bot. Adding to the list.",
                    update.effective_user.id,
                )

                users_id.append(str(update.effective_user.id))
                json_data["TELEGRAM_CHAT_ID_PRICE_ALERTS"] = users_id
                save_variables_json(json_data)

                await update.message.reply_text(
                    "🤖 Welcome to the Alert Bot! You have been registered successfully. Use the buttons below to get started!",
                    reply_markup=MAIN_MENU,
                )
        else:
            logger.info(
                "No users registered in the bot. Initializing with current user."
            )
            users_id = [str(update.effective_user.id)]
            json_data = {
                "TELEGRAM_CHAT_ID_PRICE_ALERTS": users_id,
            }
            save_variables_json(json_data)

            await update.message.reply_text(
                "🤖 Welcome to the Alert Bot! You have been registered successfully. Use the buttons below to get started!",
                reply_markup=MAIN_MENU,
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
            users_id = json_data.get("TELEGRAM_CHAT_ID_PRICE_ALERTS", [])
            if str(update.effective_user.id) in users_id:
                users_id.remove(str(update.effective_user.id))
                json_data["TELEGRAM_CHAT_ID_PRICE_ALERTS"] = users_id
                save_variables_json(json_data)
        else:
            logger.info("No users registered in the bot. Nothing to cancel.")
        await update.message.reply_text(
            "✅ You have been removed from the bot. You can start again with /start command.",
        )

    async def start_the_alerts_check_1h(self, update=None):
        """
        Start the alerts check for 1-hour timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        await update.message.reply_text("🚨 Searching for new alerts for 1h update...")

        self.crypto_value_bot.reload_the_data()

        alert_available = await self.crypto_value_bot.check_for_major_updates_1h(update)

        if not alert_available:
            await update.message.reply_text(
                "😔 No major price movement for 1h timeframe"
            )

    async def start_the_alerts_check_24h(self, update=None):
        """
        Start the alerts check for 24-hour timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        await update.message.reply_text("🔔 Searching for new alerts for 24h update...")

        self.crypto_value_bot.reload_the_data()

        alert_available = await self.crypto_value_bot.check_for_major_updates_24h(
            update
        )

        if not alert_available:
            await update.message.reply_text(
                "😔 No major price movement for 24h timeframe"
            )

    async def start_the_alerts_check_7d(self, update=None):
        """
        Start the alerts check for 7-day timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        await update.message.reply_text("⚠️ Searching for new alerts for 7d update...")
        self.crypto_value_bot.reload_the_data()

        alert_available = await self.crypto_value_bot.check_for_major_updates_7d(update)

        if not alert_available:
            await update.message.reply_text(
                "😔 No major price movement for 7d timeframe"
            )

    async def start_the_alerts_check_30d(self, update=None):
        """
        Start the alerts check for 30-day timeframe.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        await update.message.reply_text("📢 Searching for new alerts for 30d update...")

        self.crypto_value_bot.reload_the_data()

        alert_available = await self.crypto_value_bot.check_for_major_updates_30d(
            update
        )

        if not alert_available:
            await update.message.reply_text(
                "😔 No major price movement for 30d timeframe"
            )

    async def start_the_alerts_check_all_timeframes(self, update=None):
        """
        Start the alerts check for all timeframes.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if alerts are available, False otherwise.
        """
        await update.message.reply_text(
            "🌐 Searching for new alerts for all timeframes..."
        )

        self.crypto_value_bot.reload_the_data()

        alert_available = await self.crypto_value_bot.check_for_major_updates(update)

        if not alert_available:
            await update.message.reply_text(
                "😔 No major price movement for all timeframes"
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /help command to provide information about the bot's commands.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        logger.info(" Requested: help")

        help_text = """
<b>Crypto Price Alert Bot Commands</>:
/help - Show this help message
/start - Start the bot and register
/cancel - Cancel any ongoing operations and unregister
/alert_1h - Check for 1-hour price alerts
/alert_24h - Check for 24-hour price alerts
/alert_7d - Check for 7-day price alerts
/alert_30d - Check for 30-day price alerts
/alert_all - Check for all timeframes price alerts
/rsi_1h - Check RSI for the last hour
/rsi_4h - Check RSI for the last 4 hours
/rsi_1d - Check RSI for the last day
/rsi_1w - Check RSI for the last week
        """
        await send_telegram_message_update(help_text, update)

    def check_if_user_is_registered(self, update):
        """
        Check if the user is registered in the bot.
        Args:
            update: The update object from Telegram.
        Returns:
            bool: True if the user is registered, False otherwise.
        """
        json_data = load_json()
        if json_data:
            users_id = json_data.get("TELEGRAM_CHAT_ID_PRICE_ALERTS", [])
            return str(update.effective_user.id) in users_id
        return False

    async def alert_1h_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Command to check for 1-hour price alerts.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return
        await self.start_the_alerts_check_1h(update)

    async def alert_24h_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Command to check for 24-hour price alerts.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return
        await self.start_the_alerts_check_24h(update)

    async def alert_7d_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Command to check for 7-day price alerts.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return
        await self.start_the_alerts_check_7d(update)

    async def alert_30d_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Command to check for 30-day price alerts.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return
        await self.start_the_alerts_check_30d(update)

    async def alert_all_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Command to check for all timeframes price alerts.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return
        await self.start_the_alerts_check_all_timeframes(update)

    async def handle_alerts_buttons(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle the buttons for checking alerts based on user input.
        """
        text = update.message.text

        if text.lower() == "value 1h" or text.lower() == "alert1h":
            await self.start_the_alerts_check_1h(update)
        elif text.lower() == "value 1d" or text.lower() == "alert1d":
            await self.start_the_alerts_check_24h(update)
        elif text.lower() == "value 1w" or text.lower() == "alert1w":
            await self.start_the_alerts_check_7d(update)
        elif text.lower() == "value 1m" or text.lower() == "alert1m":
            await self.start_the_alerts_check_30d(update)

        elif text.lower() == "value all timeframes" or text.lower() == "alertall":
            await self.start_the_alerts_check_all_timeframes(update)
        else:
            logger.error(" Invalid command. Please use the buttons below.")
            await update.message.reply_text(
                "❌ Invalid command. Please use the buttons below."
            )

    async def rsi_check(self, timeframe, update):
        self.rsi_handler.reload_the_data()

        await update.message.reply_text("📊 Checking RSI for timeframe: " + timeframe)

        try:
            if timeframe == "all":
                # Send RSI data to Telegram
                logger.info("Starting to send RSI for all timeframes...")
                timeframes = ["1h", "4h", "1d", "1w"]

                for timeframe in timeframes:
                    await asyncio.wait_for(
                        self.rsi_handler.send_rsi_for_timeframe(
                            timeframe=timeframe, bot=None, update=update
                        ),
                        timeout=180,
                    )
            else:
                # Send RSI data to Telegram
                await asyncio.wait_for(
                    self.rsi_handler.send_rsi_for_timeframe(
                        timeframe=timeframe, bot=None, update=update
                    ),
                    timeout=180,  # 3 minutes timeout
                )
        except asyncio.TimeoutError:
            logger.error("Timeout occurred while sending RSI data.")
            await update.message.reply_text(
                "⏳ Timeout occurred while processing your request. Please try again."
            )
        except Exception as e:
            logger.error("An error occurred while sending RSI data: %s", e)
            await update.message.reply_text(
                "❌ An error occurred while processing your request. Please try again."
            )

    async def rsi_1h_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Command to check RSI for the last hour.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return

        await self.rsi_check("1h", update)

    async def rsi_4h_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Command to check RSI for the last 4 hours.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return

        await self.rsi_check("4h", update)

    async def rsi_1d_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Command to check RSI for the last day.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return

        await self.rsi_check("1d", update)

    async def rsi_1w_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Command to check RSI for the last week.
        """
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return

        await self.rsi_check("1w", update)

    async def handle_rsi_buttons(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Handle the buttons for checking RSI based on user input.
        """
        text = update.message.text

        if text.lower() == "rsi 1h" or text == "1h":
            await self.rsi_check("1h", update)
            return

        elif text.lower() == "rsi 4h" or text == "4h":

            await self.rsi_check("4h", update)
            return

        elif text.lower() == "rsi 1d" or text == "1d":

            await self.rsi_check("1d", update)
            return

        elif text.lower() == "rsi 1w" or text == "1w":

            await self.rsi_check("1w", update)
            return

        elif text == " rsi all timeframes" or text.lower() == "all":

            await update.message.reply_text("📊 Checking RSI for all timeframes...")

            await self.rsi_check("all", update)
            return

        logger.error(" Invalid timeframe specified.")
        await update.message.reply_text(
            "❌ Invalid timeframe specified. Please use the buttons below."
        )

    # Handle button presses
    # pylint:disable=unused-argument
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle button presses for checking alerts.
        Args:
            update: The update object from Telegram.
            context: The context object from Telegram.
        """
        logger.info("Handling button press: %s", update.message.text)
        if not self.check_if_user_is_registered(update):
            logger.error(
                "User %s is not registered in the bot. Please use /start command.",
                update.effective_user.id,
            )
            await update.message.reply_text(
                "❌ You are not registered in the bot. Please use /start command."
            )
            return

        text = update.message.text

        if text == "📈 RSI":
            await update.message.reply_text(
                "Choose RSI timeframe:", reply_markup=RSI_MENU
            )
            return

        if text == "📊 Value Check":
            await update.message.reply_text(
                "Choose Value timeframe:", reply_markup=VALUE_MENU
            )
            return

        if text == "🔙 Back to Menu":
            await update.message.reply_text(
                "Back to main menu.", reply_markup=MAIN_MENU
            )
            return

        logger.info(" Check for Alerts")

        if "value" in text.lower():
            await self.handle_alerts_buttons(update, context)
        elif "rsi" in text.lower():
            await self.handle_rsi_buttons(update, context)
        elif "help" in text.lower():
            await self.help_command(update, context)
        else:
            logger.error("Invalid command. Please use the buttons below.")
            await update.message.reply_text(
                "❌ Invalid command. Please use the buttons below."
            )
