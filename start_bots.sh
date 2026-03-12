#!/bin/bash

# Wait for network
echo "Waiting for network..."
until ping -c1 api.telegram.org &>/dev/null 2>&1; do
    sleep 2
done
echo "Network is up!"

# Directory where your bots are located
BOT_DIR="/mnt/data/Crypto-Bot-Ecosystem"

# List of bot scripts
BOTS=(
    "./src/bots/crypto_price_alerts_bot.py"
    "./src/bots/market_update_bot.py"
    "./src/bots/my_slave_bot.py"
    "./src/bots/news_check_bot.py"
    "main.py"
)

# Function to start a bot in a detached screen session
start_bot() {
    local bot_script="$1"
    local bot_name=$(basename "${bot_script%.py}")
    screen -dmS "$bot_name" bash -c "cd $BOT_DIR && python3 $bot_script >> /mnt/Crypto_Bot_ecosystem/logs/${bot_name}.log 2>&1"
    echo "✅ Started $bot_name in a new screen session."
}

# Start all bots
for bot in "${BOTS[@]}"; do
    start_bot "$bot"
done

echo "🚀 All bots are now running in screen sessions!"