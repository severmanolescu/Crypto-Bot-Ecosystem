"""
Crypto News Scraper Tests
"""

# pylint: disable=redefined-outer-name

import pytest
from bs4 import BeautifulSoup

from src.handlers.load_variables_handler import load_keyword_list
from src.scrapers.crypto_news_scraper import CryptoNewsScraper
from src.scrapers.data_extractor import DataExtractor


@pytest.fixture
def get_keywords():
    """
    Fixture to create an instance of PlotTrades for testing.
    """
    return load_keyword_list()


def test_crypto_news_scraper_no_keywords(get_keywords):
    """
    Test the CryptoNewsScraper class.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="post-loop">
        <p class="post-loop__title">Sample Article</p>
        <a class="post-loop__link" href="/articles/sample-article"></a>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = CryptoNewsScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert (
        len(articles) == 0
    ), "Expected no articles to be scraped from the sample HTML content."


def test_crypto_news_scraper_with_one_keyword(get_keywords):
    """
    Test the CryptoNewsScraper class with keywords.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="post-loop">
        <p class="post-loop__title">Bitcoin Reaches New Heights</p>
        <a class="post-loop__link" href="/articles/bitcoin-reaches-new-heights"></a>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = CryptoNewsScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 1, "Expected one article to be scraped."
    assert articles[0]["headline"] == "Bitcoin Reaches New Heights"
    assert articles[0]["link"] == "/articles/bitcoin-reaches-new-heights"


def test_crypto_news_scraper_with_multiple_keywords(get_keywords):
    """
    Test the CryptoNewsScraper class with multiple keywords.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="post-loop">
        <p class="post-loop__title">Ethereum's New Update</p>
        <a class="post-loop__link" href="/articles/ethereum-new-update"></a>
    </div>
    <div class="post-loop">
        <p class="post-loop__title">Bitcoin's Market Surge</p>
        <a class="post-loop__link" href="/articles/bitcoin-market-surge"></a>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = CryptoNewsScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 2, "Expected two articles to be scraped."
    assert articles[0]["headline"] == "Ethereum's New Update"
    assert articles[1]["headline"] == "Bitcoin's Market Surge"


def test_crypto_news_scraper_with_multiple_articles():
    """
    Test the CryptoNewsScraper class with multiple articles.
    """

    # Sample HTML content for testing
    html_content = """
    <div class="post-loop">
        <p class="post-loop__title">Bitcoin Price Analysis</p>
        <a class="post-loop__link" href="/articles/bitcoin-price-analysis"></a>
    </div>
    <div class="post-loop">
        <p class="post-loop__title">Ethereum Update</p>
        <a class="post-loop__link" href="/articles/ethereum-update"></a>
    </div>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(load_keyword_list())
    scraper = CryptoNewsScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 2, "Expected two articles to be scraped."
