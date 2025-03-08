import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc

import ccxt
import time
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
        # Initialize ccxt Binance
        self.exchange = ccxt.binance()

    def _fetch_ohlcv_since(self, trading_pair, start_ms):
        """
        Helper: Iteratively fetch OHLCV data from 'start_ms' until now.
        Works around Binance's 1000-candle limit by paging results.

        :param trading_pair: e.g. "ETH/USDT"
        :param start_ms: integer (milliseconds) start timestamp
        :return: pd.DataFrame with [timestamp, open, high, low, close, volume, date (UTC)]
        """
        all_ohlcvs = []
        timeframe = "1d"

        current_since = start_ms

        while True:
            # Fetch up to 1000 daily candles
            ohlcv = self.exchange.fetch_ohlcv(
                trading_pair,
                timeframe=timeframe,
                since=current_since,
                limit=1000
            )

            if not ohlcv:
                # No more data returned
                break

            all_ohlcvs += ohlcv

            # If we got fewer than 1000, we've reached the end
            if len(ohlcv) < 1000:
                break

            # Otherwise, move 'current_since' to just beyond the last candle
            last_ts = ohlcv[-1][0]
            current_since = last_ts + 1

        if not all_ohlcvs:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcvs, columns=["timestamp", "open", "high", "low", "close", "volume"])
        # Convert to datetime
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df

    def fetch_historical_prices(self, symbol, earliest_date):
        """
        Fetch OHLCV data from 'earliest_date' up to now.
        If earliest_date is None or invalid, defaults to last 365 days.

        :param symbol: e.g. "ETH"
        :param earliest_date: datetime object for earliest trade date
        :return: pd.DataFrame with columns:
                 [timestamp, open, high, low, close, volume, date]
        """
        logger.info(f"Fetching historical prices for {symbol} from Binance ")
        print(f"Fetching historical prices for {symbol} from Binance ")

        # Convert symbol to CCXT format: "ETH" -> "ETH/USDT"
        trading_pair = f"{symbol.upper()}/USDT"

        # If you have no earliest_date, default to 1 year
        if earliest_date is None:
            earliest_date = datetime.now(timezone.utc) - timedelta(days=365)

        start_ms = self.exchange.parse8601(earliest_date.isoformat())

        try:
            df = self._fetch_ohlcv_since(trading_pair, start_ms)
            if df.empty:
                logger.error(f"No historical data found for {symbol} from {earliest_date} to now.")
                print(f"No historical data found for {symbol} from {earliest_date} to now.")

                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"Error fetching price data from Binance: {str(e)}")
            print(f"Error fetching price data from Binance: {str(e)}")
            return pd.DataFrame()

    async def plot_crypto_trades(self, symbol, update, transactions_file='ConfigurationFiles/transactions.json'):
        """
        Generate a crypto price candlestick chart with buy/sell points.
        It automatically checks if you have trades older than 1 year,
        and fetches all needed data from Binance.
        """
        # 1) Load transactions
        transactions = LoadVariables.load_transactions(transactions_file)
        if not transactions:
            logger.info(f"No transactions found for {symbol}")
            print(f"No transactions found for {symbol}")
            await update.message.reply_text("No transactions found.")
            return

        # 2) Filter for this symbol
        transaction_df = pd.DataFrame(transactions)
        transaction_df = transaction_df[transaction_df["symbol"] == symbol.upper()]

        if transaction_df.empty:
            logger.info(f"No transactions found for {symbol.upper()}!")
            print(f"No transactions found for {symbol.upper()}!")
            await update.message.reply_text(f"No transactions found for {symbol.upper()}!")
            return

        # 3) Compute average buy price using ALL historical transactions (regardless of date)
        buy_transactions_all = transaction_df[transaction_df["action"] == "BUY"]

        if not buy_transactions_all.empty:
            total_cost = (buy_transactions_all["price"] * buy_transactions_all["amount"]).sum()
            total_amount = buy_transactions_all["amount"].sum()
            avg_buy_price = total_cost / total_amount if total_amount > 0 else None
        else:
            avg_buy_price = None

        # 4) Convert transaction timestamps to datetime
        transaction_df["date"] = pd.to_datetime(transaction_df["timestamp"], utc=True)

        # 5) Identify the earliest transaction date
        earliest_trade_date = transaction_df["date"].min()

        # 6) Fetch historical OHLCV data from earliest trade date if it's older than 1 year,
        #    or from 1 year ago if no older trades exist.
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        if earliest_trade_date < one_year_ago:
            fetch_start_date = earliest_trade_date
        else:
            fetch_start_date = one_year_ago

        price_data = self.fetch_historical_prices(symbol, fetch_start_date)
        if price_data.empty:
            logger.info("No price data available.")
            print("No price data available.")
            await update.message.reply_text("No price data available.")
            return

        # 7) Filter the transaction_df to show only trades in the last "fetched" range
        #    (Earliest we have from the chart)
        last_data_date = price_data["date"].max()
        first_data_date = price_data["date"].min()
        transaction_df = transaction_df[(transaction_df["date"] >= first_data_date) &
                                        (transaction_df["date"] <= last_data_date)]

        # 8) Prepare data for candlestick_ohlc
        # Convert to numeric date for candlestick
        price_data["date_num"] = price_data["date"].apply(mdates.date2num)
        ohlc_data = price_data[["date_num", "open", "high", "low", "close"]].values.tolist()

        # Separate buy and sell for markers
        buy_transactions = transaction_df[transaction_df["action"] == "BUY"].copy()
        sell_transactions = transaction_df[transaction_df["action"] == "SELL"].copy()

        buy_transactions["date_num"] = buy_transactions["date"].apply(mdates.date2num)
        sell_transactions["date_num"] = sell_transactions["date"].apply(mdates.date2num)

        # 9) Plot the candlestick chart
        fig, ax = plt.subplots(figsize=(14, 7))

        candlestick_ohlc(
            ax,
            ohlc_data,
            width=0.6,
            colorup='green',
            colordown='red',
            alpha=0.8
        )

        # 10) Overlay buy/sell markers
        ax.scatter(
            buy_transactions["date_num"],
            buy_transactions["price"],
            marker="^",
            s=100,
            edgecolors='black',
            c="lime",
            label="Buy Points",
            zorder=3
        )
        ax.scatter(
            sell_transactions["date_num"],
            sell_transactions["price"],
            marker="v",
            s=100,
            edgecolors='black',
            c="crimson",
            label="Sell Points",
            zorder=3
        )

        # 11) Plot average buy price line
        if avg_buy_price:
            ax.axhline(
                y=avg_buy_price,
                linestyle="--",
                label=f"Avg Buy Price: ${avg_buy_price:.2f}",
                zorder=2,
                color="orange"
            )

        # Format date axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        ax.set_title(f"{symbol.upper()} Price Chart", fontsize=14, fontweight="bold")
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price (USDT)", fontsize=12)
        ax.legend(loc="best")

        plt.tight_layout()

        # Save the chart
        image_path = f"{symbol}_price_chart.png"
        plt.savefig(image_path, dpi=300)

        # Send to Telegram
        await send_telegram_message_update(f"📈 Plot for: #{symbol.upper()}", update)
        await send_plot_to_telegram(image_path, update)

        plt.close(fig)

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

        plt.title("Investment Performance", fontsize=14)

        # Save as high-quality PNG for Telegram
        telegram_plot_path = "./portfolio_history.png"
        plt.savefig(telegram_plot_path, dpi=150, bbox_inches='tight')

        await send_telegram_message_update("📈 Portfolio history plot: #history_plot", update)

        await send_plot_to_telegram(telegram_plot_path, update)

        plt.close()

    async def send_all_plots(self, update):
        # Plot multiple coins
        await self.plot_crypto_trades("ETH", update)
        await self.plot_crypto_trades("ARB", update)
        await self.plot_crypto_trades("FET", update)
        await self.plot_crypto_trades("ENA", update)
        await self.plot_crypto_trades("PEPE", update)
        await self.plot_crypto_trades("LDO", update)
        await self.plot_crypto_trades("SEI", update)
