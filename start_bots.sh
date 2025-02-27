#!/bin/bash

# Directory where your bots are located
BOT_DIR="/home/sever/Crypto-Articles-Bots"

# List of bot scripts
BOTS=(
    "CryptoPriceAlertsBot.py"
    "CryptoValue.py"
    "MarketUpdateBot.py"
    "MySlaveBot.py"
    "NewsCheckBot.py"
)

# Function to start a bot in a detached screen session
start_bot() {
    local bot_script="$1"
    local bot_name="${bot_script%.py}"  # Remove .py extension for screen name
    screen -dmS "$bot_name" bash -c "cd $BOT_DIR && python3 $bot_script"
    echo "✅ Started $bot_name in a new screen session."
}

# Start all bots
for bot in "${BOTS[@]}"; do
    start_bot "$bot"
done

echo "🚀 All bots are now running in screen sessions!"
