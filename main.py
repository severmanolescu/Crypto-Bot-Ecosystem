import argparse
from datetime import datetime

import asyncio

from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("Main started")

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
        await cryptoNewsCheck.run()

        print("\n📤 Send crypto value!")
        await cryptoValueBot.fetch_data()

        now_date = datetime.now()

        logger.info(f" Ran at: {now_date.strftime('%H:%M')}")
        logger.info(f" Wait {sleep_time / 60:.2f} minutes")

        print(f"\n⌛Checked at: {now_date.strftime('%H:%M')}")
        print(f"⏳ Wait {sleep_time / 60:.2f} minutes!\n\n")
        await asyncio.sleep(sleep_time)

def main():
    parser = argparse.ArgumentParser(description="Process some arguments.")

    # Adding the --r or --recreate flag
    parser.add_argument("-r", "--recreate", action="store_true", help="Recreate something")

    args = parser.parse_args()

    if args.recreate:
        print("Recreating the data base...")

        asyncio.run(cryptoNewsCheck.recreate_data_base())

    else:
        asyncio.run(run())


if __name__ == "__main__":
    main()
