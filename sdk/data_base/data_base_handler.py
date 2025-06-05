"""
data_base_handler.py
This module handles all interactions with the SQLite database for storing articles,
summaries, and other related data.
"""

import datetime
import logging
import os

import aiosqlite

from sdk.SendTelegramMessage import send_telegram_message_update

logger = logging.getLogger(__name__)
logger.info("Data Base handler started")


class DataBaseHandler:
    """
    This class manages the SQLite database for storing articles and their summaries.
    """

    def __init__(
        self,
        articles_db_path="./articles.db",
        daily_stats_db_path="./data_bases/daily_stats.db",
        fear_greed_db_path="./data_bases/fear_greed.db",
        eth_gas_fee_db_path="./data_bases/eth_gas_fee.db",
        market_sentiment_db_path="./data_bases/market_sentiment.db",
    ):
        self.articles_db_path = articles_db_path
        self.daily_stats_db_path = daily_stats_db_path
        self.fear_greed_db_path = fear_greed_db_path
        self.eth_gas_fee_db_path = eth_gas_fee_db_path
        self.market_sentiment_db_path = market_sentiment_db_path

    async def init_db(self):
        """
        Creates the 'articles' table only if the DB file doesn't exist yet.
        If the file already exists, we assume the table was previously created.
        """
        db_file_exists = os.path.exists(self.articles_db_path)

        logger.info("Creating the data base...")
        print("Creating the data base...")

        try:
            async with aiosqlite.connect(self.articles_db_path) as db:
                # If the file doesn't exist, we create the table for the first time
                if not db_file_exists:
                    await db.execute(
                        """
                        CREATE TABLE IF NOT EXISTS articles (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            source TEXT NOT NULL,
                            headline TEXT NOT NULL,
                            link TEXT NOT NULL UNIQUE,
                            highlights TEXT,
                            openai_summary TEXT,
                            date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """
                    )
                    await db.commit()
                    print("Database and table created successfully.")
                else:
                    print("Database file already exists. Skipping table creation.")
        except aiosqlite.Error as e:
            logger.error("Error creating the database: %s", e)
            print("Error creating the database: ", e)

    async def recreate_data_base(self):
        """
        Recreates the SQLite database by deleting the existing file and initializing a new one.
        """
        logger.info("Recreating the data base...")
        print("Recreating the data base...")

        os.remove(self.articles_db_path)

        await self.init_db()

    async def update_article_summary_in_db(self, link, summary):
        """
        Update the openai_summary for the article matching the given link.
        Args:
            link (str): The unique link of the article to update.
            summary (str): The new summary to set for the article.
        """
        try:
            async with aiosqlite.connect(self.articles_db_path) as db:
                await db.execute(
                    """
                    UPDATE articles
                    SET openai_summary = ?
                    WHERE link = ?
                """,
                    (summary, link),
                )
                await db.commit()
            logger.info("Article summary updated in DB successfully.")
        except aiosqlite.Error as e:
            logger.error("Error updating article summary in DB: %s", e)
            print("Error updating article summary in DB: ", e)

    async def save_article_to_db(self, source, headline, link, highlights):
        """
        Insert a new article record into SQLite (ignore if link already exists).
        Returns the number of rows inserted (1 if new, 0 if already exists).
        Args:
            source (str): The source of the article (e.g., "crypto.news").
            headline (str): The headline of the article.
            link (str): The unique link to the article.
            highlights (str): Highlights or summary of the article.
        Returns:
            int: Number of rows inserted (1 if new, 0 if already exists).
        """
        try:
            async with aiosqlite.connect(self.articles_db_path) as db:
                # 1) Insert OR IGNORE
                await db.execute(
                    """
                    INSERT OR IGNORE INTO articles (source, headline, link, highlights)
                    VALUES (?, ?, ?, ?)
                """,
                    (source, headline, link, highlights),
                )

                # 2) Check how many rows were changed by the *immediately previous* statement
                cursor = await db.execute("SELECT changes()")
                row = await cursor.fetchone()
                # row[0] will be 1 if inserted, 0 if ignored
                row_inserted = row[0] if row else 0

                # 3) Commit your changes
                await db.commit()

            logger.info("Article saved to DB successfully: %s", headline)
            return row_inserted

        except aiosqlite.OperationalError as e:
            logger.error("Operational error saving article to DB: %s", e)
            print("Operational error saving article to DB: ", e)
            return 0

    async def fetch_todays_news(self):
        """
        Fetches all articles from today (YYYY-MM-DD) from the SQLite database.
        Returns:
            list: List of tuples with article data for today.
        """
        today_date = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # Get today's date in YYYY-MM-DD format

        async with aiosqlite.connect(self.articles_db_path) as conn:
            cursor = await conn.cursor()

            query = """
                SELECT source, headline, link, highlights, openai_summary, date_scraped
                FROM articles
                WHERE DATE(date_scraped) = ?
                ORDER BY date_scraped DESC
            """

            await cursor.execute(query, (today_date,))
            news_data = await cursor.fetchall()

            return news_data  # Returns all articles from today

    async def search_articles_by_tag(self, tag=None, limit=10):
        """
        Search articles in SQLite by a single tag.
        Args:
            tag (str): The tag to search for (e.g., "#bitcoin").
            limit (int): Maximum number of articles to return.
        Returns:
            list: List of tuples with article data matching the tag.
        """
        async with aiosqlite.connect(self.articles_db_path) as db:
            cleaned_tag = tag.lstrip("#").lower() if tag else None

            query = f"""
                SELECT source, headline, link, highlights, openai_summary, date_scraped
                FROM articles
                {"WHERE lower(highlights) LIKE ?" if cleaned_tag else ""}
                ORDER BY date_scraped DESC
                LIMIT {limit}
            """

            params = (f"%{cleaned_tag}%",) if cleaned_tag else ()
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return rows

    async def search_articles_by_tags(self, tags, limit=10, match_any=True):
        """
        Search articles in SQLite by multiple tags.
        Args:
            tags (list): List of tags to search for (e.g., ["#bitcoin", "#ethereum"]).
            limit (int): Maximum number of articles to return.
            match_any (bool): If True, articles matching any tag are returned.
                              If False, articles must match all tags.
        Returns:
            list: List of tuples with article data matching the tags.
        """
        if not tags:
            return []

        if len(tags) == 1:
            return await self.search_articles_by_tag(tags[0])

        # Build query dynamically
        conditions = []
        params = []
        for t in tags:
            cleaned_tag = t.lstrip("#").lower()
            conditions.append("lower(highlights) LIKE ?")
            params.append(f"%{cleaned_tag}%")

        # Combine conditions with OR (match_any=True) or AND (match_any=False)
        connector = " OR " if match_any else " AND "
        where_clause = connector.join(conditions)

        query = f"""
               SELECT source, headline, link, highlights, date_scraped
               FROM articles
               WHERE {where_clause}
               ORDER BY date_scraped DESC
               LIMIT {limit}
           """

        async with aiosqlite.connect(self.articles_db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return rows

    async def get_daily_article_counts(self):
        """
        Returns how many articles were inserted for each source in the last 24 hours.
        Returns:
            list: List of tuples with source and count of articles.
        """
        sources = {"crypto.news", "bitcoinmagazine", "cointelegraph"}
        async with aiosqlite.connect(self.articles_db_path) as db:
            query = """
                SELECT source, COUNT(*) 
                FROM articles
                WHERE date_scraped >= DATETIME('now', '-1 day')
                GROUP BY source
            """
            cursor = await db.execute(query)
            results = await cursor.fetchall()

            # Convert results into a dictionary for easy lookup
            counts = dict(results)

            # Ensure all three sources are included with at least 0
            final_counts = [(source, counts.get(source, 0)) for source in sources]

            return final_counts

    async def get_weekly_article_counts(self):
        """
        Returns how many articles were inserted for each source in the last 7 days.
        Example return: [("crypto.news", 12), ("cointelegraph", 23), ...]
        Returns:
            list: List of tuples with source and count of articles in the last 7 days.
        """
        async with aiosqlite.connect(self.articles_db_path) as db:
            query = """
                SELECT source, COUNT(*) 
                FROM articles
                WHERE date_scraped >= DATETIME('now', '-7 days')
                GROUP BY source
            """
            cursor = await db.execute(query)
            results = await cursor.fetchall()
            return results

    async def get_monthly_article_counts(self):
        """
        Returns how many articles were inserted for each source in the current calendar month.
        Example return: [("crypto.news", 55), ("cointelegraph", 80), ...]
        Returns:
            list: List of tuples with source and count of articles in the current month.
        """
        async with aiosqlite.connect(self.articles_db_path) as db:
            query = """
                SELECT source, COUNT(*)
                FROM articles
                WHERE strftime('%Y-%m', date_scraped) = strftime('%Y-%m', 'now')
                GROUP BY source
            """
            cursor = await db.execute(query)
            results = await cursor.fetchall()
            return results

    async def show_stats(self, update):
        """
        Displays statistics about the number of articles collected from different sources
        in the last 24 hours, 7 days, and current month.
        Args:
            update: The Telegram update object to send the message.
        """
        # Suppose we want to display daily, weekly, and monthly counts
        daily = await self.get_daily_article_counts()
        weekly = await self.get_weekly_article_counts()
        monthly = await self.get_monthly_article_counts()

        # Build a message or log it
        lines = ["<b>Daily Stats:</b>"]
        for src, cnt in daily:
            lines.append(f" - <b>{src}</b>: <b>{cnt}</b> articles in last 24h")

        lines.append("\n<b>Weekly Stats:</b>")
        for src, cnt in weekly:
            lines.append(f" - <b>{src}</b>: <b>{cnt}</b> articles in last 7 days")

        lines.append("\n<b>Monthly Stats:</b>")
        for src, cnt in monthly:
            lines.append(f" - <b>{src}</b>: <b>{cnt}</b> articles in this month")

        final_message = "\n".join(lines)

        final_message += "\n #Statistics"

        await send_telegram_message_update(final_message, update)

    async def store_daily_stats(self):
        """
        Stores the Fear & Greed index in an SQLite database.
        """
        async with aiosqlite.connect(self.daily_stats_db_path) as db:
            await db.execute(
                """
                        CREATE TABLE IF NOT EXISTS daily_stats (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            crypto_news INTEGER,
                            cointelegraph INTEGER,
                            bitcoinmagazine INTEGER,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """
            )
            daily = dict(await self.get_daily_article_counts())

            await db.execute(
                "INSERT INTO daily_stats (crypto_news, cointelegraph, bitcoinmagazine) "
                "VALUES (?, ?, ?)",
                (
                    daily["crypto.news"],
                    daily["cointelegraph"],
                    daily["bitcoinmagazine"],
                ),
            )
            await db.commit()

    async def store_fear_greed(self, index_value, index_text, last_updated):
        """
        Stores the Fear & Greed index in an SQLite database.
        Args:
            index_value (int): The value of the Fear & Greed index.
            index_text (str): The text description of the index value.
            last_updated (str): The timestamp when the index was last updated.
        """
        async with aiosqlite.connect(self.fear_greed_db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS fear_greed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_value INTEGER,
                    index_text TEXT,
                    last_updated TEXT
                )
            """
            )
            await db.execute(
                "INSERT INTO fear_greed (index_value, index_text, last_updated) VALUES (?, ?, ?)",
                (index_value, index_text, last_updated),
            )
            await db.commit()

    async def store_eth_gas_fee(self, safe_gas, propose_gas, fast_gas):
        """
        Stores the Fear & Greed index in an SQLite database.
        Args:
            safe_gas (float): The safe gas fee.
            propose_gas (float): The proposed gas fee.
            fast_gas (float): The fast gas fee.
        """
        async with aiosqlite.connect(self.eth_gas_fee_db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS fear_greed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    safe_gas REAL,
                    propose_gas REAL,
                    fast_gas REAL,
                    saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            await db.execute(
                "INSERT INTO fear_greed (safe_gas, propose_gas, fast_gas) VALUES (?, ?, ?)",
                (safe_gas, propose_gas, fast_gas),
            )
            await db.commit()

    async def store_market_sentiment(self, sentiment_counts):
        """
        Stores the Fear & Greed index in an SQLite database.
        Args:
            sentiment_counts (dict): A dictionary containing counts for each sentiment type.
                Example: {"Unknown": 10, "Negative": 20, "Neutral": 30, "Positive": 40}
        """
        async with aiosqlite.connect(self.market_sentiment_db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS fear_greed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unknown INTEGER,
                    negative INTEGER,
                    neutral INTEGER,
                    positive INTEGER,
                    saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            await db.execute(
                "INSERT INTO fear_greed (unknown, negative, neutral, positive) VALUES (?, ?, ?, ?)",
                (
                    sentiment_counts["Unknown"],
                    sentiment_counts["Negative"],
                    sentiment_counts["Neutral"],
                    sentiment_counts["Positive"],
                ),
            )
            await db.commit()

    def article_db_exists(self):
        """
        Check if the articles database file exists.
        Returns:
            bool: True if the database file exists, False otherwise.
        """
        return os.path.exists(self.articles_db_path)

    def daily_stats_db_exists(self):
        """
        Check if the daily stats database file exists.
        Returns:
            bool: True if the database file exists, False otherwise.
        """
        return os.path.exists(self.daily_stats_db_path)

    def fear_greed_db_exists(self):
        """
        Check if the Fear & Greed database file exists.
        Returns:
            bool: True if the database file exists, False otherwise.
        """
        return os.path.exists(self.fear_greed_db_path)

    def eth_gas_fee_db_exists(self):
        """
        Check if the ETH Gas Fee database file exists.
        Returns:
            bool: True if the database file exists, False otherwise.
        """
        return os.path.exists(self.eth_gas_fee_db_path)
