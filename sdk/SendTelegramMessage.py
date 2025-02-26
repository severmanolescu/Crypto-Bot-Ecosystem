from telegram import Bot
from datetime import datetime

import logging

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('log.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

# Function to send a message via Telegram
async def send_telegram_message(message, bot, telegram_important_chat_id, telegram_not_important_chat_id, is_important=False):
    bot = Bot(token=bot)

    if message.count("*") % 2 == 1:
        message = message.replace("*", "\*")

    print(f"\nSent to Telegram: {message}")
    print(f"To {len(telegram_important_chat_id)} important users!")
    print(f"To {len(telegram_not_important_chat_id)} not important users!")

    try:
        if is_important is False:
            for chat_id in telegram_not_important_chat_id:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        for chat_id in telegram_important_chat_id:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        error_message = f" Error sending message: {e}"
        logging.error(error_message)
        print(error_message)

async def send_telegram_message_update(message, update):
    print(f"\nSent to Telegram: {message}")

    await update.message.reply_text(message)

