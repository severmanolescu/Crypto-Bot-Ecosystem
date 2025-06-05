"""
Scraper for Crypto News (https://crypto.news/).
This scraper extracts articles that contain specific keywords in their headlines.
"""

import re


class CryptoNewsScraper:
    """
    Handles scraping for the https://crypto.news/ website.
    """

    def __init__(self, keywords):
        """
        Initialize the scraper with a list of keywords.
        Args:
            keywords (list): List of keywords or phrases to search for in article headlines.
        """
        self.keywords = keywords

    def contains_keywords(self, headline):
        """
        Match only full words or phrases, allowing ending punctuation like . , ! ?
        Args:
            headline (str): The headline text to check for keywords.
        Returns:
            bool: True if any keyword is found in the headline, False otherwise.
        """
        headline_lower = headline.lower()

        for keyword in self.keywords:
            keyword_lower = keyword.lower()
            pattern = rf"\b{re.escape(keyword_lower)}\b[.,!?]?"
            if re.search(pattern, headline_lower):
                return True
        return False

    def extract_highlights(self, headline):
        """
        Return #hashtags for each matched keyword in the headline.
        Args:
            headline (str): The headline text to extract hashtags from.
        Returns:
            str: A string of hashtags corresponding to the matched keywords,
                 or "#GeneralNews" if no keywords are found.
        """
        headline_lower = headline.lower()
        found_keywords = [
            f"#{keyword.replace(' ', '')}"
            for keyword in self.keywords
            if keyword.lower() in headline_lower
        ]
        return " ".join(found_keywords) if found_keywords else "#GeneralNews"

    def scrape(self, soup):
        """
        Scrape articles from Crypto News (https://crypto.news/).
        Args:
            soup (BeautifulSoup): Parsed HTML content of the Crypto News page.
        Returns:
            list: A list of dictionaries containing article headlines, links, and highlights.
            Each dictionary has the structure:
            {
                "headline": str,
                "link": str,
                "highlights": str
            }
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
                    articles.append(
                        {
                            "headline": headline_text,
                            "link": link_url,
                            "highlights": highlights,
                        }
                    )

        return articles
