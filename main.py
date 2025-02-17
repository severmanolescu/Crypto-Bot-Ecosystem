from datetime import datetime

import logging

import asyncio

logger = logging.getLogger("main.py")

logging.basicConfig(filename='log.log', level=logging.INFO)
logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Started!')

from CryptoValue import CryptoValueBot
from NewsCheck import CryptoNewsCheck

from sdk import LoadVariables as load_variables


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

        sleepTime = load_variables.get_int_variable("SLEEP_DURATION")

        print("\n🧐 Check for new articles!")
        await cryptoNewsCheck.run()

        print("\n📤 Send crypto value!")
        await cryptoValueBot.FetchData()

        nowDate = datetime.now()

        logger.info(f" Ran at: {nowDate.strftime('%H:%M')}")
        logger.info(f" Wait {sleepTime / 60:.2f} minutes")

        print(f"\n ⌛Checked at: {nowDate.strftime('%H:%M')}")
        print(f"⏳ Wait {sleepTime / 60:.2f} minutes!\n\n")
        await asyncio.sleep(sleepTime)

# Run the script
if __name__ == "__main__":
    asyncio.run(run())
