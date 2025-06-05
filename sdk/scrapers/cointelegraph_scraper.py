"""
Scraper for Cointelegraph (https://cointelegraph.com/).
This scraper extracts articles that contain specific keywords in their headlines.
"""

import re


class CointelegraphScraper:
    """
    Handles scraping for the https://cointelegraph.com/ website.
    """

    def __init__(self, keywords):
        """
        Initialize the scraper with a list of keywords.
        Args:
            keywords (list): List of keywords to search for in article headlines.
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
        Scrape articles from Cointelegraph (https://cointelegraph.com/).
        Args:
            soup (BeautifulSoup): Parsed HTML content of the Cointelegraph page.
        Returns:
            list: A list of dictionaries containing article data with keys:
                  'headline', 'link', and 'highlights'.
        """
        articles_data = []

        # Each article is wrapped in an <article> tag
        article_tags = soup.find_all("article")
        for article_tag in article_tags:
            # 1) Find headline
            headline_tag = article_tag.find(
                "span", class_="post-card__title"
            ) or article_tag.find("h2", class_="post-card__title")
            if not headline_tag:
                continue

            headline_text = headline_tag.get_text(strip=True)

            # 2) Find link
            a_tag = article_tag.find("a", href=True)
            if not a_tag:
                continue

            link_url = a_tag["href"].strip()

            # Prepend the base domain if not present
            if not link_url.startswith("http"):
                link_url = f"https://cointelegraph.com{link_url}"

            # 3) Check for keywords
            if self.contains_keywords(headline_text):
                highlights = self.extract_highlights(headline_text)
                articles_data.append(
                    {
                        "headline": headline_text,
                        "link": link_url,
                        "highlights": highlights,
                    }
                )

        return articles_data
