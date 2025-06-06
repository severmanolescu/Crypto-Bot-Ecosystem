"""
Scraper for Cointelegraph (https://cointelegraph.com/).
This scraper extracts articles that contain specific keywords in their headlines.
"""


# pylint: disable=too-few-public-methods
class CointelegraphScraper:
    """
    Handles scraping for the https://cointelegraph.com/ website.
    """

    def __init__(self, data_extractor):
        """
        Initialize the scraper with a DataExtractor instance to
        handle keyword matching.
        Args:
            data_extractor (DataExtractor): An instance of DataExtractor to
            handle keyword matching
        """
        self.data_extractor = data_extractor

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

        article_tags = soup.find_all("article")
        for article_tag in article_tags:
            headline_tag = article_tag.find(
                "span", class_="post-card__title"
            ) or article_tag.find("h2", class_="post-card__title")
            if not headline_tag:
                continue

            headline_text = headline_tag.get_text(strip=True)

            a_tag = article_tag.find("a", href=True)
            if not a_tag:
                continue

            link_url = a_tag["href"].strip()

            # Prepend the base domain if not present
            if not link_url.startswith("http"):
                link_url = f"https://cointelegraph.com{link_url}"

            # pylint: disable=duplicate-code

            if self.data_extractor.contains_keywords(headline_text):
                highlights = self.data_extractor.extract_highlights(headline_text)
                articles_data.append(
                    {
                        "headline": headline_text,
                        "link": link_url,
                        "highlights": highlights,
                    }
                )

        return articles_data
