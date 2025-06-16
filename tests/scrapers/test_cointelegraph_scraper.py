"""
CoinTelegraph Scraper Test
"""

# pylint: disable=redefined-outer-name

import pytest
from bs4 import BeautifulSoup

from src.handlers.load_variables_handler import load_keyword_list
from src.scrapers.cointelegraph_scraper import CoinTelegraphScraper
from src.scrapers.data_extractor import DataExtractor


@pytest.fixture
def get_keywords():
    """
    Fixture to create an instance of PlotTrades for testing.
    """
    return load_keyword_list()


def test_cointelegraph_scraper_no_keywords(get_keywords):
    """
    Test the CoinTelegraphScraper class.
    """

    # Sample HTML content for testing
    html_content = """
    <article>
        <span class="post-card__title">Sample Article</span>
        <a href="/articles/sample-article"></a>
    </article>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = CoinTelegraphScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert (
        len(articles) == 0
    ), "Expected no articles to be scraped from the sample HTML content."


def test_cointelegraph_scraper_with_one_keyword(get_keywords):
    """
    Test the CoinTelegraphScraper class with keywords.
    """

    # Sample HTML content for testing
    html_content = """
    <article>
        <span class="post-card__title">Bitcoin Hits New Highs</span>
        <a href="/articles/bitcoin-hits-new-highs"></a>
    </article>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = CoinTelegraphScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 1, "Expected one article to be scraped."
    assert articles[0]["headline"] == "Bitcoin Hits New Highs"
    assert (
        articles[0]["link"]
        == "https://cointelegraph.com/articles/bitcoin-hits-new-highs"
    )
    assert articles[0]["highlights"] == "#Bitcoin"


def test_cointelegraph_scraper_with_multiple_keywords(get_keywords):
    """
    Test the CoinTelegraphScraper class with multiple keywords.
    """

    # Sample HTML content for testing
    html_content = """
    <article>
        <span class="post-card__title">Bitcoin and Ethereum Rally</span>
        <a href="/articles/bitcoin-ethereum-rally"></a>
    </article>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = CoinTelegraphScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 1, "Expected one article to be scraped."
    assert articles[0]["headline"] == "Bitcoin and Ethereum Rally"
    assert (
        articles[0]["link"]
        == "https://cointelegraph.com/articles/bitcoin-ethereum-rally"
    )
    assert articles[0]["highlights"] == "#Bitcoin #ETH #Ethereum #Ether"


def test_cointelegraph_scraper_with_multiple_articles(get_keywords):
    """
    Test the CoinTelegraphScraper class with multiple articles.
    """

    # Sample HTML content for testing
    html_content = """
    <article>
        <span class="post-card__title">Bitcoin Price Analysis</span>
        <a href="/articles/bitcoin-price-analysis"></a>
    </article>
    <article>
        <span class="post-card__title">Ethereum Network Upgrade</span>
        <a href="/articles/ethereum-network-upgrade"></a>
    </article>
    """

    soup = BeautifulSoup(html_content, "html.parser")
    data_extractor = DataExtractor(get_keywords)
    scraper = CoinTelegraphScraper(data_extractor)

    articles = scraper.scrape(soup)

    assert len(articles) == 2, "Expected two articles to be scraped."
    assert articles[0]["headline"] == "Bitcoin Price Analysis"
    assert (
        articles[0]["link"]
        == "https://cointelegraph.com/articles/bitcoin-price-analysis"
    )
    assert articles[0]["highlights"] == "#Bitcoin"

    assert articles[1]["headline"] == "Ethereum Network Upgrade"
    assert (
        articles[1]["link"]
        == "https://cointelegraph.com/articles/ethereum-network-upgrade"
    )
    assert articles[1]["highlights"] == "#ETH #Ethereum #Ether"
