
# Crypto Telegram Bots

A suite of powerful Telegram bots providing real-time cryptocurrency news, market data, alerts, and portfolio management.

## Overview

This project consists of four specialized Telegram bots running on a Raspberry Pi 4, providing comprehensive cryptocurrency monitoring and management tools.

## Bots

### 1. Crypto News Bot
- **Article Sources:**
  - [crypto.news](https://crypto.news/)
  - [CoinTelegraph](https://cointelegraph.com/)
  - [Bitcoin Magazine](https://bitcoinmagazine.com/articles)
- **Features:**
  - AI-powered article summarization
  - Tag-based article search
  - Daily statistics reporting
  - Market sentiment analysis

### 2. Crypto Market Value Bot
- **Features:**
  - Real-time market updates for selected coins
  - ETH gas fee tracking
  - Fear and Greed Index monitoring
  - Portfolio tracking (P/L, holdings, average buy price)
  - Visual analytics (portfolio history, value trends, investment totals)
  - Trade visualization (buy/sell charts)

### 3. Crypto Alerts Bot
- **Features:**
  - Customizable price alerts (1h, 24h, 7d, 30d)
  - Notification system for market movements

### 4. Slave Bot (Management Bot)
- **Features:**
  - Detailed coin analysis
  - Top 10 coins ranking
  - Coin comparison tools
  - Currency conversion
  - 24h market cap change tracking
  - ROI calculator
  - Trade order management (buy/sell)
  - News bot keyword configuration
  - System variable management

## Project Structure
├── src/ \
│ ├── bots/ # Main bot implementations \
│ ├── data_base # Database handler \
│ ├── handlers/ # Utility handlers for various operations \
│ ├── scrapers/ # Scrapers for news pages \
│ ├── utils/ # Helper functions and utilities \
├── tests/ # Test suite \
├── config/ # Configuration files \
├── requirements.txt # Dependencies \
├── dev_requirements.txt # Development dependencies \
├── start_bots.sh # Script to start all bots

## Configuration
For the bots to work correctly, you need to set up the following in `config/variables.json`:
```json
{
	"CMC_API_KEY": "your_etherscan_api_key",
	"ETHERSCAN_API_KEY": "your_etherscan_api",
	"TELEGRAM_API_TOKEN_SLAVE": "your_slave_bot_token",
	"TELEGRAM_API_TOKEN_ARTICLES": "your_news_bot_token",
	"TELEGRAM_API_TOKEN_VALUE": "your_market_bot_token", 
	"TELEGRAM_API_TOKEN_ALERTS": "your_alerts_bot_token", 
	"OPEN_AI_API": "open_ai_api_ley",
	"TELEGRAM_CHAT_ID_FULL_DETAILS": ["list_of_user_ids_full_details"], 
	"TELEGRAM_CHAT_ID_PARTIAL_DATA": ["list_of_user_ids_partial_data"], 
	"COINMARKETCAP_API_KEY": "your_coinmarketcap_api_key"
}
```
<b>TELEGRAM_CHAT_ID_FULL_DETAILS</b> - List of user IDs who will receive full details from the bots and can use all commands.

<b>TELEGRAM_CHAT_ID_PARTIAL_DATA</b> - List of user IDs who will receive partial data from the bots and can use only a limited set of commands.

## Prerequisites

 - Python 3.12+ 
 - Telegram Bot API access (see [BotFather](https://core.telegram.org/bots#botfather) for more details)
 - CoinMarketCap API key (see [CoinMarketCap](https://coinmarketcap.com/api/) for more details)
 - EtherscanAPI key (see [Etherscan](https://etherscan.io/apis) for more details)
 - OpenAI API key (see [OpenAI](https://platform.openai.com/docs/api-reference) for more details)
 - SQLite (or any other database) for data storage

## Installation
### Clone the repository  
```bash  
git clone git@github.com:severmanolescu/Crypto-Articles-Bots.git  
cd Crypto-Articles-Bots
```
### Install Dependencies
```bash  
pip install -r requirements.txt
```
or
```bash  
py -m pip install -r requirements.txt
```
### Configuration
Update the config/variables.json file with your API keys and settings 

## Running the Bots
### Individual Startup
Run each bot separately:
```bash  
py src/bots/market_update_bot.py  
py src/bots/news_check_bot.py  
py src/bots/crypto_price_alerts_bot.py  
py src/bots/my_slave_bot.py
```
### Automated Startup (Linux/Raspberry Pi)
```bash  
# Update BOT_DIR in the script to your directory  
chmod +x start_bots.sh  
./start_bots.sh
```
## Running Tests:
To run the test suite:
```bash  
pytest tests/
```
or
```bash  
py -m pytest ./tests/
```

### Planned Features  
+ Forex news integration  
+ Web dashboard enhancements (please see: [trades_command_center](https://github.com/severmanolescu/trades_command_center))  
+ AI trading bots

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

### Contact 
For questions or support, please open an issue on GitHub.