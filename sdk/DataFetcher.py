import requests

from datetime import datetime

from sdk.Logger import setup_logger
logger = setup_logger("log.log")
logger.info("Data Fetcher started")

def get_eth_gas_fee(etherscan_api_url):
    try:
        response = requests.get(etherscan_api_url)
        data = response.json()

        if data["status"] == "1":
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

async def get_fear_and_greed():
    url = "https://api.alternative.me/fng/"

    try:
        response = requests.get(url)
        data = response.json()

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

    except Exception as e:
        logger.error(f" Error fetching Fear & Greed Index: {e}")
        print(f"❌ Error fetching Fear & Greed Index: {e}")