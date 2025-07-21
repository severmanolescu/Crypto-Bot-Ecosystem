"""
portfolio_manager.py
This module provides functionality to manage a cryptocurrency portfolio,
calculate its value, and send updates via Telegram.
"""

import datetime
import json
import logging
import os

import pytz

from src.handlers.load_variables_handler import load_json, load_portfolio_from_file
from src.handlers.send_telegram_message import TelegramMessagesHandler

logger = logging.getLogger(__name__)
logger.info("Open AI Prompt started")


class PortfolioManager:
    """
    PortfolioManager class to handle cryptocurrency portfolio management.
    """

    def __init__(self):
        """
        Initializes the PortfolioManager with necessary components.
        """
        self.file_path = "config/portfolio.json"

        self.portfolio = None

        self.telegram_api_token = None

        self.telegram_message = TelegramMessagesHandler()

    def reload_the_data(self):
        """
        Reload the data from the configuration file and update the portfolio.
        """
        variables = load_json()

        self.telegram_api_token = variables.get("TELEGRAM_API_TOKEN_VALUE", "")

        self.portfolio = load_portfolio_from_file()

        self.telegram_message.reload_the_data()

    def save_portfolio_to_file(self):
        """
        Save the current portfolio to a JSON file.
        """
        try:
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump(self.portfolio, file, indent=4)
            logger.info(" Portfolio saved to %s.", self.file_path)
            print(f"✅ Portfolio saved to '{self.file_path}'.")
        except FileNotFoundError:
            logger.error(" Portfolio file %s not found.", self.file_path)
            print(f"❌ Portfolio file '{self.file_path}' not found.")

    # Function to calculate total portfolio value
    def calculate_portfolio_value(self, my_crypto):
        """
        Calculate the total value of the portfolio based on current prices.
        Args:
            my_crypto (dict): A dictionary containing current prices of cryptocurrencies.
        Returns:
            str: A formatted message with the portfolio value and breakdown.
        """
        total_value = 0
        message = "📊 <b>Portfolio Value Update:</b>\n\n"

        for symbol, details in self.portfolio.items():
            if symbol in my_crypto:
                price = my_crypto[symbol]["price"]
                value = price * details["quantity"]
                total_value += value
                message += f"<b>{symbol}</b>: {details['quantity']} = ${value:,.2f}\n"

        message += f"\n💰 <b>Total Portfolio Value: ${total_value:,.2f}</b>"
        return message

    # Function to calculate total portfolio value with detailed breakdown
    # pylint:disable=too-many-locals
    def calculate_portfolio_value_detailed(self, my_crypto, save_data=False):
        """
        Calculate the total value of the portfolio with detailed breakdown.
        Args:
            my_crypto (dict): A dictionary containing current prices of cryptocurrencies.
            save_data (bool): Whether to save the portfolio history to a file.
        """
        total_value = 0
        total_investment = 0
        message = "📊 <b>Portfolio Value Update:</b>\n\n"

        for symbol, details in self.portfolio.items():
            if symbol in my_crypto:
                price = my_crypto[symbol]["price"]
                quantity = details["quantity"]
                avg_price = details.get("average_price", None)
                total_invested = avg_price * quantity if avg_price else None
                current_value = price * quantity
                profit_loss = current_value - total_invested if total_invested else None
                profit_loss_percentage = (
                    (profit_loss / total_invested * 100)
                    if total_invested and total_invested > 0
                    else None
                )

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
                        message += (
                            f"(<b>{profit_loss_percentage:+.2f}%</b>) {profit_symbol}\n"
                        )

                message += "\n"

        total_profit_loss = total_value - total_investment if total_investment else None
        total_profit_loss_percentage = (
            (total_profit_loss / total_investment * 100)
            if total_investment and total_investment > 0
            else None
        )

        message += f"💰 <b>Total Portfolio Value: ${total_value:,.2f}</b>\n"
        message += f"📊 <b>Total Investment: ${total_investment:,.2f}</b>\n"
        if total_profit_loss is not None:
            profit_symbol = "✅" if total_profit_loss >= 0 else "🔻"
            message += f"📉 <b>Total P/L: ${total_profit_loss:,.2f}</b> "
            if total_profit_loss_percentage is not None:
                message += (
                    f"(<b>{total_profit_loss_percentage:+.2f}%</b>) {profit_symbol}\n"
                )

        message += f"\n⏳ <b>Last Update:</b> {
        datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"

        if save_data:
            self.save_portfolio_history(
                total_value,
                total_investment,
                total_profit_loss,
                total_profit_loss_percentage,
            )

        return message

    def save_portfolio_history(
        self,
        total_value,
        total_investment,
        total_profit_loss,
        total_profit_loss_percentage,
    ):
        """
        Save the portfolio history to a JSON file with date and time.
        Args:
            total_value (float): The total value of the portfolio.
            total_investment (float): The total amount invested in the portfolio.
            total_profit_loss (float): The total profit or loss of the portfolio.
            total_profit_loss_percentage (float): The percentage of profit or loss.
        """
        history_file = "config/portfolio_history.json"

        # Define your time zone (replace 'Europe/Bucharest' if needed)
        local_tz = pytz.timezone("Europe/Bucharest")
        now = datetime.datetime.now(local_tz)

        # Load existing history if available
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as file:
                try:
                    history_data = json.load(file)
                except json.JSONDecodeError:
                    history_data = []
        else:
            history_data = []

        # Create a new entry with date and time
        new_entry = {
            "datetime": now.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),  # Format: YYYY-MM-DD HH:MM:SS
            "total_value": total_value,
            "total_investment": total_investment,
            "profit_loss": total_profit_loss,
            "profit_loss_percentage": total_profit_loss_percentage,
        }

        # Append new entry
        history_data.append(new_entry)

        # Save back to file
        with open(history_file, "w", encoding="utf-8") as file:
            json.dump(history_data, file, indent=4)

        # pylint: disable=logging-fstring-interpolation
        logger.info(
            f"Portfolio history updated at {new_entry['datetime']} (Local Time)."
        )
        print(f"✅ Portfolio history saved at {new_entry['datetime']} (Local Time).")

    # Fetch portfolio value and send via Telegram
    async def send_portfolio_update(
        self, my_crypto, update, detailed=False, save_data=False
    ):
        """
        Fetch the portfolio value and send it via Telegram.
        Args:
            my_crypto (dict): A dictionary containing current prices of cryptocurrencies.
            update: The update object from Telegram.
            detailed (bool): Whether to send a detailed portfolio value.
            save_data (bool): Whether to save the portfolio history data.
        """
        if detailed:
            message = self.calculate_portfolio_value_detailed(
                my_crypto, save_data=save_data
            )

            message += "\n#DetailedPortfolio"
        else:
            message = self.calculate_portfolio_value(my_crypto)

            message += "\n#Portfolio"

        await self.telegram_message.send_telegram_message(
            message, self.telegram_api_token, True, update
        )

    async def save_portfolio_history_hourly(self, my_crypto):
        """
        Save the portfolio history every hour with detailed value.
        Args:
            my_crypto (dict): A dictionary containing current prices of cryptocurrencies.
        """
        self.calculate_portfolio_value_detailed(my_crypto, save_data=True)
