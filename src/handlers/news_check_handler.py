"""
News Check Module
This module is responsible for scraping cryptocurrency news articles from various sources,
notifying via Telegram, and optionally generating summaries using OpenAI.
"""

import asyncio
import logging
from datetime import datetime

import cloudscraper
import requests
from bs4 import BeautifulSoup

import src.handlers.load_variables_handler

# Import your SDK modules
from src.data_base.data_base_handler import DataBaseHandler
from src.handlers.open_ai_prompt_handler import OpenAIPrompt
from src.handlers.send_telegram_message import TelegramMessagesHandler
from src.scrapers.bitcoin_magazine_scraper import BitcoinMagazineScraper
from src.scrapers.cointelegraph_scraper import CoinTelegraphScraper

# Import scrapers
from src.scrapers.crypto_news_scraper import CryptoNewsScraper
from src.scrapers.data_extractor import DataExtractor

# Set up logging
logger = logging.getLogger(__name__)
logger.info("News Check started")


# pylint: disable=too-many-instance-attributes
class CryptoNewsCheck:
    """
    CryptoNewsCheck orchestrates the scraping of cryptocurrency news articles
    from various sources, stores them in a database, and sends notifications via Telegram.
    """

    def __init__(self, db_path="./data_bases/articles.db"):
        """
        Main orchestrator for scraping and notifying about new articles.
        """
        # Telegram/AI summary settings
        self.send_ai_summary = None
        self.open_ai_prompt = None
        self.keywords = None
        self.telegram_not_important_chat_id = None
        self.telegram_important_chat_id = None
        self.telegram_api_token = None

        # Database handler (see src/data_base_handler.py)
        self.data_base = DataBaseHandler(db_path)

        # URLs for different news sources
        self.urls = {
            "crypto.news": "https://crypto.news/",
            "cointelegraph": "https://cointelegraph.com/",
            "bitcoinmagazine": "https://bitcoinmagazine.com/articles",
        }

        # Create a cloudscraper instance for scraping
        self.scraper = cloudscraper.create_scraper()

        # Retry settings
        self.max_retries = 5

        self.telegram_message = TelegramMessagesHandler()

    def reload_the_data(self):
        """
        Reload environment variables, API tokens, and so forth.
        """
        variables = src.handlers.load_variables_handler.load()
        self.telegram_api_token = variables.get("TELEGRAM_API_TOKEN_ARTICLES", "")
        self.telegram_important_chat_id = variables.get(
            "TELEGRAM_CHAT_ID_FULL_DETAILS", []
        )
        self.telegram_not_important_chat_id = variables.get(
            "TELEGRAM_CHAT_ID_PARTIAL_DATA", []
        )
        self.keywords = src.handlers.load_variables_handler.load_keyword_list()

        open_ai_api = variables.get("OPEN_AI_API", "")
        self.open_ai_prompt = OpenAIPrompt(open_ai_api)
        self.send_ai_summary = variables.get("SEND_AI_SUMMARY", "")

        self.telegram_message.reload_the_data()

    async def fetch_page(self, url):
        """
        Fetch the page with retry logic and exponential backoff.
        Switch to `await asyncio.sleep(...)` for true async non-blocking retries.
        Args:
            url (str): The URL to fetch.
        """
        for attempt in range(1, self.max_retries + 1):
            delay = 2**attempt
            try:
                response = self.scraper.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text
                if response.status_code in [403, 429]:
                    logger.warning(
                        "Blocked or Rate Limited (Status %d)! "
                        "Retrying in %d seconds...",
                        response.status_code,
                        delay,
                    )
                    await asyncio.sleep(delay)  # non-blocking delay
                else:
                    logger.warning(
                        "Unexpected status code: %d. Retrying in %d s...",
                        response.status_code,
                        delay,
                    )
                    await asyncio.sleep(delay)
            except requests.exceptions.ConnectionError as e:
                logger.warning(
                    "Connection error: %s. Retrying in %d seconds...", e, delay
                )
                await asyncio.sleep(delay)
            except requests.exceptions.Timeout:
                logger.warning("Request timed out. Retrying in %s seconds...", delay)
                await asyncio.sleep(delay)
            except requests.exceptions.RequestException as e:
                logger.warning("Other request error: %s", e)
                break  # Stop retrying on other request errors

        logger.error("Max retries reached. Could not fetch %s.", url)
        return None

    def scrape_articles(self, soup, source):
        """
        Decide which scraper to use based on the 'source' string.
        Each scraper class is responsible for returning a list of:
          { "headline": ..., "link": ..., "highlights": ... }
        Args:
            soup (BeautifulSoup): The parsed HTML content of the page.
            source (str): The source identifier to choose the appropriate scraper.
        """
        data_extractor = DataExtractor(self.keywords)

        if source == "crypto.news":
            scraper = CryptoNewsScraper(data_extractor)
            return scraper.scrape(soup)

        if source == "cointelegraph":
            scraper = CoinTelegraphScraper(data_extractor)
            return scraper.scrape(soup)

        if source == "bitcoinmagazine":
            scraper = BitcoinMagazineScraper(data_extractor)
            return scraper.scrape(soup)

        return []

    async def generate_summary(self, link):
        """
        Generate article summary using OpenAI (if self.send_ai_summary is True).
        Args:
            link (str): The URL of the article to summarize.
        """
        return await self.open_ai_prompt.generate_summary(link)

    async def check_news(self, source, update=None):
        """
        Orchestrates the scraping and notification for a single source.
        Args:
            source (str): The source identifier (e.g., "crypto.news",
            "cointelegraph", "bitcoinmagazine").
            update: Optional parameter for Telegram updates.
        """
        found_articles = False

        page_content = await self.fetch_page(self.urls[source])
        if page_content:
            print(f"\n✅ Connected to {source} successfully!")
            logger.info("Connected to %s successfully!", source)
            soup = BeautifulSoup(page_content, "html.parser")
            articles = self.scrape_articles(soup, source)

            if articles:
                print(f"📰 Found {len(articles)} articles from {source}.")
                logger.info("Found %d articles from %s.", len(articles), source)

                for article in articles:
                    # Insert or ignore in DB
                    row_inserted = await self.data_base.save_article_to_db(
                        source,
                        article["headline"],
                        article["link"],
                        article["highlights"],
                    )

                    # If brand-new article, optionally generate summary and send message
                    if row_inserted == 1:
                        summary_text = ""
                        if self.send_ai_summary == "True":
                            summary_text = await self.generate_summary(article["link"])
                            # Store summary in DB
                            await self.data_base.update_article_summary_in_db(
                                article["link"], summary_text
                            )

                        # Build the Telegram message
                        if summary_text:
                            message = (
                                f"📰 <b>New Article Found!</b>\n"
                                f"📌 {article['headline']}\n"
                                f"🔗 {article['link']}\n"
                                f"🤖 {summary_text}\n"
                                f"🔍 Highlights: {article['highlights']}\n"
                            )
                        else:
                            message = (
                                f"📰 <b>New Article Found!</b>\n"
                                f"📌 {article['headline']}\n"
                                f"🔗 {article['link']}\n"
                                f"🔍 Highlights: {article['highlights']}\n"
                            )

                        found_articles = True

                        # Send Telegram message
                        await self.telegram_message.send_telegram_message(
                            message, self.telegram_api_token, update=update
                        )
                    else:
                        # Already in DB
                        logger.info("Skipping existing article: %s", article["link"])
            else:
                logger.warning("No new articles found for %s.", source)
        else:
            logger.error("Failed to fetch %s.", source)

        return found_articles

    async def send_today_summary(self):
        """
        Generate and send a daily summary of all articles published today.
        """
        if self.send_ai_summary == "True":
            articles = await self.data_base.fetch_todays_news()

            message = (
                f"Te rog genereaza raportul zilnic general. nu pentru fiecare articol, "
                f"folosind urmatoarele articole, "
                f"{datetime.now().date()}:\n"
            )

            for article in articles:
                message += article[2] + "\n"

            ai_message = await self.open_ai_prompt.get_response(
                message, max_tokens=2000
            )

            ai_message += "\n #DailyReport"

            await self.telegram_message.send_telegram_message(
                ai_message, self.telegram_api_token
            )

    async def recreate_data_base(self):
        """
        Recreate the database by dropping existing tables and initializing a new one.
        """
        await self.data_base.recreate_data_base()

    async def run_from_bot(self, update):
        """
        Run the news check from a Telegram bot command.
        Args:
            update: The Telegram update object containing the command context.
        """
        await self.data_base.init_db()  # Ensure DB is ready

        tasks = [
            self.check_news("crypto.news", update),
            self.check_news("cointelegraph", update),
            self.check_news("bitcoinmagazine", update),
        ]
        results = await asyncio.gather(*tasks)  # Run all scrapers in parallel

        if not any(results):
            await self.telegram_message.send_telegram_message(
                "❌ Didn't find any new article.",
                self.telegram_api_token,
                update=update,
            )

    async def run(self):
        """
        Run the news check for all sources without Telegram context.
        """
        await self.data_base.init_db()  # Ensure DB is ready

        tasks = [
            self.check_news("crypto.news"),
            self.check_news("cointelegraph"),
            self.check_news("bitcoinmagazine"),
        ]
        await asyncio.gather(*tasks)  # Run all scrapers in parallel
