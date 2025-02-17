from telegram import Bot
from datetime import datetime

import logging

logger = logging.getLogger("SendTelegramMessage.py")

logging.basicConfig(filename='../log.log', level=logging.INFO)
logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Started!')

# Function to send a message via Telegram
async def send_telegram_message(message, bot, telegram_important_chat_id, telegram_not_important_chat_id, is_important=False):
    bot = Bot(token=bot)

    if is_important is False:
        for chat_id in telegram_not_important_chat_id:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Sent to Telegram (Chat ID): {chat_id}")
            print(f"Sent to Telegram (Chat ID): {chat_id}: {message}")
    for chat_id in telegram_important_chat_id:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Sent to Telegram (Chat ID) {chat_id}")
        print(f"Sent to Telegram (Chat ID) {chat_id}: {message}")