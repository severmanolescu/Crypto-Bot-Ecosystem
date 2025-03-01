import requests

from datetime import datetime, timezone

from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("My Slave Bot started")

from telegram import Update, ReplyKeyboardMarkup

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk.LoadVariables import (
load_portfolio_from_file,
save_data_to_json_file,
save_transaction
)
from sdk.CheckUsers import check_if_special_user
from sdk import LoadVariables as LoadVariables

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Help"]
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)

class SlaveBot:
    def __init__(self):
        self.cmc_url = None
        self.cmc_top10_url = None
        self.coingecko_url = None
        self.headers = None

    def reload_the_data(self):
        variables = LoadVariables.load()

        self.cmc_url = variables.get('CMC_URL_QUOTES', '')
        self.cmc_top10_url = variables.get('CMC_TOP10_URL', '')

        self.coingecko_url = variables.get('COINGECKO_URL', '')

        cmc_api_key = variables.get('CMC_API_KEY', '')

        self.headers = {"X-CMC_PRO_API_KEY": cmc_api_key}

    # Command: /start
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 Welcome to the News Bot! Use the buttons below to get started:",
            reply_markup=NEWS_KEYBOARD,
        )

    # Function to fetch crypto data
    def get_crypto_data(self, symbol):
        params = {"symbol": symbol.upper(), "convert": "USD"}

        self.reload_the_data()

        response = requests.get(self.cmc_url, headers=self.headers, params=params)
        data = response.json()

        if "data" in data and symbol.upper() in data["data"]:
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
                "circulating_supply": coin_data["circulating_supply"]
            }
        return None  # Coin not found

    # Function to fetch top 10 cryptos
    def get_top_10(self):
        params = {"start": 1, "limit": 10, "convert": "USD"}

        self.reload_the_data()

        response = requests.get(self.cmc_top10_url, headers=self.headers, params=params)
        data = response.json()

        if "data" in data:
            top_10 = data["data"]
            result = "🚀 *Top 10 Cryptos by Market Cap:*\n\n"
            for coin in top_10:
                name = coin["name"]
                symbol = coin["symbol"]
                price = coin["quote"]["USD"]["price"]
                market_cap = coin["quote"]["USD"]["market_cap"]
                result += (f"🔹 *{name} ({symbol})*\n"
                           f"💰 Price: ${price:,.2f}\n"
                           f"🏦 Market Cap: ${market_cap:,.2f}\n\n")
            return result
        logger.error(f" Error fetching top 10 cryptocurrencies.")
        return "❌ Error fetching top 10 cryptocurrencies."

    def get_ath_from_coingecko(self, symbol):
        """
        Fetch the all-time high price of a cryptocurrency from CoinGecko.
        :param symbol: The cryptocurrency symbol (e.g., "BTC").
        :return: The all-time high price in USD, or None if not found.
        """
        self.reload_the_data()

        # Load the symbol-to-ID mapping
        symbol_to_id = LoadVariables.load_symbol_to_id()

        coin_id = symbol_to_id.get(symbol.upper())

        if not coin_id:
            return None  # Symbol not supported

        response = requests.get(f"{self.coingecko_url}/coins/{coin_id}")
        data = response.json()

        if "market_data" in data:
            return data["market_data"]["ath"]["usd"]
        return None  # ATH not found

    async def get_details(self, data, symbol):
        ath_price = self.get_ath_from_coingecko(symbol)

        if ath_price is not None:
            ath_message = ath_price
        else:
            ath_message = "Can't find ATH"

        if data:
            return  (f"💰 Price: ${data['price']:.2f}\n"
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
                    f"📅 30 Days: {data['change_30d']:.2f}%\n")
        else:
            logger.error(f" Couldn't fetch details for {symbol}.")
            return f"❌ Couldn't fetch details for {symbol}."

    # Handle `/details <symbol>` command
    async def details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol = context.args[0] if context.args else "BTC"

        logger.error(f" User {update.effective_chat.id} "
                     f"requested details for {symbol}")

        data = self.get_crypto_data(symbol)

        logger.info(f" Requested: details {symbol}")

        message = f"📌 Crypto Details: {data['name']} ({symbol.upper()})\n"

        message += await self.get_details(data, symbol)

        await update.message.reply_text(message)

    # Handle `/top10` command
    async def top10(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = self.get_top_10()

        logger.error(f" User {update.effective_chat.id} "
                     f"requested top 10")

        logger.info(f" Requested: top 10")

        await update.message.reply_text(text, parse_mode="Markdown")

    # Handle `/compare <symbol1> <symbol2>` command
    async def compare(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 2:
            await update.message.reply_text("❌ Please provide two cryptocurrency symbols to compare.")
            return

        symbol1, symbol2 = context.args
        data1, data2 = self.get_crypto_data(symbol1), self.get_crypto_data(symbol2)

        if data1 and data2:
            message = f"""
    📊 *Comparison: {symbol1.upper()} vs {symbol2.upper()}*
    
💰 *Price*:
- {symbol1.upper()}: ${data1["price"]:.2f}
- {symbol2.upper()}: ${data2["price"]:.2f}

🏦 *Market Cap*:
- {symbol1.upper()}: ${data1["market_cap"]:.2f}
- {symbol2.upper()}: ${data2["market_cap"]:.2f}

📈 *24h Change*:
- {symbol1.upper()}: {data1["change_24h"]:.2f}%
- {symbol2.upper()}: {data2["change_24h"]:.2f}%
"""

            print(message)  # To preview before sending via Telegram

            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Couldn't fetch data for one or both symbols.")

    # Function to convert cryptocurrency
    def convert_crypto(self, amount, from_symbol, to_symbol):
        self.reload_the_data()

        params = {"symbol": from_symbol.upper(), "convert": to_symbol.upper()}

        response = requests.get(self.cmc_url, headers=self.headers, params=params)
        data = response.json()

        if "data" in data and from_symbol.upper() in data["data"]:
            coin_data = data["data"][from_symbol.upper()]
            if to_symbol.upper() in coin_data["quote"]:
                conversion_rate = coin_data["quote"][to_symbol.upper()]["price"]
                converted_amount = amount * conversion_rate
                return converted_amount
        return None  # Conversion not possible

    # Handle `/convert <amount> <from_symbol> <to_symbol>` command
    async def convert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 3:
            logger.error(f" Usage: /convert <amount> <from symbol> <to symbol>")
            await update.message.reply_text("❌ Usage: /convert <amount> <from symbol> <to symbol>")
            return

        try:
            amount = float(context.args[0])
            from_symbol = context.args[1]
            to_symbol = context.args[2]

            logger.error(f" User {update.effective_chat.id} "
                         f"requested convert from {from_symbol} to {to_symbol} with amount {amount}")

        except ValueError:
            logger.error(f" Invalid amount. Please provide a valid number.")
            await update.message.reply_text("❌ Invalid amount. Please provide a valid number.")
            return

        converted_amount = self.convert_crypto(amount, from_symbol, to_symbol)

        logger.info(f" Requested: convert {amount} {from_symbol} {to_symbol}")

        if converted_amount is not None:
            text = f"🔁 *Conversion Result:*\n{amount} {from_symbol.upper()} = {converted_amount:.2f} {to_symbol.upper()}"
            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            logger.error(f" Couldn't convert {from_symbol.upper()} to {to_symbol.upper()}.")
            await update.message.reply_text(f"❌ Couldn't convert {from_symbol.upper()} to {to_symbol.upper()}.")

    # Handle `/mcap_change <symbol>` command
    async def mcap_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 1:
            logger.error(f" Usage: /mcap_change <symbol>")
            await update.message.reply_text("❌ Usage: /mcap_change <symbol>")
            return

        symbol = context.args[0].upper()
        data = self.get_crypto_data(symbol)

        logger.error(f" User {update.effective_chat.id} "
                     f"requested market cap change for {symbol}")

        logger.info(f" Requested: mcap change {symbol}")

        if data:
            change_24h = data["change_24h"]
            text = f"📊 *Market Cap Change for {symbol} (24h):* {change_24h:.2f}%"
            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            logger.error(f" Couldn't fetch market cap change for {symbol}.")
            await update.message.reply_text(f"❌ Couldn't fetch market cap change for {symbol}.")

    # Handle `/roi <symbol> <initial_investment>` command
    async def roi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) != 3:
            logger.error(f" Usage: /roi <symbol> <initial_investment> <initial_price>")
            await update.message.reply_text("❌ Usage: /roi <symbol> <initial_investment> <initial_price>")
            return

        symbol = context.args[0].upper()

        logger.info(f" Requested: roi {symbol}")

        try:
            initial_investment = float(context.args[1])
            initial_price = float(context.args[2])
        except ValueError:
            logger.error(f" Invalid input. Please provide valid numbers.")
            await update.message.reply_text("❌ Invalid input. Please provide valid numbers.")
            return

        logger.error(f" User {update.effective_chat.id} "
                     f"requested ROI for {symbol} with investment {initial_investment} "
                     f"and initial price {initial_price}")

        data = self.get_crypto_data(symbol)

        if data:
            current_price = data["price"]
            roi_percentage = ((current_price - initial_price) / initial_price) * 100
            current_value = (initial_investment / initial_price) * current_price

            text = f"""
    📈 *ROI for {symbol} with ${initial_investment:.2f} investment:*
    - Initial Price: ${initial_price:.2f}
    - Current Price: ${current_price:.2f}
    - Current Value: ${current_value:.2f}
    - ROI: {roi_percentage:.2f}%
    """
            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            logger.error(f" Couldn't fetch ROI data for {symbol}.")
            await update.message.reply_text(f"❌ Couldn't fetch ROI data for {symbol}.")

    def update_buy(self, portfolio, symbol, amount, price):
        """ Handles buying a cryptocurrency and updating the portfolio correctly. """
        if symbol in portfolio:
            current_quantity = portfolio[symbol]["quantity"]
            current_avg_price = portfolio[symbol]["average_price"]
            current_total_investment = portfolio[symbol]["total_investment"]

            # Weighted average price calculation
            new_quantity = current_quantity + amount
            new_avg_price = ((current_quantity * current_avg_price) + (amount * price)) / new_quantity
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
            "allocation_percentage": None  # To be calculated later
        }

    def update_sell(self, portfolio, symbol, amount, price):
        """ Handles selling a cryptocurrency, updating portfolio, and adding USDT balance. """
        if symbol not in portfolio or portfolio[symbol]["quantity"] < amount:
            logger.error(f"❌ Not enough {symbol} to sell. Available: {portfolio.get(symbol, {}).get('quantity', 0)}, Requested: {amount}")
            return False

        # Calculate value in USDT
        value_in_usdt = round(amount * price, 2)

        # Deduct from crypto balance
        portfolio[symbol]["quantity"] -= amount
        portfolio[symbol]["total_investment"] -= round(amount * portfolio[symbol]["average_price"], 2)

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
        :param symbol: The cryptocurrency symbol (e.g., "BTC").
        :param amount: The amount of the cryptocurrency to buy or sell.
        :param price: The price of the asset at the time of the transaction.
        :param action: "buy" or "sell".
        """
        symbol = symbol.upper()
        portfolio = load_portfolio_from_file()

        if action == "buy":
            self.update_buy(portfolio, symbol, amount, price)
        elif action == "sell":
            if not self.update_sell(portfolio, symbol, amount, price):
                return False
        else:
            logger.error(f"❌ Invalid action: {action}. Use 'buy' or 'sell'.")
            return False

        # Save updated portfolio and transaction
        save_data_to_json_file("ConfigurationFiles/portfolio.json", portfolio)

        save_transaction(symbol, action, amount, price)

        return True

    # Handle `/buy <symbol> <amount>` command
    async def buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if check_if_special_user(update.effective_chat.id) is False:
            logger.error(f" User {update.effective_chat.id}: without rights wants to buy")
            await update.message.reply_text("❌ You don't have the rights to do this!")
            return

        if len(context.args) != 2:
            logger.error(f" Usage: /buy <symbol> <amount>")
            await update.message.reply_text("❌ Usage: /buy <symbol> <amount>")
            return

        symbol = context.args[0].upper()
        try:
            amount = float(context.args[1])
        except ValueError:
            logger.error(f" Invalid amount. Please provide a valid number.")
            await update.message.reply_text("❌ Invalid amount. Please provide a valid number.")
            return

        data = self.get_crypto_data(symbol)
        if data:
            price = data['price']
            total_cost = amount * price

            logger.info(f" User {update.effective_chat.id} requested buy for {symbol} at ${price:.2f}, total cost: ${total_cost:.2f}")

            # Update portfolio and save transaction
            if self.update_portfolio(symbol, amount, price, "buy"):
                text = (
                    f"✅ *Buy Order Executed:*\n"
                    f"📈 *{amount} {symbol}* at *${price:.2f}* each\n"
                    f"💰 *Total Cost:* ${total_cost:.2f}\n"
                    f"🕒 *Timestamp:* {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                )
                await update.message.reply_text(text, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ Failed to update portfolio for {symbol}.")
        else:
            await update.message.reply_text(f"❌ Couldn't fetch data for {symbol}.")


    # Handle `/sell <symbol> <amount>` command
    async def sell(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if check_if_special_user(update.effective_chat.id) is False:
            logger.error(f" User {update.effective_chat.id}: without rights wants to sell")
            await update.message.reply_text("❌ You don't have the rights to do this!")
            return

        if len(context.args) != 2:
            logger.error(f" Usage: /sell <symbol> <amount>")
            await update.message.reply_text("❌ Usage: /sell <symbol> <amount>")
            return

        symbol = context.args[0].upper()
        try:
            amount = float(context.args[1])
        except ValueError:
            logger.error(f" Invalid amount. Please provide a valid number.")
            await update.message.reply_text("❌ Invalid amount. Please provide a valid number.")
            return

        data = self.get_crypto_data(symbol)
        if data:
            price = data['price']
            total_value = amount * price

            logger.info(f" User {update.effective_chat.id} requested sell for {symbol} at ${price:.2f}, total value: ${total_value:.2f}")
            print(f" User {update.effective_chat.id} requested sell for {symbol} at ${price:.2f}, total value: ${total_value:.2f}")

            # Update portfolio and save transaction
            if self.update_portfolio(symbol, amount, price, "sell"):
                text = (
                    f"✅ *Sell Order Executed:*\n"
                    f"📉 *{amount} {symbol}* at *${price:.2f}* each\n"
                    f"💰 *Total Value:* ${total_value:.2f}\n"
                    f"🕒 *Timestamp:* {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                )
                await update.message.reply_text(text, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ Failed to update portfolio for {symbol}.")
        else:
            await update.message.reply_text(f"❌ Couldn't fetch data for {symbol}.")

    async def list_keywords(self, update, keywords):
        logger.info(f" User {update.effective_chat.id} "
                     f"requested keywords list")

        keywords_message = "📋 *Current keywords:*\n\n"
        for key in keywords:
            keywords_message += f"🔹 *{key}*\n"

        await update.message.reply_text(keywords_message, parse_mode="Markdown")

    async def keyword(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /keyword command to add or remove keywords.
        Usage: /keyword <add/remove> <keyword>
        """
        if check_if_special_user(update.effective_chat.id) is False:
            logger.error(f" User {update.effective_chat.id}: without rigths "
                         f"wants to update the keywords")

            await update.message.reply_text("❌ You don't have the rigths to do this!")
            return

        if len(context.args) < 1:
            logger.error(f" Usage: /keyword <add/remove/list> <keyword>")
            await update.message.reply_text("❌ Usage: /keyword <add/remove/list> <keyword>")
            return

        action = context.args[0].lower()

        logger.info(f" Requested: {action}")

        # Load existing keywords
        keywords = LoadVariables.load_keywords()

        if action == "list":
            await self.list_keywords(update, keywords)

            return

        keyword = " ".join(context.args[1:]).strip()

        if len(context.args) < 2:
            logger.error(f" Usage: /keyword <add/remove> <keyword>")
            await update.message.reply_text("❌ Usage: /keyword <add/remove/list> <keyword>")
            return

        if not keyword:
            logger.error(f" Please provide a valid keyword.")
            await update.message.reply_text("❌ Please provide a valid keyword.")
            return

        if action == "add":
            if keyword in keywords:
                await update.message.reply_text(f"ℹ️ The keyword '{keyword}' is already in the list.")
            else:
                keywords.append(keyword)
                LoadVariables.save_keywords(keywords)
                await update.message.reply_text(f"✅ Added keyword: '{keyword}'.")

        elif action == "remove":
            if keyword in keywords:
                keywords.remove(keyword)
                LoadVariables.save_keywords(keywords)
                await update.message.reply_text(f"✅ Removed keyword: '{keyword}'.")
            else:
                await update.message.reply_text(f"ℹ️ The keyword '{keyword}' is not in the list.")

        else:
            logger.error(f" Invalid action. Use 'add' or 'remove'.")
            await update.message.reply_text("❌ Invalid action. Use 'add' or 'remove'.")

    async def list_variables(self, update):
        logger.error(f" User {update.effective_chat.id} "
                     f"requested setvar list")

        variables = LoadVariables.load()

        if not variables:
            await update.message.reply_text("ℹ️ No variables found.")
            return

        variables_message = "📋 *Current Variables:*\n\n"
        for key, value in variables.items():
            variables_message += f"🔹 *{key}*: `{value}`\n"

        await update.message.reply_text(variables_message, parse_mode="Markdown")

    async def change_variable(self, update, context):
        variable_name = context.args[0].upper()
        new_value = " ".join(context.args[1:]).strip()

        logger.error(f" User {update.effective_chat.id} "
                     f"requested setvar {variable_name}: {new_value}")
        # Try to convert to integer if the value is numeric
        if new_value.isdigit():
            new_value = int(new_value)

        # Handle special case for SEND_HOURS (list of integers)
        if variable_name == "SEND_HOURS":
            try:
                new_value = set(map(int, new_value.split(",")))
            except ValueError:
                logger.error(
                    f" SEND_HOURS should be a list of numbers, e.g., '7,12,18,0'")
                await update.message.reply_text("❌ SEND_HOURS should be a list of numbers, e.g., '7,12,18,0'")
                return

        # Handle special case for cryptoCurrencies (list of strings)
        if variable_name == "CRYPTOCURRENCIES":
            new_value = new_value.split(",")

        # If it's not a numeric value or a list, assume it's a string
        if not isinstance(new_value, (int, set, list)):
            new_value = str(new_value)

        # Load existing variables
        variables = LoadVariables.load()

        # Update the variable
        variables[variable_name] = new_value
        LoadVariables.save(variables)

        await update.message.reply_text(f"✅ Updated variable '{variable_name}' to '{new_value}'.")

    async def var(self, update, context):
        """
        Handle the /setvar command to modify or list global variables.
        Usage:
        - /setvar list: Show all variables.
        - /setvar <variable_name> <new_value>: Update a variable.
        """
        if check_if_special_user(update.effective_chat.id) is False:
            logger.error(f" User {update.effective_chat.id}: without rigths "
                         f"wants to update the variables")
            await update.message.reply_text("❌ You don't have the rigths to do this!")
            return

        if not context.args:
            logger.error(f" Usage: /setvar list OR /setvar <variable_name> <new_value>")
            await update.message.reply_text("❌ Usage: /setvar list OR /setvar <variable_name> <new_value>")
            return

        action = context.args[0].lower()

        if action == "list":
            await self.list_variables(update)
            return

        if len(context.args) < 2:
            logger.error(f" Usage: /setvar <variable_name> <new_value>")
            await update.message.reply_text("❌ Usage: /setvar <variable_name> <new_value>")
            return

        await self.change_variable(update, context)

    # Handle `/help` command
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.info(f" Requested: help")

        help_text = """
📢 *Crypto Bot Commands*:
/details <symbol> - Get full details (price, volume, market cap, % changes)
/top10 - Get the top 10 cryptos by market cap
/compare <symbol1> <symbol2> - Compare two cryptocurrencies
/convert <amount> <from symbol> <to symbol> - Convert cryptocurrency
/mcapchange <symbol> - Get market cap change in 24h
/roi <symbol> <initial investment> - Calculate ROI"""

        if check_if_special_user(update.effective_chat.id):
            help_text += """
/buy <symbol> <amount> - Buy a cryptocurrency
/sell <symbol> <amount> - Sell a cryptocurrency
/keyword <list> - Show all the available keywords
/keyword <add/remove> <keyword> - Add or remove a keyword for news filtering
/var list - Show all variables and their values
/var <variable name> <new value> - Update a variable"""

        help_text += """
/help - Show this help message
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")


    # Handle button presses
    async def handle_buttons(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text

        special_user = True

        if text == "🚨 Help":
            await self.help_command(update, context)

    # Main function to start the bot
    def run_bot(self):
        variables = LoadVariables.load()

        bot_token = variables.get('TELEGRAM_API_TOKEN_SLAVE', '')

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

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_buttons))

        # Start the bot
        logger.info(f" Bot is running...")
        print("🤖 Bot is running...")
        app.run_polling()

if __name__ == "__main__":
    slave_bot = SlaveBot()

    slave_bot.run_bot()
