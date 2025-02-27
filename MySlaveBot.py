import os
import json
import requests

from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("My Slave Bot started")

from telegram import Update, ReplyKeyboardMarkup

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from sdk.CheckUsers import check_if_special_user
from sdk import LoadVariables as load_variables

# Persistent buttons for news commands
NEWS_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🚨 Help"]
    ],
    resize_keyboard=True,  # Makes the buttons smaller and fit better
    one_time_keyboard=False,  # Buttons stay visible after being clicked
)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Welcome to the News Bot! Use the buttons below to get started:",
        reply_markup=NEWS_KEYBOARD,
    )

# Function to fetch crypto data
def get_crypto_data(symbol):
    params = {"symbol": symbol.upper(), "convert": "USD"}

    variables = load_variables.load()

    cmc_url = variables.get('CMC_URL_QUOTES', '')
    cmc_api_key = variables.get('CMC_API_KEY', '')

    headers = {"X-CMC_PRO_API_KEY": cmc_api_key}

    response = requests.get(cmc_url, headers=headers, params=params)
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
def get_top_10():
    params = {"start": 1, "limit": 10, "convert": "USD"}
    variables = load_variables.load()

    cmc_top10_url = variables.get('CMC_TOP10_URL', '')
    cmc_api_key = variables.get('CMC_API_KEY', '')

    headers = {"X-CMC_PRO_API_KEY": cmc_api_key}

    response = requests.get(cmc_top10_url, headers=headers, params=params)
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

def get_ath_from_coingecko(symbol):
    """
    Fetch the all-time high price of a cryptocurrency from CoinGecko.
    :param symbol: The cryptocurrency symbol (e.g., "BTC").
    :return: The all-time high price in USD, or None if not found.
    """
    variables = load_variables.load()

    coingecko_url = variables.get('COINGECKO_URL', '')

    # Load the symbol-to-ID mapping
    symbol_to_id = load_variables.load_symbol_to_id()

    coin_id = symbol_to_id.get(symbol.upper())

    if not coin_id:
        return None  # Symbol not supported

    response = requests.get(f"{coingecko_url}/{coin_id}")
    data = response.json()

    if "market_data" in data:
        return data["market_data"]["ath"]["usd"]
    return None  # ATH not found

async def get_details(data, symbol):
    ath_price = get_ath_from_coingecko(symbol)

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
async def details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0] if context.args else "BTC"

    logger.error(f" User {update.effective_chat.id} "
                 f"requested details for {symbol}")

    data = get_crypto_data(symbol)

    logger.info(f" Requested: details {symbol}")

    message = f"📌 Crypto Details: {data['name']} ({symbol.upper()})\n"

    message += await get_details(data, symbol)

    await update.message.reply_text(message)

# Handle `/top10` command
async def top10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_top_10()

    logger.error(f" User {update.effective_chat.id} "
                 f"requested top 10")

    logger.info(f" Requested: top 10")

    await update.message.reply_text(text, parse_mode="Markdown")

# Handle `/compare <symbol1> <symbol2>` command
async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Please provide two cryptocurrency symbols to compare.")
        return

    symbol1, symbol2 = context.args
    data1, data2 = get_crypto_data(symbol1), get_crypto_data(symbol2)

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
def convert_crypto(amount, from_symbol, to_symbol):
    params = {"symbol": from_symbol.upper(), "convert": to_symbol.upper()}

    variables = load_variables.load()

    CMC_URL = variables.get('CMC_URL_QUOTES', '')
    CMC_API_KEY = variables.get('CMC_API_KEY', '')

    HEADERS = {"X-CMC_PRO_API_KEY": CMC_API_KEY}

    response = requests.get(CMC_URL, headers=HEADERS, params=params)
    data = response.json()

    if "data" in data and from_symbol.upper() in data["data"]:
        coin_data = data["data"][from_symbol.upper()]
        if to_symbol.upper() in coin_data["quote"]:
            conversion_rate = coin_data["quote"][to_symbol.upper()]["price"]
            converted_amount = amount * conversion_rate
            return converted_amount
    return None  # Conversion not possible

