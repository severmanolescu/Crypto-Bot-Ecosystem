"""
Scraper for Crypto News (https://crypto.news/).
This scraper extracts articles that contain specific keywords in their headlines.
"""


# pylint: disable=too-few-public-methods
class CryptoNewsScraper:
    """
    Handles scraping for the https://crypto.news/ website.
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

                if self.data_extractor.contains_keywords(headline_text):
                    highlights = self.data_extractor.contains_keywords(headline_text)
                    articles.append(
                        {
                            "headline": headline_text,
                            "link": link_url,
                            "highlights": highlights,
                        }
                    )

        return articles
