"""
Bitcoin Magazine Scraper Test
"""

# pylint: disable=redefined-outer-name

import pytest
from bs4 import BeautifulSoup

from src.handlers.load_variables_handler import load_keyword_list
from src.scrapers.bitcoin_magazine_scraper import BitcoinMagazineScraper
from src.scrapers.data_extractor import DataExtractor


@pytest.fixture
def get_keywords():
    """
    Fixture to create an instance of PlotTrades for testing.
    """
    return load_keyword_list()


def test_bitcoin_magazine_scraper_no_keywords(get_keywords):
    """
    Test the BitcoinMagazineScraper class.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="td_module_flex td_module_flex_1 td_module_wrap td-animation-stack td-cpt-post">
        <div class="td-module-container td-category-pos-image">
            <div class="td-module-meta-info">
                <h3 class="entry-title td-module-title">
                    <a href="/articles/sample-article">Sample Article</a>
                </h3>
            </div>
        </div>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = BitcoinMagazineScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert (
        len(articles) == 0
    ), "Expected no articles to be scraped from the sample HTML content."


def test_bitcoin_magazine_scraper_with_one_keyword(get_keywords):
    """
    Test the BitcoinMagazineScraper class with keywords.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="td_module_flex td_module_flex_1 td_module_wrap td-animation-stack td-cpt-post">
        <div class="td-module-container td-category-pos-image">
            <div class="td-module-meta-info">
                <h3 class="entry-title td-module-title">
                    <a href="/articles/bitcoin-price-analysis">Bitcoin Price Analysis</a>
                </h3>
            </div>
        </div>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = BitcoinMagazineScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 1, "Expected one article to be scraped."
    assert (
        articles[0]["headline"] == "Bitcoin Price Analysis"
    ), "Headline does not match."
    assert (
        articles[0]["link"]
        == "https://bitcoinmagazine.com/articles/bitcoin-price-analysis"
    ), "Link does not match."
    assert articles[0]["highlights"] == "#Bitcoin", "Highlights do not match."


def test_bitcoin_magazine_scraper_with_multiple_keywords(get_keywords):
    """
    Test the BitcoinMagazineScraper class with multiple keywords.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="td_module_flex td_module_flex_1 td_module_wrap td-animation-stack td-cpt-post">
        <div class="td-module-container td-category-pos-image">
            <div class="td-module-meta-info">
                <h3 class="entry-title td-module-title">
                    <a href="/articles/bitcoin-and-ethereum">Bitcoin and Ethereum Update</a>
                </h3>
            </div>
        </div>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = BitcoinMagazineScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 1, "Expected one article to be scraped."
    assert (
        articles[0]["headline"] == "Bitcoin and Ethereum Update"
    ), "Headline does not match."
    assert (
        articles[0]["link"]
        == "https://bitcoinmagazine.com/articles/bitcoin-and-ethereum"
    ), "Link does not match."
    assert (
        articles[0]["highlights"] == "#Bitcoin #ETH #Ethereum #Ether"
    ), "Highlights do not match."


def test_bitcoin_magazine_scraper_with_multiple_articles():
    """
    Test the BitcoinMagazineScraper class with multiple articles.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="td_module_flex td_module_flex_1 td_module_wrap td-animation-stack td-cpt-post">
        <div class="td-module-container td-category-pos-image">
            <div class="td-module-meta-info">
                <h3 class="entry-title td-module-title">
                    <a href="/articles/bitcoin-price-analysis">Bitcoin Price Analysis</a>
                </h3>
            </div>
        </div>
    </div>
    <div class="td_module_flex td_module_flex_1 td_module_wrap td-animation-stack td-cpt-post">
        <div class="td-module-container td-category-pos-image">
            <div class="td-module-meta-info">
                <h3 class="entry-title td-module-title">
                    <a href="/articles/ethereum-update">Ethereum Update</a>
                </h3>
            </div>
        </div>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(load_keyword_list())
    scraper = BitcoinMagazineScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 2, "Expected two articles to be scraped."
