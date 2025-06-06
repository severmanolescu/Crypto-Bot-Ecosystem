"""
main.py
This script is the main entry point for the Crypto Value Bot and News Check application.
"""

# pylint: disable=global-variable-not-assigned
import argparse
import asyncio
import logging
from datetime import datetime

import sdk.load_variables_handler
from crypto_value_handler import CryptoValueBot
from news_check_handler import CryptoNewsCheck
from sdk.logger_handler import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

logger.info("Main started")

cryptoValueBot = CryptoValueBot()
cryptoNewsCheck = CryptoNewsCheck()


def read_variables():
    """
    Read variables from the configuration and reload the data for the bots.
    """
    global cryptoValueBot
    global cryptoNewsCheck

    cryptoValueBot.reload_the_data()

    cryptoNewsCheck.reload_the_data()


async def run():
    """
    Run the main loop for the Crypto Value Bot and News Check application.
    """
    while True:
        global cryptoValueBot
        global cryptoNewsCheck

        read_variables()

        sleep_time = sdk.load_variables_handler.get_int_variable("SLEEP_DURATION", 1800)

        print("\n🧐 Check for new articles!")
        await cryptoNewsCheck.run()

        print("\n📤 Send crypto value!")
        await cryptoValueBot.fetch_data()

        now_date = datetime.now()

        # pylint: disable=logging-fstring-interpolation
        logger.info(f" Ran at: {now_date.strftime('%H:%M')}")
        # pylint: disable=logging-fstring-interpolation
        logger.info(f" Wait {sleep_time / 60:.2f} minutes")

        print(f"\n⌛Checked at: {now_date.strftime('%H:%M')}")
        print(f"⏳ Wait {sleep_time / 60:.2f} minutes!\n\n")
        await asyncio.sleep(sleep_time)


def main():
    """
    Main function to handle command line arguments and start the application.
    """
    parser = argparse.ArgumentParser(
        description="Recreate the news data base if needed."
    )

    parser.add_argument(
        "-r", "--recreate", action="store_true", help="Recreate the news data base"
    )

    args = parser.parse_args()

    if args.recreate:
        print("Recreating the data base...")

        asyncio.run(cryptoNewsCheck.recreate_data_base())

    else:
        asyncio.run(run())


if __name__ == "__main__":
    main()
