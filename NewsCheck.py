import json
import os
import time
import logging
import requests
import cloudscraper

from datetime import datetime
from bs4 import BeautifulSoup

from sdk.OpenAIPrompt import OpenAIPrompt

from sdk import SendTelegramMessage as message_handler
from sdk import LoadVariables as load_variables

logger = logging.getLogger("NewsCheck.py")

logging.basicConfig(filename='./log.log', level=logging.INFO)
logger.info(f' Started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}!')

class CryptoNewsCheck:
    def __init__(self):
        # URLs for both sites
        self.send_ai_summary = None
        self.openAIPrompt = None
        self.keywords = None
        self.telegram_not_important_chat_id = None
        self.telegram_important_chat_id = None
        self.telegram_api_token = None
        self.urls = {
            "crypto.news": "https://crypto.news/",
            "cointelegraph": "https://cointelegraph.com/",
            "bitcoinmagazine": "https://bitcoinmagazine.com/articles"
        }

        # Create a scraper instance
        self.scraper = cloudscraper.create_scraper()

        # Files to track scraped articles
        self.scraped_articles_files = {
            "crypto.news": "./ConfigurationFiles/scraped_articles_cryptonews.json",
            "cointelegraph": "./ConfigurationFiles/scraped_articles_cointelegraph.json",
            "bitcoinmagazine": "./ConfigurationFiles/scraped_articles_bitcoinmagazine.json"
        }
        self.scraped_articles = {
            "crypto.news": set(),
            "cointelegraph": set(),
            "bitcoinmagazine": set()
        }

        # Retry settings
        self.max_retries = 5
        self.retry_delay = 5

    def reload_the_data(self):
        variables = load_variables.load()

        self.telegram_api_token = variables.get("TELEGRAM_API_TOKEN_ARTICLES", "")
        self.telegram_important_chat_id = variables.get("TELEGRAM_CHAT_ID_FULL_DETAILS", [])
        self.telegram_not_important_chat_id = variables.get("TELEGRAM_CHAT_ID_PARTIAL_DATA", [])

        self.keywords = load_variables.load_keyword_list()

        ope_ai_api = variables.get('OPEN_AI_API', '')

        self.openAIPrompt = OpenAIPrompt(ope_ai_api)

        self.send_ai_summary = variables.get("SEND_AI_SUMMARY", "")
        
    def load_scraped_file(self, source):
        """Load previously scraped articles."""
        if os.path.exists(self.scraped_articles_files[source]):
            with open(self.scraped_articles_files[source], "r") as file:
                self.scraped_articles[source] = set(json.load(file))
        else:
            self.scraped_articles[source] = set()

    def contains_keywords(self, headline):
        """Check if the headline contains any of the specified keywords."""
        headline_lower = headline.lower()
        return any(keyword.lower() in headline_lower for keyword in self.keywords)

    async def fetch_page(self, url):
        """Fetch the page with retry logic."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.scraper.get(url, timeout=10)

                if response.status_code == 200:
                    return response.text

                elif response.status_code in [403, 429]:  # Blocked or Rate Limited
                    logger.warning(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Blocked or Rate Limited (Status {response.status_code})! Retrying in {self.retry_delay} seconds...")
                    print(f"\n\n⚠️ Blocked or Rate Limited (Status {response.status_code})! Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

                else:
                    logger.warning(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Unexpected status code: {response.status_code}. Retrying...")
                    print(f"\n\n⚠️ Unexpected status code: {response.status_code}. Retrying...")
                    time.sleep(self.retry_delay)

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Connection error: {e}. Retrying in {self.retry_delay} seconds...")
                print(f"\n\n⚠️ Connection error: {e}. Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)

            except requests.exceptions.Timeout:
                logger.warning(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Request timed out. Retrying in 5 seconds...")
                print("\n\n⚠️ Request timed out. Retrying in 5 seconds...")
                time.sleep(self.retry_delay)

            except requests.exceptions.RequestException as e:
                logger.warning(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Other request error: {e}")
                print(f"\n\n⚠️ Other request error: {e}")
                break  # Stop retrying if it's another type of error

        logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Max retries reached. Could not fetch {url}.")
        print(f"\n\n❌ Max retries reached. Could not fetch {url}.")
        return None

    def scrape_articles(self, soup, source):
        """Scrape articles from either Crypto News, Cointelegraph, or Bitcoin Magazine."""
        if source == "crypto.news":
            return self.scrape_crypto_news(soup)
        elif source == "cointelegraph":
            return self.scrape_cointelegraph(soup)
        elif source == "bitcoinmagazine":
            return self.scrape_bitcoinmagazine(soup)
        return []

    def scrape_crypto_news(self, soup):
        """Scrape articles from Crypto News."""
        articles = []

        # Scrape articles from post-loop
        post_loop_articles = soup.find_all("div", class_="post-loop")
        for article in post_loop_articles:
            headline = article.find("p", class_="post-loop__title")
            link = article.find("a", class_="post-loop__link", href=True)

            if headline and link:
                headline_text = headline.text.strip()

                link_url = link["href"]

                headline_lower = headline_text.lower()
                found_keywords = [f"#{keyword.replace(' ', '')}" for keyword in self.keywords if
                                  keyword.lower() in headline_lower]

                if link_url not in self.scraped_articles["crypto.news"] and self.contains_keywords(headline_text):
                    articles.append({"headline": headline_text, "link": link_url, "highlights": found_keywords})
                    self.scraped_articles["crypto.news"].add(link_url)

        return articles

    def scrape_cointelegraph(self, soup):
        """Scrape articles from Cointelegraph."""
        articles = soup.find_all("article")
        return self.process_articles(articles, "cointelegraph")

    def scrape_bitcoinmagazine(self, soup):
        """Scrape articles from Bitcoin Magazine."""
        articles = soup.find_all("phoenix-card")
        return self.process_articles(articles, "bitcoinmagazine")

    def process_articles(self, articles, source, is_slider=False):
        """Process and filter articles for keywords."""
        new_articles = []
        for article in articles:
            headline = self.extract_headline(article, source, is_slider)
            link = self.extract_link(article, source, is_slider)

            if link and link not in self.scraped_articles[source] and self.contains_keywords(headline):
                highlights = self.extract_highlights(headline)
                new_articles.append({"headline": headline, "link": link, "highlights": highlights})

                self.scraped_articles[source].add(link)

        return new_articles

    def extract_highlights(self, headline):
        """Return highlights found in headline."""
        headline_lower = headline.lower()
        found_keywords = [f"#{keyword.replace(' ', '')}" for keyword in self.keywords if
                          keyword.lower() in headline_lower]
        return ' '.join(found_keywords) if found_keywords else "#GeneralNews"

    def extract_headline(self, article, source, is_slider=False):
        """Extract headline based on the source and article type."""
        if source == "crypto.news":
            if is_slider:
                # For home-opinion-slider__slide articles
                headline = article.find("h3", class_="home-opinion-slider__slide-title")
            else:
                # For post-loop articles
                headline = article.find("p", class_="post-loop__title")
            return headline.text.strip() if headline else "No headline found"
        elif source == "cointelegraph":
            headline = (
                    article.find("span", class_="post-card__title") or
                    article.find("h2", class_="post-card__title")
            )
            return headline.text.strip() if headline else "No headline found"
        elif source == "bitcoinmagazine":
            headline = article.find("h2", class_="m-ellipsis--text m-card--header-text")
            return headline.text.strip() if headline else "No headline found"
        return "No headline found"

    def extract_link(self, article, source, is_slider=False):
        """Extract link based on the source and article type."""
        if source == "crypto.news":
            if is_slider:
                # For home-opinion-slider__slide articles
                link = article.find("a", href=True)
            else:
                # For post-loop articles
                link = article.find("a", class_="post-loop__link", href=True)
            return link["href"] if link else None
        elif source == "cointelegraph":
            link = article.find("a", href=True)
            return f"https://cointelegraph.com{link['href']}" if link else None
        elif source == "bitcoinmagazine":
            link = article.find("a", href=True)
            return f"https://bitcoinmagazine.com{link['href']}" if link else None
        return None

    def delete_scraped_list(self, source):
        if os.path.exists(self.scraped_articles_files[source]):
            os.remove(self.scraped_articles_files[source])

    def save_scraped_list(self, source):
        """Save scraped articles to prevent duplicate notifications."""
        with open(self.scraped_articles_files[source], "w") as file:
            json.dump(list(self.scraped_articles[source]), file)

    async def generate_summary(self, link):
        """Generate article summary using OpenAI."""
        return await self.openAIPrompt.generate_summary(link)

    async def check_news(self, source):
        """Main function to scrape news from the given source and send articles."""
        url = self.urls[source]
        page_content = await self.fetch_page(url)

        if page_content:
            logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:  Connected to {source} successfully!")
            print(f"\n✅ Connected to {source} successfully!")
            self.load_scraped_file(source)

            soup = BeautifulSoup(page_content, "html.parser")
            articles = self.scrape_articles(soup, source)

            if articles:
                print(f"📰 Found {len(articles)} new articles!\n")

                for article in articles:
                    if self.send_ai_summary == "True":
                        message = (f"📰 New Article Found!\n"
                                   f"📌 {article['headline']}\n"
                                   f"🔗 {article['link']}\n"
                                   f"🤖 {await self.generate_summary(article['link'])}\n"
                                   f"🔍 Highlights: {article['highlights']}\n")

                    else:
                        message = (f"📰 New Article Found!\n"
                                   f"📌 {article['headline']}\n"
                                   f"🔗 {article['link']}\n"
                                   f"🔍 Highlights: {article['highlights']}\n")

                    await message_handler.send_telegram_message(message, self.telegram_api_token,
                                                                self.telegram_important_chat_id,
                                                                self.telegram_not_important_chat_id)

                self.save_scraped_list(source)
            else:
                logger.warning(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:  No new articles found from {source}!")
                print(f"😔 No new articles found from {source}!")
        else:
            logger.error(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:  Failed to fetch {source}.")
            print(f"❌ Failed to fetch {source}.")

    async def reload_the_news(self, source, user_id, special_user = False):
        self.delete_scraped_list(source)

        if special_user is False:
            self.telegram_important_chat_id = []
            self.telegram_not_important_chat_id = [user_id]

            self.send_ai_summary = False
        else:
            self.telegram_important_chat_id = [user_id]
            self.telegram_not_important_chat_id = []

        await self.check_news(source)

    async def run(self):
        """Run the scraper for both sources."""
        await self.check_news("crypto.news")
        await self.check_news("cointelegraph")
        await self.check_news("bitcoinmagazine")
