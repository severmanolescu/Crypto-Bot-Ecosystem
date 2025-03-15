# scrapers/crypto_news_scraper.py

from bs4 import BeautifulSoup

class CryptoNewsScraper:
    """
    Handles scraping for the https://crypto.news/ website.
    """

    def __init__(self, keywords):
        """
        :param keywords: List of strings that we want to check for in article headlines
        """
        self.keywords = keywords

    def contains_keywords(self, headline):
        """Check if the headline contains any of the specified keywords."""
        headline_lower = headline.lower()
        return any(keyword.lower() in headline_lower for keyword in self.keywords)

    def extract_highlights(self, headline):
        """Return #hashtags for each matched keyword in the headline."""
        headline_lower = headline.lower()
        found_keywords = [
            f"#{keyword.replace(' ', '')}"
            for keyword in self.keywords
            if keyword.lower() in headline_lower
        ]
        return ' '.join(found_keywords) if found_keywords else "#GeneralNews"

    def scrape(self, soup: BeautifulSoup):
        """
        Scrape articles from Crypto News (https://crypto.news/).
        :param soup: BeautifulSoup object of the page
        :return: list of dicts, each with {headline, link, highlights}
        """
        articles = []

        # Find all article containers
        post_loop_articles = soup.find_all("div", class_="post-loop")
        for article in post_loop_articles:
            headline_tag = article.find("p", class_="post-loop__title")
            link_tag = article.find("a", class_="post-loop__link", href=True)

            if headline_tag and link_tag:
                headline_text = headline_tag.text.strip()
                link_url = link_tag["href"].strip()

                if self.contains_keywords(headline_text):
                    highlights = self.extract_highlights(headline_text)
                    articles.append({
                        "headline": headline_text,
                        "link": link_url,
                        "highlights": highlights
                    })

        return articles