# Handle `/convert <amount> <from_symbol> <to_symbol>` command
async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    converted_amount = convert_crypto(amount, from_symbol, to_symbol)

    logger.info(f" Requested: convert {amount} {from_symbol} {to_symbol}")

    if converted_amount is not None:
        text = f"🔁 *Conversion Result:*\n{amount} {from_symbol.upper()} = {converted_amount:.2f} {to_symbol.upper()}"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        logger.error(f" Couldn't convert {from_symbol.upper()} to {to_symbol.upper()}.")
        await update.message.reply_text(f"❌ Couldn't convert {from_symbol.upper()} to {to_symbol.upper()}.")

# Handle `/mcap_change <symbol>` command
async def mcap_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        logger.error(f" Usage: /mcap_change <symbol>")
        await update.message.reply_text("❌ Usage: /mcap_change <symbol>")
        return

    symbol = context.args[0].upper()
    data = get_crypto_data(symbol)

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
async def roi(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    data = get_crypto_data(symbol)

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

# Function to update the portfolio
def update_portfolio(symbol, amount, action):
    """
    Update the portfolio based on a buy or sell transaction.
    :param symbol: The cryptocurrency symbol (e.g., "BTC").
    :param amount: The amount of the cryptocurrency to buy or sell.
    :param action: "buy" or "sell".
    """
    symbol = symbol.upper()

    # Load portfolio from file
    if not os.path.exists("ConfigurationFiles/portfolio.json"):
        portfolio = {}
    else:
        with open("ConfigurationFiles/portfolio.json", "r") as file:
            portfolio = json.load(file)

    if action == "buy":

        if symbol in portfolio:
            portfolio[symbol] += amount
        else:
            portfolio[symbol] = amount
    elif action == "sell":

        if symbol in portfolio:
            if portfolio[symbol] >= amount:
                portfolio[symbol] -= amount
                if portfolio[symbol] == 0:  # Remove symbol if amount reaches zero
                    del portfolio[symbol]
            else:
                logger.error(f" Not enough {symbol} to sell. Available: {portfolio[symbol]}, Requested: {amount}")
                print(f"❌ Not enough {symbol} to sell. Available: {portfolio[symbol]}, Requested: {amount}")
                return False
        else:
            logger.error(f" {symbol} not found in portfolio.")
            print(f"❌ {symbol} not found in portfolio.")
            return False
    else:
        logger.error(f" Invalid action: {action}. Use 'buy' or 'sell'.")
        print(f"❌ Invalid action: {action}. Use 'buy' or 'sell'.")
        return False

    # Save the updated portfolio to the file
    with open("ConfigurationFiles/portfolio.json", "w") as file:
        json.dump(portfolio, file, indent=4)
    return True

# Handle `/buy <symbol> <amount>` command
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if check_if_special_user(update.effective_chat.id) is False:
        logger.error(f" User {update.effective_chat.id}: without rigths "
                     f"wants to buy")
        await update.message.reply_text("❌ You don't have the rigths to do this!")
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

    data = get_crypto_data(symbol)
    if data:
        price = data['price']
        total_cost = amount * price

        logger.error(f" User {update.effective_chat.id} "
                     f"requested buy for {symbol} price {price} and total cost of {total_cost}")

        # Update the portfolio
        if update_portfolio(symbol, amount, "buy"):
            transaction = f"BUY {amount} {symbol} at ${price:.2f} each. Total Cost: ${total_cost:.2f}\n"

            # Save the transaction to a file
            with open("ConfigurationFiles/transactions.txt", "a") as file:
                file.write(transaction)

            text = f"✅ *Buy Order Executed:*\n{transaction}"
            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            logger.error(f" Failed to update portfolio for {symbol}.")
            await update.message.reply_text(f"❌ Failed to update portfolio for {symbol}.")
    else:
        logger.error(f" Couldn't fetch data for {symbol}.")
        await update.message.reply_text(f"❌ Couldn't fetch data for {symbol}.")

# Handle `/sell <symbol> <amount>` command
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if check_if_special_user(update.effective_chat.id) is False:
        logger.error(f" User {update.effective_chat.id}: without rigths "
                     f"wants to sell")
        await update.message.reply_text("❌ You don't have the rigths to do this!")
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

    data = get_crypto_data(symbol)
    if data:
        price = data['price']
        total_value = amount * price

        logger.error(f" User {update.effective_chat.id} "
                     f"requested sell for {symbol} price {price} and total cost of {total_value}")

        # Update the portfolio
        if update_portfolio(symbol, amount, "sell"):
            transaction = f"SELL {amount} {symbol} at ${price:.2f} each. Total Value: ${total_value:.2f}\n"

            # Save the transaction to a file
            with open("ConfigurationFiles/transactions.txt", "a") as file:
                file.write(transaction)

            text = f"✅ *Sell Order Executed:*\n{transaction}"
            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            logger.error(f" Failed to update portfolio for {symbol}.")
            await update.message.reply_text(f"❌ Failed to update portfolio for {symbol}.")
    else:
        logger.error(f" Couldn't fetch data for {symbol}.")
        await update.message.reply_text(f"❌ Couldn't fetch data for {symbol}.")

async def list_keywords(update, keywords):
    logger.info(f" User {update.effective_chat.id} "
                 f"requested keywords list")

    keywords_message = "📋 *Current keywords:*\n\n"
    for key in keywords:
        keywords_message += f"🔹 *{key}*\n"

    await update.message.reply_text(keywords_message, parse_mode="Markdown")

async def keyword(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    keywords = load_variables.load_keywords()

    if action == "list":
        await list_keywords(update, keywords)

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
            load_variables.save_keywords(keywords)
            await update.message.reply_text(f"✅ Added keyword: '{keyword}'.")

    elif action == "remove":
        if keyword in keywords:
            keywords.remove(keyword)
            load_variables.save_keywords(keywords)
            await update.message.reply_text(f"✅ Removed keyword: '{keyword}'.")
        else:
            await update.message.reply_text(f"ℹ️ The keyword '{keyword}' is not in the list.")

    else:
        logger.error(f" Invalid action. Use 'add' or 'remove'.")
        await update.message.reply_text("❌ Invalid action. Use 'add' or 'remove'.")

async def list_variables(update):
    logger.error(f" User {update.effective_chat.id} "
                 f"requested setvar list")

    variables = load_variables.load()

    if not variables:
        await update.message.reply_text("ℹ️ No variables found.")
        return

    variables_message = "📋 *Current Variables:*\n\n"
    for key, value in variables.items():
        variables_message += f"🔹 *{key}*: `{value}`\n"

    await update.message.reply_text(variables_message, parse_mode="Markdown")

async def change_variable(update, context):
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
    variables = load_variables.load()

    # Update the variable
    variables[variable_name] = new_value
    load_variables.save(variables)

    await update.message.reply_text(f"✅ Updated variable '{variable_name}' to '{new_value}'.")

async def setvar(update, context):
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
        await list_variables(update)
        return

    if len(context.args) < 2:
        logger.error(f" Usage: /setvar <variable_name> <new_value>")
        await update.message.reply_text("❌ Usage: /setvar <variable_name> <new_value>")
        return

    await change_variable(update, context)

# Handle `/help` command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    /setvar list - Show all variables and their values
    /setvar <variable name> <new value> - Update a variable"""

    help_text += """
    /help - Show this help message
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")


# Handle button presses
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    special_user = True

    if text == "🚨 Help":
        await help_command(update, context)

# Main function to start the bot
def main():
    variables = load_variables.load()

    bot_token = variables.get('BOT_TOKEN', '')

    app = Application.builder().token(bot_token).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("details", details))
    app.add_handler(CommandHandler("top10", top10))
    app.add_handler(CommandHandler("compare", compare))
    app.add_handler(CommandHandler("convert", convert))
    app.add_handler(CommandHandler("mcapchange", mcap_change))
    app.add_handler(CommandHandler("roi", roi))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("keyword", keyword))
    app.add_handler(CommandHandler("setvar", setvar))
    app.add_handler(CommandHandler("help", help_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    # Start the bot
    logger.info(f" Bot is running...")
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()