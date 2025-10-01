"""
Send messages to Telegram using the Telegram Bot API.
"""

import logging

from telegram import Bot

from src.handlers.data_fetcher_handler import get_eth_gas_fee
from src.handlers.load_variables_handler import load_json
from src.utils.utils import format_change

logger = logging.getLogger(__name__)
logger.info("Telegram message handler started")


async def send_telegram_message_update(message, update):
    """
    Send a message to a Telegram chat using the update object.
    Args:
        message (str): The message to send.
        update (Update): The update object containing the message context.
    """
    print(f"\nSent to Telegram:\n {message}")

    await update.message.reply_text(message, parse_mode="HTML")


async def send_plot_to_telegram(image_path, update):
    """
    Send the generated plot image to a Telegram chat asynchronously.
    Args:
        image_path (str): The path to the image file to send.
        update (Update): The update object containing the message context.
    """
    if update is not None:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img)


class TelegramMessagesHandler:
    """
    TelegramMessagesHandler class to manage sending messages via Telegram.
    """

    def __init__(self):
        """
        Initializes the TelegramMessagesHandler with necessary variables.
        """
        self.telegram_not_important_chat_id = None
        self.telegram_important_chat_id = None

        self.telegram_price_alerts_chat_id = None
        self.telegram_news_check_chat_id = None

        self.etherscan_api_url = None

        self.reload_the_data()

    def reload_the_data(self):
        """
        Reload the data from the configuration file and update the Telegram chat IDs
        and Etherscan API URL.
        """
        variables = load_json()

        self.telegram_important_chat_id = variables.get(
            "TELEGRAM_CHAT_ID_FULL_DETAILS", []
        )
        self.telegram_not_important_chat_id = variables.get(
            "TELEGRAM_CHAT_ID_PARTIAL_DATA", []
        )

        self.telegram_price_alerts_chat_id = variables.get(
            "TELEGRAM_CHAT_ID_PRICE_ALERTS", []
        )

        self.telegram_news_check_chat_id = variables.get(
            "TELEGRAM_CHAT_ID_NEWS_CHECK", []
        )

        # Etherscan API credentials
        self.etherscan_api_url = variables.get(
            "ETHERSCAN_GAS_API_URL", ""
        ) + variables.get("ETHERSCAN_API_KEY", "")

    # Function to send a message via Telegram
    async def send_telegram_message(
        self, message, bot_token, is_important=False, update=None
    ):
        """
        Send a message to Telegram using the Bot API.
        Args:
            message (str): The message to send.
            bot_token (str): The Telegram bot token.
            is_important (bool): Flag to indicate if the message is important.
            update (Update, optional): The update object containing the message context.
        """
        if update is not None:
            await send_telegram_message_update(message, update)

            return

        bot = Bot(token=bot_token)

        print(f"\n\nSent to Telegram:\n")
        print(f"To {len(self.telegram_important_chat_id)} important users!")
        print(f"To {len(self.telegram_not_important_chat_id)} not important users!")

        try:
            if not is_important:
                for chat_id in self.telegram_not_important_chat_id:
                    await bot.send_message(
                        chat_id=chat_id, text=message, parse_mode="HTML"
                    )
            for chat_id in self.telegram_important_chat_id:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        # pylint:disable=broad-exception-caught
        except Exception as e:
            error_message = f" Error sending message: {e}"
            logger.error(error_message)
            print(error_message)

    async def send_telegram_message_price_alerts(self, message, bot_token, update=None):
        """
        Send a price alert message to Telegram.
        Args:
            message (str): The message to send.
            bot_token (str): The Telegram bot token.
            update (Update, optional): The update object containing the message context.
        """
        if update is not None:
            await send_telegram_message_update(message, update)
            return

        bot = Bot(token=bot_token)

        print(f"\n\nSent to Telegram:\n")
        print(f"To {len(self.telegram_price_alerts_chat_id)} users!")

        try:
            for chat_id in self.telegram_price_alerts_chat_id:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        # pylint:disable=broad-exception-caught
        except Exception as e:
            error_message = f" Error sending price alert message: {e}"
            logger.error(error_message)
            print(error_message)

    async def send_telegram_message_news_check(self, message, bot_token, update=None):
        """
        Send a news check message to Telegram.
        Args:
            message (str): The message to send.
            bot_token (str): The Telegram bot token.
            update (Update, optional): The update object containing the message context.
        """
        if update is not None:
            await send_telegram_message_update(message, update)
            return

        bot = Bot(token=bot_token)

        print(f"\n\nSent to Telegram:\n")
        print(f"To {len(self.telegram_news_check_chat_id)} users!")

        try:
            for chat_id in self.telegram_news_check_chat_id:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        # pylint:disable=broad-exception-caught
        except Exception as e:
            error_message = f" Error sending news check message: {e}"
            logger.error(error_message)
            print(error_message)

    async def send_eth_gas_fee(self, telegram_api_token, update=None):
        """
        Fetch and send the current Ethereum gas fees to Telegram.
        Args:
            telegram_api_token (str): The Telegram bot token.
            update (Update, optional): The update object containing the message context.
        """
        message = ""
        safe_gas, propose_gas, fast_gas = get_eth_gas_fee(self.etherscan_api_url)
        if safe_gas and propose_gas and fast_gas:
            message += (
                f"⛽ <b>ETH Gas Fees (Gwei)</b>:\n"
                f"🐢 Safe: {safe_gas}\n"
                f"🚗 Propose: {propose_gas}\n"
                f"🚀 Fast: {fast_gas}\n\n"
                f"#GasFee"
            )
        await self.send_telegram_message(message, telegram_api_token, False, update)

    async def send_market_update(
        self, telegram_api_token, now_date, my_crypto, update=None
    ):
        """
        Send a market update message to Telegram with current cryptocurrency prices and changes.
        Args:
            telegram_api_token (str): The Telegram bot token.
            now_date (datetime): The current date and time for the update.
            my_crypto (dict): A dictionary containing cryptocurrency data.
            update (Update, optional): The update object containing the message context.
        """
        message = f"🕒 <b>Market Update at {now_date.strftime('%H:%M')}</b>"

        for symbol, data in my_crypto.items():
            message += (
                f"\n<b>{symbol}</b>\n"
                f"Price: $<b>{data['price']:.2f}</b>\n"
                f"1h: {format_change(data['change_1h'])}\n"
                f"24h: {format_change(data['change_24h'])}\n"
                f"7d: {format_change(data['change_7d'])}\n"
                f"30d: {format_change(data['change_30d'])}\n"
            )

        message += "#MarketUpdate\n\n"

        await self.send_telegram_message(message, telegram_api_token, False, update)
