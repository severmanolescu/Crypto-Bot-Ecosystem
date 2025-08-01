"""
My Slave Bot
"""

# pylint: disable=wrong-import-position


import logging
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.handlers.load_variables_handler import (
    load_json,
    load_keyword_list,
    load_portfolio_from_file,
    load_symbol_to_id,
)
from src.handlers.logger_handler import setup_logger
from src.handlers.save_data_handler import (
    save_data_to_json_file,
    save_keywords,
    save_transaction,
    save_variables_json,
)
from src.utils.utils import check_if_special_user, check_requests

setup_logger(file_name="slave_bot.log")
logger = logging.getLogger(__name__)
logger.info("My Slave Bot started")

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [["🚨 Help"]],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)


# pylint: disable=too-many-public-methods
class SlaveBot:
    """
    A Telegram bot that provides cryptocurrency data and trading functionalities.
    """

    def __init__(self):
        """
        Initializes the bot with URLs and headers for API requests.
        """
        self.cmc_url = None
        self.cmc_top10_url = None
        self.coingecko_url = None
        self.headers = None

    def reload_the_data(self):
        """
        Reloads the API URLs and headers from the configuration file.
        """
        variables = load_json()

        self.cmc_url = variables.get("CMC_URL_QUOTES", "")
        self.cmc_top10_url = variables.get("CMC_TOP10_URL", "")

        self.coingecko_url = variables.get("COINGECKO_URL", "")

        cmc_api_key = variables.get("CMC_API_KEY", "")

        self.headers = {"X-CMC_PRO_API_KEY": cmc_api_key}

    # Command: /start
    # pylint: disable=unused-argument
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /start command and sends a welcome message with buttons.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        await update.message.reply_text(
            "🤖 Welcome to the Slave Bot! Use the buttons below to get started:",
            reply_markup=NEWS_KEYBOARD,
        )

    # Function to fetch crypto data
    def get_crypto_data(self, symbol):
        """
        Fetches cryptocurrency data from CoinMarketCap API.
        Args:
            symbol (str): The cryptocurrency symbol (e.g., "BTC").
        Returns:
            dict: A dictionary containing the cryptocurrency data, or None if not found.
        """
        params = {"symbol": symbol.upper(), "convert": "USD"}

        self.reload_the_data()

        data = check_requests(self.cmc_url, self.headers, params)

        if data is not None and "data" in data and symbol.upper() in data["data"]:
            coin_data = data["data"][symbol.upper()]
            quote = coin_data["quote"]["USD"]
            return {
                "name": coin_data["name"],
                "symbol": coin_data["symbol"],
                "price": quote["price"],
                "market_cap": quote["market_cap"],
                "volume": quote["volume_24h"],
                "change_1h": quote["percent_change_1h"],
                "change_24h": quote["percent_change_24h"],
                "change_7d": quote["percent_change_7d"],
                "change_30d": quote["percent_change_30d"],
                "dominance": quote["market_cap_dominance"],
                "total_supply": coin_data["total_supply"],
                "circulating_supply": coin_data["circulating_supply"],
            }
        return None  # Coin not found

    # Function to fetch top 10 cryptos
    def get_top_10(self):
        """
        Fetches the top 10 cryptocurrencies by market cap from CoinMarketCap API.
        Returns:
            str: A formatted string with the top 10 cryptocurrencies and their details.
        """
        params = {"start": 1, "limit": 10, "convert": "USD"}

        self.reload_the_data()

        data = check_requests(self.cmc_top10_url, self.headers, params)

        if data is not None and "data" in data:
            top_10 = data["data"]
            result = "🚀 <b>Top 10 Cryptos by Market Cap:</b>\n\n"
            for coin in top_10:
                name = coin["name"]
                symbol = coin["symbol"]
                price = coin["quote"]["USD"]["price"]
                market_cap = coin["quote"]["USD"]["market_cap"]
                result += (
                    f"🔹 <b>{name} ({symbol})</b>\n"
                    f"💰 Price: ${price:,.2f}\n"
                    f"🏦 Market Cap: ${market_cap:,.2f}\n\n"
                )
            return result
        logger.error(" Error fetching top 10 cryptocurrencies.")
        return "❌ Error fetching top 10 cryptocurrencies."

    def get_ath_from_coingecko(self, symbol):
        """
        Retrieves the all-time high (ATH) price of a cryptocurrency from CoinGecko.
        Args:
            symbol (str): The cryptocurrency symbol (e.g., "BTC").
        Returns:
            float: The all-time high price in USD, or None if not found.
        """
        self.reload_the_data()

        # Load the symbol-to-ID mapping
        symbol_to_id = load_symbol_to_id()

        coin_id = symbol_to_id.get(symbol.upper())

        if not coin_id:
            return None  # Symbol not supported

        data = check_requests(f"{self.coingecko_url}/coins/{coin_id}")

        if data is not None and "market_data" in data:
            return data["market_data"]["ath"]["usd"]
        return None  # ATH not found

    async def get_details(self, data, symbol):
        """
        Fetches and formats the details of a cryptocurrency.
        Args:
            data (dict): The cryptocurrency data dictionary.
            symbol (str): The cryptocurrency symbol (e.g., "BTC").
        Returns:
            str: A formatted string with the cryptocurrency details.
        """
        ath_price = self.get_ath_from_coingecko(symbol)

        if ath_price is not None:
            ath_message = ath_price
        else:
            ath_message = "Can't find ATH"

        if data:
            return (
                f"💰 Price: ${data['price']:.2f}\n"
                f"🏦 Market Cap: ${data['market_cap']:,.2f}\n"
                f"📊 24h Volume: ${data['volume']:,.2f}\n"
                f"🌍 Market Dominance: {data['dominance']:.2f}%\n"
                f"📦 Circulating Supply: {data['circulating_supply']:,.2f}\n"
                f"📦 Total Supply: {data['total_supply']:,.2f}\n"
                f"🚀 All time high: {ath_message}\n"
                f"\n"
                f"📈 Price Changes:\n"
                f"🕐 1 Hour: {data['change_1h']:.2f}%\n"
                f"🌅 24 Hours: {data['change_24h']:.2f}%\n"
                f"📆 7 Days: {data['change_7d']:.2f}%\n"
                f"📅 30 Days: {data['change_30d']:.2f}%\n"
            )
        logger.error(" Couldn't fetch details for %s", symbol)
        return f"❌ Couldn't fetch details for {symbol}."

    # Handle `/details <symbol>` command
    async def details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /details command to fetch and display cryptocurrency details.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        symbol = context.args[0] if context.args else "BTC"

        # pylint: disable=logging-fstring-interpolation
        logger.error(
            f" User {update.effective_chat.id} " f"requested details for {symbol}"
        )

        data = self.get_crypto_data(symbol)

        logger.info(" Requested: details %s", symbol)

        message = f"📌 Crypto Details: {data['name']} ({symbol.upper()})\n"

        message += await self.get_details(data, symbol)

        await update.message.reply_text(message)

    # Handle `/top10` command
    # pylint: disable=unused-argument
    async def top10(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /top10 command to fetch and display the top 10 cryptocurrencies by market cap.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        text = self.get_top_10()

        logger.info(" Requested: top 10")

        await update.message.reply_text(text, parse_mode="HTML")

    # Handle `/compare <symbol1> <symbol2>` command
    async def compare(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /compare command to compare two cryptocurrencies.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if len(context.args) != 2:
            await update.message.reply_text(
                "❌ Please provide two cryptocurrency symbols to compare."
            )
            return

        symbol1, symbol2 = context.args
        data1, data2 = self.get_crypto_data(symbol1), self.get_crypto_data(symbol2)

        if data1 and data2:
            message = f"""
    📊 Comparison: <b>{symbol1.upper()}</b> vs <b>{symbol2.upper()}</b>

💰 <b>Price</b>:
- {symbol1.upper()}: ${data1["price"]:.2f}
- {symbol2.upper()}: ${data2["price"]:.2f}

🏦 <b>Market Cap</b>:
- {symbol1.upper()}: ${data1["market_cap"]:.2f}
- {symbol2.upper()}: ${data2["market_cap"]:.2f}

📈 <b>24h Change</b>:
- {symbol1.upper()}: {data1["change_24h"]:.2f}%
- {symbol2.upper()}: {data2["change_24h"]:.2f}%
"""
            print(message)  # To preview before sending via Telegram

            await update.message.reply_text(message, parse_mode="HTML")
        else:
            await update.message.reply_text(
                "❌ Couldn't fetch data for one or both symbols."
            )

    # Function to convert cryptocurrency
    def convert_crypto(self, amount, from_symbol, to_symbol):
        """
        Converts a specified amount of one cryptocurrency to another.
        Args:
            amount (float): The amount of the cryptocurrency to convert.
            from_symbol (str): The symbol of the cryptocurrency to convert from (e.g., "BTC").
            to_symbol (str): The symbol of the cryptocurrency to convert to (e.g., "ETH").
        Returns:
            float: The converted amount in the target cryptocurrency, or None if conversion is
            not possible.
        """
        self.reload_the_data()

        params = {"symbol": from_symbol.upper(), "convert": to_symbol.upper()}

        data = check_requests(self.cmc_url, self.headers, params)

        if data is not None and "data" in data and from_symbol.upper() in data["data"]:
            coin_data = data["data"][from_symbol.upper()]
            if to_symbol.upper() in coin_data["quote"]:
                conversion_rate = coin_data["quote"][to_symbol.upper()]["price"]
                converted_amount = amount * conversion_rate
                return converted_amount
        return None  # Conversion not possible

    # Handle `/convert <amount> <from_symbol> <to_symbol>` command
    async def convert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /convert command to convert a specified amount of one cryptocurrency to another.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if len(context.args) != 3:
            logger.error(" Usage: /convert <amount> <from symbol> <to symbol>")
            await update.message.reply_text(
                "❌ Usage: /convert <amount> <from symbol> <to symbol>"
            )
            return

        try:
            amount = float(context.args[0])
            from_symbol = context.args[1]
            to_symbol = context.args[2]

        except ValueError:
            logger.error(" Invalid amount. Please provide a valid number.")
            await update.message.reply_text(
                "❌ Invalid amount. Please provide a valid number."
            )
            return

        converted_amount = self.convert_crypto(amount, from_symbol, to_symbol)

        # pylint: disable=logging-fstring-interpolation
        logger.info(f" Requested: convert {amount} {from_symbol} {to_symbol}")

        if converted_amount is not None:
            text = (
                f"🔁 <b>Conversion Result:</b>\n{amount} {from_symbol.upper()} = "
                f"{converted_amount:.2f} {to_symbol.upper()}"
            )
            await update.message.reply_text(text, parse_mode="HTML")
        else:
            # pylint: disable=logging-fstring-interpolation
            logger.error(
                f" Couldn't convert {from_symbol.upper()} to {to_symbol.upper()}."
            )
            await update.message.reply_text(
                f"❌ Couldn't convert {from_symbol.upper()} to {to_symbol.upper()}."
            )

    # Handle `/mcap_change <symbol>` command
    async def mcap_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /mcap_change command to fetch and display the market cap change
        for a cryptocurrency.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if len(context.args) != 1:
            logger.error(" Usage: /mcap_change <symbol>")
            await update.message.reply_text("❌ Usage: /mcap_change <symbol>")
            return

        symbol = context.args[0].upper()
        data = self.get_crypto_data(symbol)

        logger.info(" Requested: mcap change %s", symbol)

        if data:
            change_24h = data["change_24h"]
            text = f"📊 <b>Market Cap Change for {symbol} (24h):</b> {change_24h:.2f}%"
            await update.message.reply_text(text, parse_mode="HTML")
        else:
            logger.error(" Couldn't fetch market cap change for %s.", symbol)
            await update.message.reply_text(
                f"❌ Couldn't fetch market cap change for {symbol}."
            )

    # Handle `/roi <symbol> <initial_investment>` command
    async def roi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /roi command to calculate the return on investment (ROI) for a cryptocurrency.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if len(context.args) != 3:
            logger.error(" Usage: /roi <symbol> <initial_investment> <initial_price>")
            await update.message.reply_text(
                "❌ Usage: /roi <symbol> <initial_investment> <initial_price>"
            )
            return

        symbol = context.args[0].upper()

        logger.info(" Requested: roi %s", symbol)

        try:
            initial_investment = float(context.args[1])
            initial_price = float(context.args[2])
        except ValueError:
            logger.error(" Invalid input. Please provide valid numbers.")
            await update.message.reply_text(
                "❌ Invalid input. Please provide valid numbers."
            )
            return

        data = self.get_crypto_data(symbol)

        if data:
            current_price = data["price"]
            roi_percentage = ((current_price - initial_price) / initial_price) * 100
            current_value = (initial_investment / initial_price) * current_price

            text = f"""
📈 <b>ROI for {symbol} with ${initial_investment:.2f} investment:</b>
- Initial Price: ${initial_price:.2f}
- Current Price: ${current_price:.2f}
- Current Value: ${current_value:.2f}
- ROI: {roi_percentage:.2f}%
    """
            await update.message.reply_text(text, parse_mode="HTML")
        else:
            logger.error(" Couldn't fetch ROI data for %s.", symbol)
            await update.message.reply_text(f"❌ Couldn't fetch ROI data for {symbol}.")

    def update_buy(self, portfolio, symbol, amount, price):
        """
        Handles buying a cryptocurrency and updating the portfolio.
        Args:
            portfolio (dict): The current portfolio dictionary.
            symbol (str): The cryptocurrency symbol (e.g., "BTC").
            amount (float): The amount of the cryptocurrency to buy.
            price (float): The price of the cryptocurrency at the time of purchase.
        """
        if symbol in portfolio:
            current_quantity = portfolio[symbol]["quantity"]
            current_avg_price = portfolio[symbol]["average_price"]
            current_total_investment = portfolio[symbol]["total_investment"]

            # Weighted average price calculation
            new_quantity = current_quantity + amount
            new_avg_price = (
                (current_quantity * current_avg_price) + (amount * price)
            ) / new_quantity
            new_total_investment = current_total_investment + (amount * price)
        else:
            # If it's a new asset, initialize with all required fields
            new_quantity = amount
            new_avg_price = price
            new_total_investment = round(amount * price, 2)

        portfolio[symbol] = {
            "quantity": round(new_quantity, 6),
            "average_price": round(new_avg_price, 6),
            "total_investment": round(new_total_investment, 2),
            "allocation_percentage": None,  # To be calculated later
        }

    def update_sell(self, portfolio, symbol, amount, price):
        """
        Handles selling a cryptocurrency, updating the portfolio, and adding USDT balance.
        Args:
            portfolio (dict): The current portfolio dictionary.
            symbol (str): The cryptocurrency symbol (e.g., "BTC").
            amount (float): The amount of the cryptocurrency to sell.
            price (float): The price of the cryptocurrency at the time of sale.
        """
        if symbol not in portfolio or portfolio[symbol]["quantity"] < amount:
            return False

        # Calculate value in USDT
        value_in_usdt = round(amount * price, 2)

        # Deduct from crypto balance
        portfolio[symbol]["quantity"] -= amount
        portfolio[symbol]["total_investment"] -= round(
            amount * portfolio[symbol]["average_price"], 2
        )

        # Remove asset if quantity reaches zero
        if portfolio[symbol]["quantity"] <= 0:
            del portfolio[symbol]

        # Ensure USDT exists in portfolio
        if "USDT" not in portfolio:
            portfolio["USDT"] = {"quantity": 0}

        # Add the value of the sale to USDT balance
        portfolio["USDT"]["quantity"] += value_in_usdt

        return True

    def update_portfolio(self, symbol, amount, price, action):
        """
        Update the portfolio based on a buy or sell transaction.
        Args:
            symbol (str): The cryptocurrency symbol (e.g., "BTC").
            amount (float): The amount of the cryptocurrency to buy or sell.
            price (float): The price of the cryptocurrency at the time of transaction.
            action (str): The action to perform, either "buy" or "sell".
        Returns:
            bool: True if the portfolio was updated successfully, False otherwise.
        """
        symbol = symbol.upper()
        portfolio = load_portfolio_from_file()

        if action == "buy":
            self.update_buy(portfolio, symbol, amount, price)
        elif action == "sell":
            if not self.update_sell(portfolio, symbol, amount, price):
                return False
        else:
            logger.error("❌ Invalid action: %s. Use 'buy' or 'sell'.", action)
            return False

        # Save updated portfolio and transaction
        save_data_to_json_file("./config/portfolio.json", portfolio)

        save_transaction(symbol, action, amount, price)

        return True

    # Handle `/buy <symbol> <amount>` command
    async def buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /buy command to buy a specified amount of a cryptocurrency.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if check_if_special_user(update.effective_chat.id) is False:
            # pylint: disable=logging-fstring-interpolation
            logger.error(
                f" User {update.effective_chat.id}: without rights wants to buy"
            )
            await update.message.reply_text("❌ You don't have the rights to do this!")
            return

        if len(context.args) != 2:
            logger.error(" Usage: /buy <symbol> <amount>")
            await update.message.reply_text("❌ Usage: /buy <symbol> <amount>")
            return

        symbol = context.args[0].upper()
        try:
            amount = float(context.args[1])
        except ValueError:
            logger.error(" Invalid amount. Please provide a valid number.")
            await update.message.reply_text(
                "❌ Invalid amount. Please provide a valid number."
            )
            return

        data = self.get_crypto_data(symbol)
        if data:
            price = data["price"]
            total_cost = amount * price

            # pylint: disable=logging-fstring-interpolation
            logger.info(
                f" User {update.effective_chat.id} requested buy for {symbol} at ${price:.2f}, "
                f"total cost: ${total_cost:.2f}"
            )

            # Update portfolio and save transaction
            if self.update_portfolio(symbol, amount, price, "buy"):
                text = (
                    f"✅ <b>Buy Order Executed:</b>\n"
                    f"📈 <b>{amount} {symbol}</b> at <b>${price:.2f}</b> each\n"
                    f"💰 <b>Total Cost:</b> ${total_cost:.2f}\n"
                    f"🕒 <b>Timestamp:</b> {datetime.now(timezone.utc).
                    strftime('%Y-%m-%d %H:%M UTC')}"
                )
                await update.message.reply_text(text, parse_mode="HTML")
            else:
                await update.message.reply_text(
                    f"❌ Failed to update portfolio for {symbol}."
                )
        else:
            await update.message.reply_text(f"❌ Couldn't fetch data for {symbol}.")

    # Handle `/sell <symbol> <amount>` command
    async def sell(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /sell command to sell a specified amount of a cryptocurrency.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if check_if_special_user(update.effective_chat.id) is False:
            # pylint: disable=logging-fstring-interpolation
            logger.error(
                f" User {update.effective_chat.id}: without rights wants to sell"
            )
            await update.message.reply_text("❌ You don't have the rights to do this!")
            return

        if len(context.args) != 2:
            logger.error(" Usage: /sell <symbol> <amount>")
            await update.message.reply_text("❌ Usage: /sell <symbol> <amount>")
            return

        symbol = context.args[0].upper()
        try:
            amount = float(context.args[1])
        except ValueError:
            logger.error(" Invalid amount. Please provide a valid number.")
            await update.message.reply_text(
                "❌ Invalid amount. Please provide a valid number."
            )
            return

        data = self.get_crypto_data(symbol)
        if data:
            price = data["price"]
            total_value = amount * price

            # Update portfolio and save transaction
            if self.update_portfolio(symbol, amount, price, "sell"):
                text = (
                    f"✅ <b>Sell Order Executed:</b>\n"
                    f"📉 <b>{amount} {symbol}</b> at <b>${price:.2f}</b> each\n"
                    f"💰 <b>Total Value:</b> ${total_value:.2f}\n"
                    f"🕒 <b>Timestamp:</b> {datetime.now(timezone.utc).
                    strftime('%Y-%m-%d %H:%M UTC')}"
                )
                await update.message.reply_text(text, parse_mode="HTML")
            else:
                await update.message.reply_text(
                    f"❌ Failed to update portfolio for {symbol}."
                )
        else:
            await update.message.reply_text(f"❌ Couldn't fetch data for {symbol}.")

    async def list_keywords(self, update, keywords):
        """
        List all current keywords in the bot.
        Args:
            update (Update): The update object containing the message.
            keywords (list): The list of current keywords.
        """
        keywords_message = "📋 <b>Current keywords:</b>\n\n"
        logger.info("Number of keywords: %d", len(keywords))
        for key in keywords:
            keywords_message += f"🔹 <b>{key}</b>\n"

        await update.message.reply_text(keywords_message, parse_mode="HTML")

    async def keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /keyword command to add or remove keywords.
        Usage: /keyword <add/remove> <keyword>
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if check_if_special_user(update.effective_chat.id) is False:
            await update.message.reply_text("❌ You don't have the rigths to do this!")
            return

        if len(context.args) < 1:
            logger.error(" Usage: /keyword <add/remove/list> <keyword>")
            await update.message.reply_text(
                "❌ Usage: /keyword <add/remove/list> <keyword>"
            )
            return

        action = context.args[0].lower()

        logger.info(" Requested: %s", action)

        # Load existing keywords
        keywords = load_keyword_list()

        if action == "list":
            await self.list_keywords(update, keywords)

            return

        keyword = " ".join(context.args[1:]).strip()

        if len(context.args) < 2:
            logger.error(" Usage: /keyword <add/remove> <keyword>")
            await update.message.reply_text(
                "❌ Usage: /keyword <add/remove/list> <keyword>"
            )
            return

        if not keyword:
            logger.error(" Please provide a valid keyword.")
            await update.message.reply_text("❌ Please provide a valid keyword.")
            return

        if action == "add":
            if keyword in keywords:
                await update.message.reply_text(
                    f"ℹ️ The keyword '{keyword}' is already in the list."
                )
            else:
                keywords.append(keyword)
                save_keywords(keywords)
                await update.message.reply_text(f"✅ Added keyword: '{keyword}'.")

        elif action == "remove":
            if keyword in keywords:
                keywords.remove(keyword)
                save_keywords(keywords)
                await update.message.reply_text(f"✅ Removed keyword: '{keyword}'.")
            else:
                await update.message.reply_text(
                    f"ℹ️ The keyword '{keyword}' is not in the list."
                )

        else:
            logger.error(" Invalid action. Use 'add' or 'remove'.")
            await update.message.reply_text("❌ Invalid action. Use 'add' or 'remove'.")

    async def list_variables(self, update):
        """
        List all current variables in the bot.
        Args:
            update (Update): The update object containing the message.
        """
        variables = load_json()

        if not variables:
            await update.message.reply_text("ℹ️ No variables found.")
            return

        variables_message = "📋 <b>Current Variables:</b>\n\n"
        for key, value in variables.items():
            variables_message += f"🔹 <b>{key}</b>: `{value}`\n"

        await update.message.reply_text(variables_message, parse_mode="HTML")

    async def change_variable(self, update, context):
        """
        Change a global variable in the bot.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        variable_name = context.args[0].upper()
        new_value = " ".join(context.args[1:]).strip()

        # Try to convert to integer if the value is numeric
        if new_value.isdigit():
            new_value = int(new_value)

        # Handle special case for SEND_HOURS (list of integers)
        if variable_name == "SEND_HOURS":
            try:
                new_value = set(map(int, new_value.split(",")))
            except ValueError:
                logger.error(
                    " SEND_HOURS should be a list of numbers, e.g., '7,12,18,0'"
                )
                await update.message.reply_text(
                    "❌ SEND_HOURS should be a list of numbers, e.g., '7,12,18,0'"
                )
                return

        # Handle special case for cryptoCurrencies (list of strings)
        if variable_name == "CRYPTOCURRENCIES":
            new_value = new_value.split(",")

        # If it's not a numeric value or a list, assume it's a string
        if not isinstance(new_value, (int, set, list)):
            new_value = str(new_value)

        # Load existing variables
        variables = load_json()

        # Update the variable
        variables[variable_name] = new_value
        save_variables_json(variables)

        await update.message.reply_text(
            f"✅ Updated variable '{variable_name}' to '{new_value}'."
        )

    async def var(self, update, context):
        """
        Handle the /var command to modify or list global variables.
        Usage:
        - /var list: Show all variables.
        - /var <variable_name> <new_value>: Update a variable.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        if check_if_special_user(update.effective_chat.id) is False:
            await update.message.reply_text("❌ You don't have the rigths to do this!")
            return

        if not context.args:
            logger.error(" Usage: /var list OR /var <variable_name> <new_value>")
            await update.message.reply_text(
                "❌ Usage: /var list OR /var <variable_name> <new_value>"
            )
            return

        action = context.args[0].lower()

        if action == "list":
            await self.list_variables(update)
            return

        if len(context.args) < 2:
            logger.error(" Usage: /var <variable_name> <new_value>")
            await update.message.reply_text(
                "❌ Usage: /var <variable_name> <new_value>"
            )
            return

        await self.change_variable(update, context)

    # Handle `/help` command
    # pylint: disable=unused-argument
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles the /help command to provide a list of available commands and their usage.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        logger.info(" Requested: help")

        help_text = """
📢 <b>Crypto Bot Commands</b>:
/details <b>symbol</b> - Get full details (price, volume, market cap, % changes)
/top10 - Get the top 10 cryptos by market cap
/compare <b>symbol1</b> <b>symbol2</b> - Compare two cryptocurrencies
/convert <b>amount</b> <b>from symbol</b> <b>to symbol</b> - Convert cryptocurrency
/mcapchange <b>symbol</b> - Get market cap change in 24h
/roi <b>symbol</b> <b>initial investment</b> - Calculate ROI"""

        if check_if_special_user(update.effective_chat.id):
            help_text += """
/buy <b>symbol</b> <b>amount</b> - Buy a cryptocurrency
/sell <b>symbol</b> <b>amount</b> - Sell a cryptocurrency
/keyword <b>list</b> - Show all the available keywords
/keyword <b>add/remove</b> <b>keyword</b> - Add or remove a keyword for news filtering
/var list - Show all variables and their values
/var <b>variable name</b> <b>new value</b> - Update a variable"""

        help_text += """
/help - Show this help message
"""
        await update.message.reply_text(help_text, parse_mode="HTML")

    # Handle button presses
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handles button presses in the chat.
        Args:
            update (Update): The update object containing the message.
            context (ContextTypes.DEFAULT_TYPE): The context for the command.
        """
        text = update.message.text

        if text == "🚨 Help":
            await self.help_command(update, context)

    # Main function to start the bot
    def run_bot(self):
        """
        Initializes and runs the Telegram bot with command handlers.
        """
        variables = load_json()

        bot_token = variables.get("TELEGRAM_API_TOKEN_SLAVE", "")

        app = Application.builder().token(bot_token).build()

        # Add command handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("details", self.details))
        app.add_handler(CommandHandler("top10", self.top10))
        app.add_handler(CommandHandler("compare", self.compare))
        app.add_handler(CommandHandler("convert", self.convert))
        app.add_handler(CommandHandler("mcapchange", self.mcap_change))
        app.add_handler(CommandHandler("roi", self.roi))
        app.add_handler(CommandHandler("buy", self.buy))
        app.add_handler(CommandHandler("sell", self.sell))
        app.add_handler(CommandHandler("keyword", self.keyword))
        app.add_handler(CommandHandler("var", self.var))
        app.add_handler(CommandHandler("help", self.help_command))

        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_buttons)
        )

        # Start the bot
        logger.info(" Bot is running...")
        print("🤖 Bot is running...")
        app.run_polling()


if __name__ == "__main__":
    slave_bot = SlaveBot()

    slave_bot.run_bot()
