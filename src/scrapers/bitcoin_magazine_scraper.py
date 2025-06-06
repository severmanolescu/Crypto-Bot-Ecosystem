"""
Scraper for BitcoinMagazine (https://bitcoinmagazine.com/articles).
This scraper extracts articles that contain specific keywords in their headlines.
"""


# pylint: disable=too-few-public-methods
class BitcoinMagazineScraper:
    """
    Handles scraping for https://bitcoinmagazine.com/articles
    (which uses the td_module_flex div structure).
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
        Scrape articles from BitcoinMagazine.
        Example structure:

        <div class="td_module_flex td_module_flex_1 td_module_wrap td-animation-stack td-cpt-post">
          <div class="td-module-container td-category-pos-image">
              ...
              <div class="td-module-meta-info">
                  <h3 class="entry-title td-module-title">
                      <a href="..." ...>HEADLINE TEXT</a>
                  </h3>
                  ...
              </div>
          </div>
        </div>
        Args:
            soup (BeautifulSoup): Parsed HTML content of the Bitcoin Magazine articles page.
        Returns:
            list: A list of dictionaries containing article headlines, links, and highlights.
        """
        articles_data = []

        post_divs = soup.find_all("div", class_=lambda c: c and "td_module_flex" in c)

        for post in post_divs:
            # Inside each post, find h3.entry-title td-module-title
            h3 = post.find("h3", class_="entry-title td-module-title")
            if not h3:
                continue

            a_tag = h3.find("a", href=True)
            if not a_tag:
                continue

            headline_text = a_tag.get_text(strip=True)
            link_url = a_tag["href"].strip()

            if not link_url.startswith("http"):
                link_url = f"https://bitcoinmagazine.com{link_url}"

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
