import matplotlib.pyplot as plt
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone

import sdk.LoadVariables as LoadVariables

from sdk.SendTelegramMessage import (
send_plot_to_telegram,
send_telegram_message_update
)

from sdk.Logger import setup_logger

logger = setup_logger("log.log")
logger.info("Market Update Bot started")

class PlotTrades:
    def __init__(self):
        self.coingecko_api_key = None
        self.coingecko_base_url = None

    def reload_the_data(self):
        variables = LoadVariables.load()

        self.coingecko_api_key = variables.get("COINGECKO_API_KEY", "")
        self.coingecko_base_url = variables.get("COINGECKO_URL", "")

    def fetch_historical_prices(self, symbol):
        """ Fetch historical price data from CoinGecko Free API (limited to 1 year). """
        logger.info(f"Fetching historical prices for {symbol}")
        print(f"Fetching historical prices for {symbol}")

        url = f"{self.coingecko_base_url}/coins/{symbol}/market_chart?vs_currency=usd&days=365&interval=daily"
        headers = {"x-cg-demo-api-key": self.coingecko_api_key} if self.coingecko_api_key else {}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            dates = [datetime.fromtimestamp(int(price[0] / 1000), tz=timezone.utc) for price in data['prices']]
            prices = [price[1] for price in data['prices']]
            return pd.DataFrame({'date': dates, 'price': prices})
        else:
            logger.error(f"Error fetching price data from CoinGecko: {response.text}")
            print(f"Error fetching price data from CoinGecko: {response.text}")
            return pd.DataFrame()

    async def plot_crypto_trades(self, symbol, update, transactions_file='ConfigurationFiles/transactions.json'):
        """ Generate a crypto price chart with buy/sell points and correct average buy price. """
        transactions = LoadVariables.load_transactions(transactions_file)
        if not transactions:
            logger.info(f"No transactions found for {symbol}")
            print(f"No transactions found for {symbol}")
            await update.message.reply_text("No transactions found.")
            return

        # Load all transactions (including older than 1 year)
        transaction_df = pd.DataFrame(transactions)
        transaction_df = transaction_df[transaction_df["symbol"] == symbol.upper()]

        if transaction_df.empty:
            logger.info(f"No transactions found for {symbol.upper()}!")
            print(f"No transactions found for {symbol.upper()}!")

            await update.message.reply_text(f"No transactions found for {symbol.upper()}!")
            return

        # Compute Average Buy Price using ALL historical transactions
        buy_transactions_all = transaction_df[transaction_df["action"] == "BUY"]

        if not buy_transactions_all.empty:
            total_cost = (buy_transactions_all["price"] * buy_transactions_all["amount"]).sum()
            total_amount = buy_transactions_all["amount"].sum()
            avg_buy_price = total_cost / total_amount if total_amount > 0 else None
        else:
            avg_buy_price = None

        # Now filter transactions only for the last 365 days for plotting
        transaction_df["date"] = pd.to_datetime(transaction_df["timestamp"], utc=True)
        latest_date = datetime.now(timezone.utc)
        earliest_allowed_date = latest_date - timedelta(days=365)
        transaction_df = transaction_df[transaction_df["date"] >= earliest_allowed_date]

        # Fetch historical prices (only the last 365 days due to API limits)
        symbol_to_id = LoadVariables.load_symbol_to_id()
        coin_id = symbol_to_id.get(symbol.upper())

        price_data = self.fetch_historical_prices(coin_id)
        if price_data.empty:
            logger.info("No price data available.")
            print("No price data available.")

            await update.message.reply_text("No price data available.")
            return

        # Filter buy and sell transactions (for plotting)
        buy_transactions = transaction_df[transaction_df["action"] == "BUY"]
        sell_transactions = transaction_df[transaction_df["action"] == "SELL"]

        # Plot price data with improved aesthetics
        plt.figure(figsize=(14, 7))
        plt.plot(price_data["date"], price_data["price"], label=f"{symbol.upper()} Price", color="royalblue",
                 linestyle="-", linewidth=1.5)

        # Plot buy points with enhanced visibility
        plt.scatter(buy_transactions["date"], buy_transactions["price"], color="limegreen", edgecolors="black",
                    marker="^",
                    s=200, label="Buy Points", zorder=3, linewidth=1.5)

        # Plot sell points with enhanced visibility
        plt.scatter(sell_transactions["date"], sell_transactions["price"], color="crimson", edgecolors="black",
                    marker="v",
                    s=200, label="Sell Points", zorder=3, linewidth=1.5)

        # Plot average buy price as a horizontal line (calculated from all transactions)
        if avg_buy_price:
            plt.axhline(y=avg_buy_price, color="orange", linestyle="--", linewidth=2,
                        label=f"Avg Buy Price: ${avg_buy_price:.2f}")

        # Labels and legend
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Price (USD)", fontsize=12)
        plt.title(f"{symbol.upper()} Price Chart with Buy & Sell Points (Last 365 Days)", fontsize=14,
                  fontweight="bold")
        plt.legend(fontsize=12, frameon=True, loc="best")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.xticks(rotation=45, fontsize=10)
        plt.yticks(fontsize=10)
        plt.tight_layout()

        # Save plot and send to Telegram
        image_path = f"{symbol}_price_chart.png"
        plt.savefig(image_path, dpi=300)

        await send_telegram_message_update(f"📈 Plot for: {symbol.upper()}", update)

        await send_plot_to_telegram(image_path, update)
        plt.close()

    async def send_all_plots(self, update):
        await self.plot_crypto_trades("ETH", update)
        await self.plot_crypto_trades("ARB", update)
        await self.plot_crypto_trades("FET", update)
        await self.plot_crypto_trades("ENA", update)
        await self.plot_crypto_trades("PEPE", update)
        await self.plot_crypto_trades("LDO", update)
        await self.plot_crypto_trades("SEI", update)