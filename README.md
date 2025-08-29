# Crypto Bot Ecosystem

<div align="center">
  <img src="./assets/banner.svg" alt="Crypto Intelligence Bots" width="99%">
</div>

A comprehensive suite of intelligent Telegram bots for cryptocurrency trading, market analysis, and portfolio management.

---
## Note

If you’d like to receive news updates from this bot, please contact me directly.\
A self-registration method is currently being developed, so you’ll soon be able to subscribe on your own.

---

## Features

- Real-time cryptocurrency news with AI-powered summaries
- Advanced market analysis and price tracking
- Smart price alerts with technical indicators
- Portfolio management with P/L tracking and analytics
- Multi-bot architecture for specialized functionality

---

## Bot Overview

### 1. Crypto News Bot
Intelligent news aggregation and analysis from premium sources.
- **Article Sources:**
  - [crypto.news](https://crypto.news/)
  - [CoinTelegraph](https://cointelegraph.com/)
  - [Bitcoin Magazine](https://bitcoinmagazine.com/articles)
- **Key Features:**
  - AI-powered article summarization
  - Tag-based article search
  - Daily statistics reporting
  - Market sentiment analysis
  - Keyword-based news filtering
  - Real-time news updates

### 2. Crypto Market Value Bot
Comprehensive market tracking and portfolio management.
- **Core Features:**
  - Real-time market updates for selected coins
  - ETH gas fee tracking
  - Fear and Greed Index monitoring
  - Portfolio tracking (P/L, holdings, average buy price)
  - Visual analytics (P/L, holdings, averages)
  - AI-powered article summarization for market news

### 3. Crypto Alerts Bot
Smart notification system for market movements.
- **Alert Types:**
  - Price change notifications (1h, 24h, 7d, 30d)
  - RSI (Relative Strength Index) tracking 
  - Custom threshold alerts 
  - Real-time market movement detection

### 4. Slave Bot (Management Bot)
Central command center for advanced operations.
- **Management Tools:**
  - Detailed coin analysis 
  - Top 10 rankings and comparisons 
  - Currency conversion 
  - ROI calculator 
  - System configuration 
  - News bot keyword management

---

## Project Structure

```
Crypto-Articles-Bots/
├── src/
│   ├── bots/              # Bot implementations
│   ├── data_base/         # Database handlers
│   ├── handlers/          # Utility handlers 
│   ├── scrapers/          # News scrapers
│   └── utils/             # Helper functions
├── tests/                 # Test suite
├── config/                # Configuration files
├── scripts/               # Utility scripts
├── requirements.txt       # Production dependencies
├── dev_requirements.txt   # Development dependencies
└── start_bots.sh          # Bot startup script 
```

---

## Installation
### Prerequisites
Before installation, ensure you have:

| Requirement         | Version | Purpose                                           |
|---------------------|---------|---------------------------------------------------|
| Python              | 3.12+   | Programming language for the bots                 |
| Git                 | Latest  | Version control system for cloning the repository |
| Linux/Raspberry Pi  | Any     | Optional, for automated startup scripts           |
| Internet Connection | Stable  | Required for API calls and news scraping          |

### Api Keys Required
You'll need accounts and API keys for:
- **Telegram Bot API** - [BotFather Guide](https://core.telegram.org/bots#botfather)
- **CoinMarketCap API** - [Get API Key](https://coinmarketcap.com/api/) 
- **Etherscan API** - [Register Here](https://etherscan.io/apis) 
- **OpenAI API** - [OpenAI Platform](https://platform.openai.com/docs/api-reference)

### Quick Setup
```bash  
# 1. Clone the repository
git clone git@github.com:severmanolescu/Crypto-Articles-Bots.git
cd Crypto-Articles-Bots

# 2. Install dependencies
pip install -r requirements.txt

# Edit config/variables.json with your API keys
```

---

## Configuration
To run the bots, you need to configure the environment variables and API keys. The configuration file is located at `./config/variables.json`. This file contains all necessary API keys and settings for the bots to function correctly.
```json
{
  "CMC_API_KEY": "your_coinmarketcap_api_key", 
  "ETHERSCAN_API_KEY": "your_etherscan_api_key", 
  "TELEGRAM_API_TOKEN_SLAVE": "your_slave_bot_token", 
  "TELEGRAM_API_TOKEN_ARTICLES": "your_news_bot_token", 
  "TELEGRAM_API_TOKEN_VALUE": "your_market_bot_token", 
  "TELEGRAM_API_TOKEN_ALERTS": "your_alerts_bot_token", 
  "OPEN_AI_API": "open_ai_api_key", 
  "TELEGRAM_CHAT_ID_FULL_DETAILS": ["list_of_user_ids_full_details"], 
  "TELEGRAM_CHAT_ID_PARTIAL_DATA": ["list_of_user_ids_partial_data"], 
  "AI_ARTICLE_SUMMARY_PROMPT": "AI Prompt for summarizing articles",
  "AI_TODAY_SUMMARY_PROMPT": "AI Prompt for summarizing today's news"
}
```

### Configuration Options 

| Setting                           | Description                                     | Access Level                                                           |
|-----------------------------------|-------------------------------------------------|------------------------------------------------------------------------|
| **CMC_API_KEY**                   | API key for CoinMarketCap                       | Required for market data retrieval.                                    |
| **ETHERSCAN_API_KEY**             | API key for Etherscan                           | Required for blockchain data retrieval.                                |
| **OPEN_AI_API**                   | API key for OpenAI                              | Required for AI-powered features like article summarization.           |
| **TELEGRAM_API_TOKEN_SLAVE**      | Token for the Slave Bot                         | Required for management operations.                                    |
| **TELEGRAM_API_TOKEN_ARTICLES**   | Token for the News Bot                          | Required for news aggregation and summarization.                       |
| **TELEGRAM_API_TOKEN_VALUE**      | Token for the Market Value Bot                  | Required for market tracking and portfolio management.                 |
| **TELEGRAM_API_TOKEN_ALERTS**     | Token for the Alerts Bot                        | Required for price alerts and notifications.                           |
| **TELEGRAM_CHAT_ID_FULL_DETAILS** | Users with complete bot access                  | Full access to all commands and features.                              |
| **TELEGRAM_CHAT_ID_PARTIAL_DATA** | Users with limited bot access                   | Limited access to basic commands and features.                         |
| **AI_ARTICLE_SUMMARY_PROMPT**     | Customizable AI prompt for article summaries    | Used by the news bot to summarize articles in a specific language.     |
| **AI_TODAY_SUMMARY_PROMPT**       | Customizable AI prompt for daily news summaries | Used by the news bot to summarize today's news in a specific language. |


---

## Running the Bots
### Individual Startup
To run each bot individually, you can use the following commands:
```bash  
# News Bot
python ./src/bots/news_check_bot.py

# Market Bot  
python ./src/bots/market_update_bot.py

# Alerts Bot
python ./src/bots/crypto_price_alerts_bot.py

# Management Bot
python ./src/bots/my_slave_bot.py
```
### Automated Startup (Linux/Raspberry Pi)
To start all bots automatically, you can use the provided `start_bots.sh` script. This script will run all bots in the background.
```bash  
# Make script executable
chmod +x start_bots.sh

# Start all bots
./start_bots.sh
```
**Note: Update **BOT_DIR** in start_bots.sh to match your installation path.**

---

## Auto-Start on Boot (Linux/Raspberry Pi)
To ensure the bots start automatically on boot, you can add the `start_bots.sh` script to your crontab:
```bash
# Edit crontab
crontab -e

# Add this line (replace with your actual path)
@reboot /path/to/your/start_bots.sh
```

---

## Testing
Ensure everything works correctly with our test suite:

```bash  
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test category
pytest tests/test_bots.py
```
---

## Usage Examples
### Getting Started
Getting Started
- Add bots to Telegram using their respective tokens 
- Send **/start** to initialize each bot
- Use the buttons in the bot interface to use the features
- Use **/help** to see available commands

---

## Development
### Development Setup
```bash
# Install development dependencies
pip install -r dev_requirements.txt

# Run tests
pytest tests/

# Code formatting
black src/
isort src/

# Linting
pylint src/
```

---

## Planned Features
+ Forex news integration  
+ Web dashboard enhancements (please see: [trades_command_center](https://github.com/severmanolescu/trades_command_center))  
+ AI trading bots
+ Advanced analytics

---

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

---

## Contact 
For questions or support, please open an issue on GitHub.

---

⭐ Star this repository if you find it useful! \
Made with ❤️ for the crypto community.
