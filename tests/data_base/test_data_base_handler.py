"""
Test suite for the data_base_handler class in the src.data_base module.
This suite tests the creation, insertion, updating, and
fetching of articles in the database.
"""

import pytest

from src.data_base import data_base_handler

TABLE_NAME = "test_table.db"
DB_HANDLER = data_base_handler.DataBaseHandler(articles_db_path=TABLE_NAME)


@pytest.mark.asyncio
async def test_create_table():
    """
    Test the creation of the database file.
    """
    print("Testing the creation of the database file...")

    # Create the table
    await DB_HANDLER.init_db()

    # Check if the table exists
    assert (
        DB_HANDLER.article_db_exists()
    ), f"Table {TABLE_NAME} should exist after creation."


@pytest.mark.asyncio
async def test_recreate_table():
    """
    Test the recreation of the database file.
    """
    print("\nTesting the recreation of the database file...")

    # Recreate the table
    await DB_HANDLER.recreate_data_base()

    # Check if the table exists
    assert (
        DB_HANDLER.article_db_exists()
    ), f"Table {TABLE_NAME} should exist after recreation."


@pytest.mark.asyncio
async def test_insert_article():
    """
    Test inserting an article into the database.
    """
    print("\nTesting the insertion of an article...")

    # Insert a test article
    await DB_HANDLER.save_article_to_db(
        source="crypto.news",
        headline="Test Headline",
        link="Test Link",
        highlights="Test Highlights",
    )

    # Check if the article was inserted
    articles = await DB_HANDLER.fetch_todays_news()
    assert len(articles) == 1, "There should be one article in the database."

    assert articles[0][0] == "crypto.news", "The inserted article source should match."
    assert (
        articles[0][1] == "Test Headline"
    ), "The inserted article headline should match."
    assert articles[0][2] == "Test Link", "The inserted article link should match."
    assert (
        articles[0][3] == "Test Highlights"
    ), "The inserted article highlights should match."


@pytest.mark.asyncio
async def test_update_article_summary():
    """
    Test updating the summary of an article in the database.
    """
    print("\nTesting the update of an article summary...")

    # Update the summary of the inserted article
    await DB_HANDLER.update_article_summary_in_db(
        link="Test Link", summary="Updated Summary"
    )

    # Fetch the updated article
    articles = await DB_HANDLER.fetch_todays_news()
    assert len(articles) == 1, "There should still be one article in the database."
    assert (
        articles[0][4] == "Updated Summary"
    ), "The article summary should be updated correctly."


@pytest.mark.asyncio
async def test_fetch_articles_by_tag():
    """
    Test fetching articles by tag.
    """
    print("\nTesting fetching articles by tag...")

    # Fetch articles by tag
    articles = await DB_HANDLER.search_articles_by_tag(tag="Test Highlights")

    assert len(articles) == 1, "There should be one article with the specified tag."
    assert articles[0][3] == "Test Highlights", "The article source should match."


@pytest.mark.asyncio
async def test_fetch_articles_by_tags():
    """
    Test fetching articles by tags.
    """
    print("\nTesting fetching articles by tag...")

    # Fetch articles by tag
    articles = await DB_HANDLER.search_articles_by_tags(tags=["Test Highlights"])

    assert len(articles) == 1, "There should be one article with the specified tag."
    assert articles[0][3] == "Test Highlights", "The article source should match."


@pytest.mark.asyncio
async def test_fetch_daily_article_counts():
    """
    Test fetching today's articles.
    """
    print("\nTesting fetching today's articles...")

    # Fetch today's articles
    articles = await DB_HANDLER.get_daily_article_counts()

    counts = dict(articles)
    crypto_news_count = counts.get("crypto.news", 0)

    assert crypto_news_count == 1, "There should be one article for today."


@pytest.mark.asyncio
async def test_fetch_weekly_article_counts():
    """
    Test fetching weekly articles.
    """
    print("\nTesting fetching this week articles...")

    # Fetch today's articles
    articles = await DB_HANDLER.get_weekly_article_counts()

    counts = dict(articles)
    crypto_news_count = counts.get("crypto.news", 0)

    assert crypto_news_count == 1, "There should be one article for this week."


@pytest.mark.asyncio
async def test_fetch_monthly_article_counts():
    """
    Test fetching monthly articles.
    """
    print("\nTesting fetching this month articles...")

    # Fetch today's articles
    articles = await DB_HANDLER.get_monthly_article_counts()

    counts = dict(articles)
    crypto_news_count = counts.get("crypto.news", 0)

    assert crypto_news_count == 1, "There should be one article for this month."
