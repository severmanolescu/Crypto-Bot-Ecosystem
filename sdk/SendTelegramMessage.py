from telegram import Bot
from datetime import datetime

import logging

logger = logging.getLogger("SendTelegramMessage.py")

logging.basicConfig(filename='./log.log', level=logging.INFO)
logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Started!')

# Function to send a message via Telegram
async def send_telegram_message(message, bot, telegram_important_chat_id, telegram_not_important_chat_id, is_important=False):
    bot = Bot(token=bot)

    if message.count("*") % 2 == 1:
        message = message.replace("*", "\*")

    logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:Sent to Telegram: {message}")
    print(f"\n\nSent to Telegram: {message}")

    try:
        if is_important is False:
            for chat_id in telegram_not_important_chat_id:
                await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
                logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:Sent to (Chat ID): {chat_id}")
                print(f"Sent to (Chat ID): {chat_id}")
        for chat_id in telegram_important_chat_id:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:Sent to (Chat ID): {chat_id}")
            print(f"Sent to (Chat ID): {chat_id}")
    except Exception as e:
        error_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error sending message: {e}"
        logger.error(error_message)
        print(error_message)

