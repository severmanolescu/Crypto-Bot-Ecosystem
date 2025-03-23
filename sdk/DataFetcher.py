from datetime import datetime

from sdk.Utils import check_requests

from sdk.Logger import setup_logger
logger = setup_logger("log.log")
logger.info("Data Fetcher started")

def get_eth_gas_fee(etherscan_api_url):
    try:
        data = check_requests(etherscan_api_url)

        if data is not None and data["status"] == "1":
            gas_data = data["result"]
            safe_gas = gas_data["SafeGasPrice"]
            propose_gas = gas_data["ProposeGasPrice"]
            fast_gas = gas_data["FastGasPrice"]
            return safe_gas, propose_gas, fast_gas
        else:
            logger.error(f" Failed to fetch ETH gas fees.")
            print("❌ Failed to fetch ETH gas fees.")
            return None, None, None
    except Exception as e:
        logger.error(f" Error fetching ETH gas fees: {e}")
        print(f"❌ Error fetching ETH gas fees: {e}")
        return None, None, None

async def get_fear_and_greed_message():
    url = "https://api.alternative.me/fng/"

    data = check_requests(url)

    if data is not None:
        index_value = data["data"][0]["value"]  # Fear & Greed Score
        index_text = data["data"][0]["value_classification"]  # Sentiment (Fear, Greed, etc.)

        timestamp = int(data["data"][0]['timestamp'])
        last_update_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        message = f"📊 *Crypto Fear & Greed Index*:\n" \
                  f"💡 *Score*: {index_value} / 100\n" \
                  f"🔎 *Sentiment*: {index_text}\n" \
                  f"🕒 Last Updated: {last_update_date}\n" \
                  f"#FearAndGreed"

        return message
    return "❌ Error during the data request"

async def get_fear_and_greed():
    url = "https://api.alternative.me/fng/"
    data = check_requests(url)

    if data is not None:
        index_value = data["data"][0]["value"]  # Fear & Greed Score
        index_text = data["data"][0]["value_classification"]  # Sentiment (Fear, Greed, etc.)

        timestamp = int(data["data"][0]['timestamp'])
        last_update_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        return index_value, index_text, last_update_date
    return None, None, None
