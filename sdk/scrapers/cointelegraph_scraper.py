from bs4 import BeautifulSoup

class CointelegraphScraper:
    """
    Handles scraping for the https://cointelegraph.com/ website.
    """

    def __init__(self, keywords):
        """
        :param keywords: List of strings that we want to check for in article headlines
        """
        self.keywords = keywords

    def contains_keywords(self, headline: str) -> bool:
        """Check if the headline contains any of the specified keywords."""
        headline_lower = headline.lower()
        return any(keyword.lower() in headline_lower for keyword in self.keywords)

    def extract_highlights(self, headline: str) -> str:
        """Return #hashtags for each matched keyword in the headline."""
        headline_lower = headline.lower()
        found_keywords = [
            f"#{keyword.replace(' ', '')}"
            for keyword in self.keywords
            if keyword.lower() in headline_lower
        ]
        return ' '.join(found_keywords) if found_keywords else "#GeneralNews"

    def scrape(self, soup: BeautifulSoup) -> list:
        """
        Scrape articles from Cointelegraph (https://cointelegraph.com/).
        :param soup: BeautifulSoup object
        :return: list of dicts, each with {headline, link, highlights}
        """
        articles_data = []

        # Each article is wrapped in an <article> tag
        article_tags = soup.find_all("article")
        for article_tag in article_tags:
            # 1) Find headline
            headline_tag = (
                article_tag.find("span", class_="post-card__title") or
                article_tag.find("h2", class_="post-card__title")
            )
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
                articles_data.append({
                    "headline": headline_text,
                    "link": link_url,
                    "highlights": highlights
                })

        return articles_data
