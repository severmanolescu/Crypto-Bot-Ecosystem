import backtrader as bt
import requests
import datetime
import random
import csv
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


# 🚀 Fetch One Year of Historical Data from CoinGecko
def get_historical_data(symbol="bitcoin", currency="usd", days=365):
    """Fetch 1 year of daily historical prices from CoinGecko and convert to DataFrame."""
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {"vs_currency": currency, "days": days, "interval": "daily"}

    response = requests.get(url, params=params)
    data = response.json()

    if "prices" not in data:
        raise ValueError("Failed to fetch historical data.")

    df = pd.DataFrame(data["prices"], columns=["timestamp", "close"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Convert to Backtrader-compatible format (OHLCV)
    df["open"] = df["close"]
    df["high"] = df["close"]
    df["low"] = df["close"]
    df["volume"] = 0  # CoinGecko does not provide exact volume for daily data

    # Set DateTime as index
    df.set_index("datetime", inplace=True)
    df = df[["open", "high", "low", "close", "volume"]]

    return df


# 🚀 AI-Powered Dollar Cost Averaging (DCA) Strategy
class AI_DCA(bt.Strategy):
    params = (("dca_frequency", 7), ("investment_amount", 1000))

    def __init__(self):
        self.last_buy = None
        self.trade_log = []
        self.dates = []  # 🚀 Track all dates
        self.prices = []  # 🚀 Track all prices
        self.buy_dates = []
        self.buy_prices = []
        self.sell_dates = []  # 🚀 Track sell dates
        self.sell_prices = []  # 🚀 Track sell prices
        self.model = LogisticRegression()
        self.scaler = StandardScaler()
        self.train_ai_model()

    def train_ai_model(self):
        """Train AI model with better buy signals."""
        random.seed(42)

        market_trends = []
        labels = []

        for i in range(1, 1000):
            price = 40000 + random.uniform(-5000, 5000)
            ma_trend = random.uniform(0.9, 1.1)
            rsi = random.uniform(10, 90)
            macd = random.uniform(-5, 5)
            bollinger = random.uniform(0.8, 1.2)

            market_trends.append([price, ma_trend, rsi, macd, bollinger])

            # 🚀 New Buy Rule: Only Buy If RSI < 30 AND MACD > 0 (bullish momentum)
            buy_signal = 1 if (rsi < 30 and macd > 0) else 0

            labels.append(buy_signal)

        self.scaler.fit(market_trends)
        self.model.fit(self.scaler.transform(market_trends), labels)

    def next(self):
        """AI decides when to buy and sell, tracking both buy and sell points."""

        # 🚀 Store daily prices for plotting
        self.dates.append(self.datetime.date(0))
        self.prices.append(self.data.close[0])

        if self.last_buy and (self.datetime.date(0) - self.last_buy).days < self.params.dca_frequency:
            return  # Skip if not DCA time yet

        ma_trend = random.uniform(0.9, 1.1)
        rsi = random.uniform(10, 90)
        macd = random.uniform(-5, 5)
        bollinger = random.uniform(0.8, 1.2)

        market_data = [[self.data.close[0], ma_trend, rsi, macd, bollinger]]
        market_data_scaled = self.scaler.transform(market_data)

        buy_prob = self.model.predict_proba(market_data_scaled)[0][1]
        buy_signal = self.model.predict(market_data_scaled)[0]

        if buy_signal == 1:
            self.buy(size=self.params.investment_amount / self.data.close[0])
            self.last_buy = self.datetime.date(0)
            self.buy_dates.append(self.datetime.date(0))
            self.buy_prices.append(self.data.close[0])
            print(f"✅ AI DCA Buy: {self.data.close[0]} on {self.datetime.date(0)}")

        # 🚀 Sell Condition: AI Takes Profit If RSI > 80 (not 70)
        if rsi > 80 and self.position:
            self.sell(size=self.position.size * 0.25)  # Sell 50% of holdings
            self.sell_dates.append(self.datetime.date(0))
            self.sell_prices.append(self.data.close[0])
            print(f"💰 AI Took Profit at {self.data.close[0]} on {self.datetime.date(0)}")

    def stop(self):
        """Save trades to CSV, including buy and sell points."""

        with open("trades.csv", "w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["Date", "Type", "Price"])
            writer.writeheader()

            for date, price in zip(self.buy_dates, self.buy_prices):
                writer.writerow({"Date": date, "Type": "BUY", "Price": price})

            for date, price in zip(self.sell_dates, self.sell_prices):
                writer.writerow({"Date": date, "Type": "SELL", "Price": price})

        print("\n📁 Trades saved to trades.csv")

        # 🚀 Plot Results Manually
        plt.figure(figsize=(12, 6))
        plt.plot(self.dates, self.prices, label="Crypto Price", marker=".", markersize=3, linestyle="-", color="blue")

        # AI Buy Markers (Green)
        plt.scatter(self.buy_dates, self.buy_prices, color="green", label="AI DCA Buys", marker="o")

        # AI Sell Markers (Red)
        plt.scatter(self.sell_dates, self.sell_prices, color="red", label="AI Sells", marker="x")

        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.title("AI DCA - Buy & Sell Points")
        plt.legend()
        plt.grid()
        plt.xticks(rotation=45)
        plt.savefig("ai_dca_trades.png")  # Save as an image
        print("\n📊 Plot saved as ai_dca_trades.png")
        plt.show()


# 🚀 Standard DCA Strategy (Fixed Interval)
class Standard_DCA(bt.Strategy):
    params = (("dca_frequency", 7), ("investment_amount", 1000))

    def __init__(self):
        self.last_buy = None
        self.buy_dates = []
        self.buy_prices = []

    def next(self):
        """Buys every fixed interval (e.g., every 7 days)."""
        if self.last_buy is None or (self.datetime.date(0) - self.last_buy).days >= self.params.dca_frequency:
            self.buy(size=self.params.investment_amount / self.data.close[0])
            self.last_buy = self.datetime.date(0)
            self.buy_dates.append(self.datetime.date(0))
            self.buy_prices.append(self.data.close[0])
            #print(f"📅 Standard DCA Buy: {self.data.close[0]} on {self.datetime.date(0)}")

    def stop(self):
        """Print total trades for debugging."""
        total_trades = len(self.buy_prices)
        avg_buy_price = sum(self.buy_prices) / total_trades if total_trades > 0 else 0
        print(f"\n📊 {self.__class__.__name__} Total Buys: {total_trades} | Avg Buy Price: ${avg_buy_price:.2f}")


# Fetch 1 year of historical data
print("🔄 Fetching 1 year of historical data from CoinGecko...")
historical_data = get_historical_data(symbol="bitcoin", days=365)

# 🚀 Create Two Separate Cerebro Instances for Independent Brokers
cerebro_ai = bt.Cerebro()
cerebro_std = bt.Cerebro()

data_feed = bt.feeds.PandasData(dataname=historical_data)

# 🚀 Set up separate brokers for each strategy
broker_ai = bt.brokers.BackBroker()
broker_std = bt.brokers.BackBroker()

cerebro_ai.broker = broker_ai
cerebro_std.broker = broker_std

cerebro_ai.adddata(data_feed)
cerebro_std.adddata(data_feed)

# 🚀 Run AI DCA Strategy in Its Own Broker
cerebro_ai.addstrategy(AI_DCA)
ai_results = cerebro_ai.run()

# 🚀 Run Standard DCA Strategy in Its Own Broker
cerebro_std.addstrategy(Standard_DCA)
std_results = cerebro_std.run()

# 🚀 Get AI and Standard DCA Portfolio Values Separately
ai_final_value = cerebro_ai.broker.getvalue()
std_final_value = cerebro_std.broker.getvalue()

# 🚀 Print Performance Comparison
print("\n📊 **Performance Comparison**")
print(f"AI DCA Final Portfolio Value: ${ai_final_value:.2f}")
print(f"Standard DCA Final Portfolio Value: ${std_final_value:.2f}")

# 🚀 Check if AI Actually Bought Anything
if ai_final_value == 10000:
    print("⚠️ AI did NOT execute any trades! Check model settings.")


# Extract buy dates and prices from each strategy
ai_strategy = ai_results[0]  # AI DCA strategy instance
std_strategy = std_results[0]  # Standard DCA strategy instance

# 🚀 Plot AI DCA vs. Standard DCA Buy Points
plt.figure(figsize=(12, 6))
plt.plot(historical_data.index, historical_data["close"], label="BTC Price", color="blue")

# AI Buy Markers (Green)
plt.scatter(ai_strategy.buy_dates, ai_strategy.buy_prices, color="green", label="AI DCA Buys", marker="o")

# Standard DCA Buy Markers (Red)
plt.scatter(std_strategy.buy_dates, std_strategy.buy_prices, color="red", label="Standard DCA Buys", marker="x")

plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.title("AI DCA vs. Standard DCA - Buy Points Comparison")
plt.legend()
plt.grid()
plt.xticks(rotation=45)
plt.savefig("dca_comparison.png")
print("\n📊 Plot saved as dca_comparison.png")
plt.show()

