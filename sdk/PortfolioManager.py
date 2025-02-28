import json
import os

from sdk.SendTelegramMessage import TelegramMessagesHandler
from sdk.LoadVariables import load_portfolio_from_file
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

        self.portfolio = load_portfolio_from_file()

        self.telegram_message.reload_the_data()

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

        for symbol, details in self.portfolio.items():
            if symbol in my_crypto:
                price = my_crypto[symbol]["price"]
                value = price * details['quantity']
                total_value += value
                message += f"*{symbol}*: {details['quantity']} = ${value:,.2f}\n"

        message += f"\n💰 *Total Portfolio Value: ${total_value:,.2f}*"
        return message

    # Function to calculate total portfolio value with detailed breakdown
    def calculate_portfolio_value_detailed(self, my_crypto):
        total_value = 0
        total_investment = 0
        message = "📊 *Portfolio Value Update:*\n\n"

        for symbol, details in self.portfolio.items():
            if symbol in my_crypto:
                price = my_crypto[symbol]["price"]
                quantity = details['quantity']
                avg_price = details.get('average_price', None)
                total_invested = avg_price * quantity if avg_price else None
                current_value = price * quantity
                profit_loss = current_value - total_invested if total_invested else None
                profit_loss_percentage = (
                            profit_loss / total_invested * 100) if total_invested and total_invested > 0 else None

                total_value += current_value
                if total_invested:
                    total_investment += total_invested

                message += f"*{symbol}*\n"
                message += f"🔹 Quantity: *{quantity:,.4f}*\n"
                if avg_price:
                    message += f"🔹 Average Price: *${avg_price:,.4f}*\n"
                    message += f"🔹 Total Investment: *${total_invested:,.2f}*\n"
                message += f"🔹 Current Value: *${current_value:,.2f}*\n"

                if profit_loss is not None:
                    profit_symbol = "✅" if profit_loss >= 0 else "🔻"
                    message += f"🔹 *P/L: ${profit_loss:,.2f}* "
                    if profit_loss_percentage is not None:
                        message += f"(*{profit_loss_percentage:+.2f}%*) {profit_symbol}\n"

                message += "\n"

        total_profit_loss = total_value - total_investment if total_investment else None
        total_profit_loss_percentage = (
                    total_profit_loss / total_investment * 100) if total_investment and total_investment > 0 else None

        message += f"💰 *Total Portfolio Value: ${total_value:,.2f}*\n"
        message += f"📊 *Total Investment: ${total_investment:,.2f}*\n"
        if total_profit_loss is not None:
            profit_symbol = "✅" if total_profit_loss >= 0 else "🔻"
            message += f"📉 *Total P/L: ${total_profit_loss:,.2f}* "
            if total_profit_loss_percentage is not None:
                message += f"(*{total_profit_loss_percentage:+.2f}%*) {profit_symbol}\n"

        from datetime import datetime
        message += f"\n⏳ *Last Update:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"

        return message

    # Fetch portfolio value and send via Telegram
    async def send_portfolio_update(self, my_crypto, update, detailed = False):
        if detailed:
            message = self.calculate_portfolio_value_detailed(my_crypto)
        else:
            message = self.calculate_portfolio_value(my_crypto)

        await self.telegram_message.send_telegram_message(message, self.telegram_api_token, True, update)