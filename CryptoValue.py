import requests
import logging
import json
import os

from datetime import datetime

from sdk.OpenAIPrompt import OpenAIPrompt


from sdk import SendTelegramMessage as message_handler
from sdk import LoadVariables as load_variables

logger = logging.getLogger("CryptoValue.py")

logging.basicConfig(filename='log.log', level=logging.INFO)
logger.info(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Started!')

def format_change(change):
    if change is None:
        return "N/A"
    if change < 0:
        return f"`🔴 {change:.2f}%`"  # Negative change in monospace
    else:
        return f"`🟢 +{change:.2f}%`"  # Positive change in monospace

class CryptoValueBot:
    def __init__(self):
        self.lastSentHour = None
        self.alert_threshold = None
        self.my_crypto = None
        self.top_100_crypto = None
        self.portfolio = None
        self.cryptoCurrencies = None
        self.coinmarketcap_api_key = None
        self.coinmarketcap_api_url = None
        self.etherscan_api_url = None
        self.send_ai_summary = None
        self.send_hours = None
        self.openAIPrompt = None
        self.keywords = None
        self.telegram_not_important_chat_id = None
        self.telegram_important_chat_id = None
        self.telegram_api_token_alerts = None
        self.telegram_api_token = None

    def reload_the_data(self):
        variables = load_variables.load()

        self.telegram_api_token = variables.get("TELEGRAM_API_TOKEN_VALUE", "")
        self.telegram_api_token_alerts = variables.get("TELEGRAM_API_TOKEN_ALERTS", "")
        self.telegram_important_chat_id = variables.get("TELEGRAM_CHAT_ID_FULL_DETAILS", [])
        self.telegram_not_important_chat_id = variables.get("TELEGRAM_CHAT_ID_PARTIAL_DATA", [])

        self.keywords = load_variables.load_keyword_list()

        OPEN_AI_API = variables.get('OPEN_AI_API', '')

        self.openAIPrompt = OpenAIPrompt(OPEN_AI_API)

        self.send_hours = variables.get("SEND_HOURS", "")

        self.lastSentHour = None
        self.alert_threshold = load_variables.get_int_variable("ALERT_THRESHOLD", 2.5)

        self.my_crypto = {}
        self.top_100_crypto = {}

        # Load portfolio from file
        self.portfolio = self.load_portfolio_from_file("ConfigurationFiles/portfolio.json")

        self.cryptoCurrencies = variables.get("CRYPTOCURRENCIES", "")

        # CoinMarketCap API credentials
        self.coinmarketcap_api_key = variables.get("CMC_API_KEY", "")
        self.coinmarketcap_api_url = variables.get("CMC_URL_LISTINGS", "")

        # Etherscan API credentials
        self.etherscan_api_url = variables.get("ETHERSCAN_GAS_API_URL", "") + variables.get("ETHERSCAN_API_KEY", "")

        self.send_ai_summary = variables.get("SEND_AI_SUMMARY", "")


    def load_portfolio_from_file(self, file_path):
        """
        Load portfolio data from a JSON file.
        """
        if not os.path.exists(file_path):
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:  Portfolio file '{file_path}' not found. Using an empty portfolio.")
            print(f"❌ Portfolio file '{file_path}' not found. Using an empty portfolio.")
            return {}

        try:
            with open(file_path, "r") as file:
                portfolio = json.load(file)
                logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Portfolio loaded from '{file_path}'.")
                print(f"✅ Portfolio loaded from '{file_path}'.")
                return portfolio
        except json.JSONDecodeError:
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Invalid JSON in portfolio file '{file_path}'. Using an empty portfolio.")
            print(f"❌ Invalid JSON in portfolio file '{file_path}'. Using an empty portfolio.")
            return {}
        except Exception as e:
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error loading portfolio from '{file_path}': {e}. Using an empty portfolio.")
            print(f"❌ Error loading portfolio from '{file_path}': {e}. Using an empty portfolio.")
            return {}

    def save_portfolio_to_file(self, file_path):
        """
        Save the current portfolio to a JSON file.
        """
        try:
            with open(file_path, "w") as file:
                json.dump(self.portfolio, file, indent=4)
            logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Portfolio saved to '{file_path}'.")
            print(f"✅ Portfolio saved to '{file_path}'.")
        except Exception as e:
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error saving portfolio to '{file_path}': {e}")
            print(f"❌ Error saving portfolio to '{file_path}': {e}")

    # Function to calculate total portfolio value
    def calculate_portfolio_value(self):
        total_value = 0
        message = "📊 *Portfolio Value Update:*\n\n"

        for symbol, amount in self.portfolio.items():
            if symbol in self.my_crypto:
                price = self.my_crypto[symbol]["price"]
                value = price * amount
                total_value += value
                message += f"*{symbol}*: {amount} = ${value:,.2f}\n"

        message += f"\n💰 *Total Portfolio Value: ${total_value:,.2f}*"
        return message

    # Fetch portfolio value and send via Telegram
    async def send_portfolio_update(self):
        message = self.calculate_portfolio_value()
        await message_handler.send_telegram_message(message, self.telegram_api_token, self.telegram_important_chat_id,
                                    self.telegram_not_important_chat_id, True)

    # Function to fetch cryptocurrency prices and price changes
    def get_my_crypto(self):
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.coinmarketcap_api_key,
        }
        parameters = {
            "start": "1",
            "limit": "100",
            "convert": "USD",
        }
        response = requests.get(self.coinmarketcap_api_url, headers=headers, params=parameters)
        data = json.loads(response.text)

        for crypto in data["data"]:
            symbol = crypto["symbol"]
            if symbol in self.cryptoCurrencies:
                self.my_crypto[symbol] = {
                    "price": crypto["quote"]["USD"]["price"],
                    "change_1h": crypto["quote"]["USD"]["percent_change_1h"],
                    "change_24h": crypto["quote"]["USD"]["percent_change_24h"],
                    "change_7d": crypto["quote"]["USD"]["percent_change_7d"],
                    "change_30d": crypto["quote"]["USD"]["percent_change_30d"],
                }
            self.top_100_crypto[symbol] = {
                "price": crypto["quote"]["USD"]["price"],
                "change_1h": crypto["quote"]["USD"]["percent_change_1h"],
                "change_24h": crypto["quote"]["USD"]["percent_change_24h"],
                "change_7d": crypto["quote"]["USD"]["percent_change_7d"],
                "change_30d": crypto["quote"]["USD"]["percent_change_30d"],
            }

    # Function to fetch Ethereum gas fees
    def get_eth_gas_fee(self):
        try:
            response = requests.get(self.etherscan_api_url)
            data = response.json()

            if data["status"] == "1":
                gas_data = data["result"]
                safe_gas = gas_data["SafeGasPrice"]
                propose_gas = gas_data["ProposeGasPrice"]
                fast_gas = gas_data["FastGasPrice"]
                return safe_gas, propose_gas, fast_gas
            else:
                logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Failed to fetch ETH gas fees.")
                print("❌ Failed to fetch ETH gas fees.")
                return None, None, None
        except Exception as e:
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error fetching ETH gas fees: {e}")
            print(f"❌ Error fetching ETH gas fees: {e}")
            return None, None, None

    async def show_fear_and_greed(self):
        url = "https://api.alternative.me/fng/"

        try:
            response = requests.get(url)
            data = response.json()

            index_value = data["data"][0]["value"]  # Fear & Greed Score
            index_text = data["data"][0]["value_classification"]  # Sentiment (Fear, Greed, etc.)

            timestamp = int(data["data"][0]['timestamp'])
            last_update_date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

            message = f"📊 *Crypto Fear & Greed Index*:\n" \
                      f"💡 *Score*: {index_value} / 100\n" \
                      f"🔎 *Sentiment*: {index_text}\n" \
                      f"🕒 Last Updated: {last_update_date}"

            await message_handler.send_telegram_message(message, self.telegram_api_token,
                                                        self.telegram_important_chat_id,
                                                        self.telegram_not_important_chat_id, True)

        except Exception as e:
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Error fetching Fear & Greed Index: {e}")
            print(f"❌ Error fetching Fear & Greed Index: {e}")

    async def send_eth_gas_fee(self):
        message = ""
        safe_gas, propose_gas, fast_gas = self.get_eth_gas_fee()
        if safe_gas and propose_gas and fast_gas:
            message += (
                f"⛽ *ETH Gas Fees (Gwei)*:\n"
                f"🐢 Safe: {safe_gas}\n"
                f"🚗 Propose: {propose_gas}\n"
                f"🚀 Fast: {fast_gas}\n\n"
            )
        await message_handler.send_telegram_message(message, self.telegram_api_token, self.telegram_important_chat_id,
                                                    self.telegram_not_important_chat_id, True)

    async def send_market_update(self, nowDate):
        message = f"🕒 *Market Update at {nowDate.strftime('%H:%M')}*"

        if self.send_ai_summary == "True":
            message += '\n\n'
            message += await self.openAIPrompt.getResponse(f"Based on the hour: {nowDate.hour} generate a quote")
        message += f"\n\n"

        for symbol, data in self.my_crypto.items():
            message += (
                f"*{symbol}*\n"
                f"Price: $*{data['price']:.2f}*\n"
                f"1h: {format_change(data['change_1h'])}\n"
                f"24h: {format_change(data['change_24h'])}\n"
                f"7d: {format_change(data['change_7d'])}\n"
                f"30d: {format_change(data['change_30d'])}\n\n"
            )

        await message_handler.send_telegram_message(message, self.telegram_api_token, self.telegram_important_chat_id,
                                                    self.telegram_not_important_chat_id, True)
    # Scheduled market updates
    async def send_all_the_messages(self, nowDate):
        if nowDate.hour in self.send_hours and self.lastSentHour != nowDate.hour:
            self.lastSentHour = nowDate.hour

            await self.send_market_update(nowDate)

            await self.send_eth_gas_fee()

            if nowDate.hour == sorted(self.send_hours)[0]:
                await self.show_fear_and_greed()

            await self.send_portfolio_update()

    # Check for alerts every 30 minutes
    async def check_for_major_updates(self, nowDate):
        alert_message = "🚨 *Crypto Alert!* Significant 1-hour change detected:\n\n"
        alerts_found = False

        for symbol, data in self.top_100_crypto.items():
            change_1h = data["change_1h"]

            if abs(change_1h) >= self.alert_threshold:  # Check if change exceeds ±5%
                alerts_found = True
                alert_message += f"*{symbol}* → {format_change(change_1h)}\n"

        if alerts_found:
            await message_handler.send_telegram_message(alert_message, self.telegram_api_token_alerts,
                                                        self.telegram_important_chat_id,
                                                        self.telegram_not_important_chat_id, True)

            return True
        else:
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: No major price movement!")
            print(f"No major price movement at {nowDate.strftime('%H:%M')}")

        return False

    async def fetch_Data(self):
        self.get_my_crypto()

        nowDate = datetime.now()

        await self.send_all_the_messages(nowDate)

        await self.check_for_major_updates(nowDate)