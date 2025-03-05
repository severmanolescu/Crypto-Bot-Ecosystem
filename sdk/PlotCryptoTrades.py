import matplotlib.pyplot as plt
import pandas as pd
import requests
import matplotlib.dates as mdates

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

        try:
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
        except Exception as e:
            logger.error("Error during getting historical prices")
            print("Error during getting historical prices")
            pd.DataFrame()

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

        await send_telegram_message_update(f"📈 Plot for: #{symbol.upper()}", update)

        await send_plot_to_telegram(image_path, update)
        plt.close()

    async def send_portfolio_history_plot(self, update, portfolio_history_file='./ConfigurationFiles/portfolio_history.json'):
        data = LoadVariables.load(portfolio_history_file)

        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Apply rolling mean to smooth fluctuations (window size 3)
        numeric_cols = ['total_value', 'total_investment', 'profit_loss', 'profit_loss_percentage']
        df_smoothed = df.copy()
        df_smoothed[numeric_cols] = df[numeric_cols].rolling(window=3, min_periods=1).mean()

        # Plot - Adjust size for Telegram
        fig, ax1 = plt.subplots(figsize=(10, 5), dpi=150)

        # Plot the main values with markers
        ax1.plot(df_smoothed['datetime'], df_smoothed['total_value'], marker='o', label="Total Value", color='b',
                 alpha=0.7)
        ax1.plot(df_smoothed['datetime'], df_smoothed['total_investment'], marker='s', label="Total Investment",
                 color='g', alpha=0.7)
        ax1.plot(df_smoothed['datetime'], df_smoothed['profit_loss'], marker='^', label="Profit/Loss", color='r',
                 alpha=0.7)

        # Add labels to some points (reduce clutter for Telegram)
        for i in range(0, len(df_smoothed), max(1, len(df_smoothed) // 6)):
            ax1.text(df_smoothed['datetime'][i], df_smoothed['total_value'][i], f"{df_smoothed['total_value'][i]:,.0f}",
                     fontsize=10, color='b', ha='right')
            ax1.text(df_smoothed['datetime'][i], df_smoothed['profit_loss'][i], f"{df_smoothed['profit_loss'][i]:,.0f}",
                     fontsize=10, color='r', ha='right')

        ax1.set_xlabel("DateTime", fontsize=12)
        ax1.set_ylabel("Value ($)", fontsize=12)
        ax1.legend(loc="upper left", fontsize=10)

        # Improve X-axis formatting
        ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        plt.xticks(rotation=45, fontsize=10)

        # Secondary y-axis for profit_loss_percentage
        ax2 = ax1.twinx()
        ax2.plot(df_smoothed['datetime'], df_smoothed['profit_loss_percentage'], marker='d', linestyle='dashed',
                 color='purple', label="Profit/Loss %", alpha=0.7)

        # Add labels for profit_loss_percentage
        for i in range(0, len(df_smoothed), max(1, len(df_smoothed) // 6)):
            ax2.text(df_smoothed['datetime'][i], df_smoothed['profit_loss_percentage'][i],
                     f"{df_smoothed['profit_loss_percentage'][i]:.1f}%", fontsize=10, color='purple', ha='left')

        ax2.set_ylabel("Profit/Loss %", fontsize=12)
        ax2.legend(loc="upper right", fontsize=10)

        plt.title("Investment Performance (Telegram Optimized)", fontsize=14)

        # Save as high-quality PNG for Telegram
        telegram_plot_path = "./portfolio_history.png"
        plt.savefig(telegram_plot_path, dpi=150, bbox_inches='tight')

        await send_plot_to_telegram(telegram_plot_path, update)

        # Show plot
        #plt.show()
    async def send_all_plots(self, update):
        await self.plot_crypto_trades("ETH", update)
        await self.plot_crypto_trades("ARB", update)
        await self.plot_crypto_trades("FET", update)
        await self.plot_crypto_trades("ENA", update)
        await self.plot_crypto_trades("PEPE", update)
        await self.plot_crypto_trades("LDO", update)
        await self.plot_crypto_trades("SEI", update)
