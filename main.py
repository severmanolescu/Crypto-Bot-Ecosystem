from datetime import datetime

import logging

import asyncio

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('log.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

from CryptoValue import CryptoValueBot
from NewsCheck import CryptoNewsCheck

from sdk import LoadVariables as LoadVariables


cryptoValueBot = CryptoValueBot()
cryptoNewsCheck = CryptoNewsCheck()

def read_variables():
    global cryptoValueBot
    global cryptoNewsCheck

    cryptoValueBot.reload_the_data()

    cryptoNewsCheck.reload_the_data()

async def run():
    while True:
        global cryptoValueBot
        global cryptoNewsCheck

        read_variables()

        sleep_time = LoadVariables.get_int_variable("SLEEP_DURATION")

        print("\n🧐 Check for new articles!")
        # await cryptoNewsCheck.run()

        print("\n📤 Send crypto value!")
        await cryptoValueBot.fetch_data()

        now_date = datetime.now()

        logging.info(f" Ran at: {now_date.strftime('%H:%M')}")
        logging.info(f" Wait {sleep_time / 60:.2f} minutes")

        print(f"\n⌛Checked at: {now_date.strftime('%H:%M')}")
        print(f"⏳ Wait {sleep_time / 60:.2f} minutes!\n\n")
        await asyncio.sleep(sleep_time)

# Run the script
if __name__ == "__main__":
    asyncio.run(run())
