"""
Data Fetcher Module
This module is responsible for fetching various data from external APIs,
including Ethereum gas fees and the Crypto Fear & Greed Index.
"""

import logging
from datetime import datetime

from src.utils.utils import check_requests

logger = logging.getLogger(__name__)
logger.info("Data Fetcher started")


def get_eth_gas_fee(etherscan_api_url):
    """
    Fetches the current Ethereum gas fees from the Etherscan API.
    Args:
        etherscan_api_url (str): The URL of the Etherscan API endpoint for gas fees.
    Returns:
        tuple: A tuple containing the safe gas price, propose gas price, and fast gas price.
                Returns (None, None, None) if the request fails or data is not available.
    """
    try:
        data = check_requests(etherscan_api_url)

        if data is not None and data["status"] == "1":
            gas_data = data["result"]
            safe_gas = gas_data["SafeGasPrice"]
            propose_gas = gas_data["ProposeGasPrice"]
            fast_gas = gas_data["FastGasPrice"]
            return safe_gas, propose_gas, fast_gas
        logger.error(" Failed to fetch ETH gas fees.")
        print("❌ Failed to fetch ETH gas fees.")
        return None, None, None
    except KeyError as e:
        logger.error(" KeyError while fetching ETH gas fees: %s", e)
        print("❌ KeyError while fetching ETH gas fees:", e)
        return None, None, None


async def get_fear_and_greed_message():
    """
    Fetches the Crypto Fear & Greed Index and formats it into a message.
    Returns:
        str: A formatted message containing the Fear & Greed Index score,
        sentiment, and last update date.
        If the request fails, returns an error message.
    """
    url = "https://api.alternative.me/fng/"

    data = check_requests(url)

    if data is not None:
        index_value = data["data"][0]["value"]  # Fear & Greed Score
        index_text = data["data"][0][
            "value_classification"
        ]  # Sentiment (Fear, Greed, etc.)

        timestamp = int(data["data"][0]["timestamp"])
        last_update_date = datetime.fromtimestamp(timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        message = (
            f"📊 <b>Crypto Fear & Greed Index</b>:\n"
            f"💡 <b>Score</b>: {index_value} / 100\n"
            f"🔎 <b>Sentiment</b>: {index_text}\n"
            f"🕒 Last Updated: {last_update_date}\n"
            f"#FearAndGreed"
        )

        return message
    return "❌ Error during the data request"


async def get_fear_and_greed():
    """
    Fetches the Crypto Fear & Greed Index from the Alternative.me API.
    Returns:
        tuple: A tuple containing the Fear & Greed Index score, sentiment, and last update date.
               Returns (None, None, None) if the request fails or data is not available.
    """
    url = "https://api.alternative.me/fng/"
    data = check_requests(url)

    if data is not None:
        index_value = data["data"][0]["value"]  # Fear & Greed Score
        index_text = data["data"][0][
            "value_classification"
        ]  # Sentiment (Fear, Greed, etc.)

        timestamp = int(data["data"][0]["timestamp"])
        last_update_date = datetime.fromtimestamp(timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        return index_value, index_text, last_update_date
    return None, None, None
