import json
import os

from sdk.SendTelegramMessage import TelegramMessagesHandler
from sdk.Logger import setup_logger
from sdk import LoadVariables

logger = setup_logger("log.log")
logger.info("Open AI Prompt started")

class PortfolioManager:
    def __init__(self):
        self.file_path = "ConfigurationFiles/portfolio.json"

        self.portfolio = None

        self.telegram_api_token = None

        self.telegram_message = TelegramMessagesHandler()

    def reload_the_data(self):
        variables = LoadVariables.load()

        self.telegram_api_token = variables.get("TELEGRAM_API_TOKEN_VALUE", "")

        self.portfolio = self.load_portfolio_from_file()

        self.telegram_message.reload_the_data()

    def load_portfolio_from_file(self):
        """
        Load portfolio data from a JSON file.
        """
        if not os.path.exists(self.file_path):
            logger.error(f"  Portfolio file '{self.file_path}' not found. Using an empty portfolio.")
            print(f"❌ Portfolio file '{self.file_path}' not found. Using an empty portfolio.")
            return {}

        try:
            with open(self.file_path, "r") as file:
                portfolio = json.load(file)
                logger.info(f" Portfolio loaded from '{self.file_path}'.")
                print(f"✅ Portfolio loaded from '{self.file_path}'.")
                return portfolio
        except json.JSONDecodeError:
            logger.error(f" Invalid JSON in portfolio file '{self.file_path}'. Using an empty portfolio.")
            print(f"❌ Invalid JSON in portfolio file '{self.file_path}'. Using an empty portfolio.")
            return {}
        except Exception as e:
            logger.error(f" Error loading portfolio from '{self.file_path}': {e}. Using an empty portfolio.")
            print(f"❌ Error loading portfolio from '{self.file_path}': {e}. Using an empty portfolio.")
            return {}

    def save_portfolio_to_file(self):
        """
        Save the current portfolio to a JSON file.
        """
        try:
            with open(self.file_path, "w") as file:
                json.dump(self.portfolio, file, indent=4)
            logger.info(f" Portfolio saved to '{self.file_path}'.")
            print(f"✅ Portfolio saved to '{self.file_path}'.")
        except Exception as e:
            logger.error(f" Error saving portfolio to '{self.file_path}': {e}")
            print(f"❌ Error saving portfolio to '{self.file_path}': {e}")

    # Function to calculate total portfolio value
    def calculate_portfolio_value(self, my_crypto):
        total_value = 0
        message = "📊 *Portfolio Value Update:*\n\n"

        for symbol, amount in self.portfolio.items():
            if symbol in my_crypto:
                price = my_crypto[symbol]["price"]
                value = price * amount
                total_value += value
                message += f"*{symbol}*: {amount} = ${value:,.2f}\n"

        message += f"\n💰 *Total Portfolio Value: ${total_value:,.2f}*"
        return message

    # Fetch portfolio value and send via Telegram
    async def send_portfolio_update(self, my_crypto, update):
        message = self.calculate_portfolio_value(my_crypto)
        await self.telegram_message.send_telegram_message(message, self.telegram_api_token, True, update)