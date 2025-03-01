from telegram import Bot

from sdk import LoadVariables as LoadVariables
from sdk.OpenAIPrompt import OpenAIPrompt
from sdk.DataFetcher import get_eth_gas_fee
from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("Telegram message handler started")

def format_change(change):
    if change is None:
        return "N/A"
    if change < 0:
        return f"`🔴 {change:.2f}%`"  # Negative change in monospace
    else:
        return f"`🟢 +{change:.2f}%`"  # Positive change in monospace


async def send_telegram_message_update(message, update):
    print(f"\nSent to Telegram:\n {message}")

    await update.message.reply_text(message)

async def send_plot_to_telegram(image_path, update):
    """ Send the generated plot image to a Telegram chat asynchronously. """
    if update is not None:
        with open(image_path, "rb") as img:
            await update.message.reply_photo(photo=img)

class TelegramMessagesHandler:
    def __init__(self):
        self.telegram_not_important_chat_id = None
        self.telegram_important_chat_id = None

        self.etherscan_api_url = None

        self.send_ai_summary = None
        self.open_ai_prompt = None

        self.reload_the_data()

    def reload_the_data(self):
        variables = LoadVariables.load()

        self.telegram_important_chat_id = variables.get("TELEGRAM_CHAT_ID_FULL_DETAILS", [])
        self.telegram_not_important_chat_id = variables.get("TELEGRAM_CHAT_ID_PARTIAL_DATA", [])

        # Etherscan API credentials
        self.etherscan_api_url = variables.get("ETHERSCAN_GAS_API_URL", "") + variables.get("ETHERSCAN_API_KEY", "")

        open_ai_api = variables.get('OPEN_AI_API', '')

        self.open_ai_prompt = OpenAIPrompt(open_ai_api)

        self.send_ai_summary = variables.get("SEND_AI_SUMMARY", "")

    # Function to send a message via Telegram
    async def send_telegram_message(self, message, bot, is_important=False, update=None):
        if update is not None:
            await send_telegram_message_update(message, update)

            return

        bot = Bot(token=bot)

        #if message.count("*") % 2 == 1:
        #    message = message.replace("*", "\*")

        print(f"\nSent to Telegram:\n {message}")
        print(f"To {len(self.telegram_important_chat_id)} important users!")
        print(f"To {len(self.telegram_not_important_chat_id)} not important users!")

        try:
            if is_important is False:
                for chat_id in self.telegram_not_important_chat_id:
                    await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            for chat_id in self.telegram_important_chat_id:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            error_message = f" Error sending message: {e}"
            logger.error(error_message)
            print(error_message)

    async def send_eth_gas_fee(self, telegram_api_token, update = None):
        message = ""
        safe_gas, propose_gas, fast_gas = get_eth_gas_fee(self.etherscan_api_url)
        if safe_gas and propose_gas and fast_gas:
            message += (
                f"⛽ *ETH Gas Fees (Gwei)*:\n"
                f"🐢 Safe: {safe_gas}\n"
                f"🚗 Propose: {propose_gas}\n"
                f"🚀 Fast: {fast_gas}\n\n"
            )
        await self.send_telegram_message(message, telegram_api_token, False, update)

    async def send_market_update(self, telegram_api_token, now_date, my_crypto, update = None):
        message = f"🕒 *Market Update at {now_date.strftime('%H:%M')}*"

        if self.send_ai_summary == "True":
            message += '\n\n'
            changes_text = "\n".join([f"{symbol}: {data['change_1h']}%" for symbol, data in my_crypto.items()])
            prompt = f"Generate a short quote about the crypto market. Hour: {now_date.hour}, changes:\n{changes_text}"

            message += await self.open_ai_prompt.get_response(prompt)
        message += f"\n\n"

        for symbol, data in my_crypto.items():
            message += (
                f"*{symbol}*\n"
                f"Price: $*{data['price']:.2f}*\n"
                f"1h: {format_change(data['change_1h'])}\n"
                f"24h: {format_change(data['change_24h'])}\n"
                f"7d: {format_change(data['change_7d'])}\n"
                f"30d: {format_change(data['change_30d'])}\n\n"
            )

        await self.send_telegram_message(message, telegram_api_token, False, update)
