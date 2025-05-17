import datetime
import json
import os

import pytz

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
        message = "📊 <b>Portfolio Value Update:</b>\n\n"

        for symbol, details in self.portfolio.items():
            if symbol in my_crypto:
                price = my_crypto[symbol]["price"]
                value = price * details['quantity']
                total_value += value
                message += f"<b>{symbol}</b>: {details['quantity']} = ${value:,.2f}\n"

        message += f"\n💰 <b>Total Portfolio Value: ${total_value:,.2f}</b>"
        return message

    # Function to calculate total portfolio value with detailed breakdown
    def calculate_portfolio_value_detailed(self, my_crypto, save_data = False):
        total_value = 0
        total_investment = 0
        message = "📊 <b>Portfolio Value Update:</b>\n\n"

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

                message += f"<b>{symbol}</b>\n"
                message += f"🔹 Quantity: <b>{quantity:,.4f}</b>\n"
                if avg_price:
                    message += f"🔹 Average Price: <b>${avg_price:,.4f}</b>\n"
                    message += f"🔹 Total Investment: <b>${total_invested:,.2f}</b>\n"
                message += f"🔹 Current Value: <b>${current_value:,.2f}</b>\n"

                if profit_loss is not None:
                    profit_symbol = "✅" if profit_loss >= 0 else "🔻"
                    message += f"🔹 <b>P/L: ${profit_loss:,.2f}</b>"
                    if profit_loss_percentage is not None:
                        message += f"(<b>{profit_loss_percentage:+.2f}%</b>) {profit_symbol}\n"

                message += "\n"

        total_profit_loss = total_value - total_investment if total_investment else None
        total_profit_loss_percentage = (
                    total_profit_loss / total_investment * 100) if total_investment and total_investment > 0 else None

        message += f"💰 <b>Total Portfolio Value: ${total_value:,.2f}</b>\n"
        message += f"📊 <b>Total Investment: ${total_investment:,.2f}</b>\n"
        if total_profit_loss is not None:
            profit_symbol = "✅" if total_profit_loss >= 0 else "🔻"
            message += f"📉 <b>Total P/L: ${total_profit_loss:,.2f}</b> "
            if total_profit_loss_percentage is not None:
                message += f"(<b>{total_profit_loss_percentage:+.2f}%</b>) {profit_symbol}\n"

        from datetime import datetime
        message += f"\n⏳ <b>Last Update:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"

        if save_data:
            self.save_portfolio_history(total_value, total_investment, total_profit_loss, total_profit_loss_percentage)

        return message

    def save_portfolio_history(self, total_value, total_investment, total_profit_loss, total_profit_loss_percentage):
        history_file = "ConfigurationFiles/portfolio_history.json"

        # Define your time zone (replace 'Europe/Bucharest' if needed)
        local_tz = pytz.timezone('Europe/Bucharest')
        now = datetime.datetime.now(local_tz)

        # Load existing history if available
        if os.path.exists(history_file):
            with open(history_file, "r") as file:
                try:
                    history_data = json.load(file)
                except json.JSONDecodeError:
                    history_data = []
        else:
            history_data = []

        # Create a new entry with date and time
        new_entry = {
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),  # Format: YYYY-MM-DD HH:MM:SS
            "total_value": total_value,
            "total_investment": total_investment,
            "profit_loss": total_profit_loss,
            "profit_loss_percentage": total_profit_loss_percentage
        }

        # Append new entry
        history_data.append(new_entry)

        # Save back to file
        with open(history_file, "w") as file:
            json.dump(history_data, file, indent=4)

        logger.info(f"Portfolio history updated at {new_entry['datetime']} (Local Time).")
        print(f"✅ Portfolio history saved at {new_entry['datetime']} (Local Time).")

    # Fetch portfolio value and send via Telegram
    async def send_portfolio_update(self, my_crypto, update, detailed = False, save_data = False):
        if detailed:
            message = self.calculate_portfolio_value_detailed(my_crypto, save_data=save_data)

            message += "\n#DetailedPortfolio"
        else:
            message = self.calculate_portfolio_value(my_crypto)

            message += "\n#Portfolio"

        await self.telegram_message.send_telegram_message(message, self.telegram_api_token, True, update)

    async def save_portfolio_history_hourly(self, my_crypto):
        self.calculate_portfolio_value_detailed(my_crypto, save_data=True)
