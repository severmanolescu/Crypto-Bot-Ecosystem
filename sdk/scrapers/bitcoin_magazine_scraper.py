import re

from bs4 import BeautifulSoup

class BitcoinMagazineScraper:
    """
    Handles scraping for https://bitcoinmagazine.com/articles (which uses the td_module_flex div structure).
    """

    def __init__(self, keywords):
        """
        :param keywords: List of strings that we want to check for in article headlines
        """
        self.keywords = keywords

    def contains_keywords(self, headline):
        """Match only full words or phrases, allowing ending punctuation like . , ! ?"""
        headline_lower = headline.lower()

        for keyword in self.keywords:
            keyword_lower = keyword.lower()
            pattern = rf'\b{re.escape(keyword_lower)}\b[.,!?]?'
            if re.search(pattern, headline_lower):
                return True
        return False

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
        """
        articles_data = []

        # 1) Find the relevant div containers
        post_divs = soup.find_all("div", class_=lambda c: c and "td_module_flex" in c)

        for post in post_divs:
            # Inside each post, find h3.entry-title td-module-title
            h3 = post.find("h3", class_="entry-title td-module-title")
            if not h3:
                continue

            # There's an <a> tag with the headline and the URL
            a_tag = h3.find("a", href=True)
            if not a_tag:
                continue

            headline_text = a_tag.get_text(strip=True)
            link_url = a_tag["href"].strip()

            # Prepend domain if needed
            if not link_url.startswith("http"):
                link_url = f"https://bitcoinmagazine.com{link_url}"

            # Check for keywords
            if self.contains_keywords(headline_text):
                highlights = self.extract_highlights(headline_text)
                articles_data.append({
                    "headline": headline_text,
                    "link": link_url,
                    "highlights": highlights
                })

        return articles_data
