import requests
import logging

from datetime import datetime

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('log.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

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
            logging.error(f" Failed to fetch ETH gas fees.")
            print("❌ Failed to fetch ETH gas fees.")
            return None, None, None
    except Exception as e:
        logging.error(f" Error fetching ETH gas fees: {e}")
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
                  f"🕒 Last Updated: {last_update_date}"

        return message

    except Exception as e:
        logging.error(f" Error fetching Fear & Greed Index: {e}")
        print(f"❌ Error fetching Fear & Greed Index: {e}")