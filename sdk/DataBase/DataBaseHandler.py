import os
import datetime
import aiosqlite

from sdk.Logger import setup_logger
from sdk.SendTelegramMessage import send_telegram_message_update

logger = setup_logger("log.log")
logger.info("Data Base handler started")

class DataBaseHandler:
    def __init__(self, db_path="./articles.db"):
        self.db_path = db_path

    async def init_db(self):
        """
        Creates the 'articles' table only if the DB file doesn't exist yet.
        If the file already exists, we assume the table was previously created.
        """
        db_file_exists = os.path.exists(self.db_path)

        logger.info("Creating the data base...")
        print("Creating the data base...")

        async with aiosqlite.connect(self.db_path) as db:
            # If the file doesn't exist, we create the table for the first time
            if not db_file_exists:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        headline TEXT NOT NULL,
                        link TEXT NOT NULL UNIQUE,
                        highlights TEXT,
                        openai_summary TEXT,
                        date_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                await db.commit()

    async def recreate_data_base(self):
        logger.info("Recreating the data base...")
        print("Recreating the data base...")

        os.remove(self.db_path)

        await self.init_db()

    async def update_article_summary_in_db(self, link, summary):
        """Update the openai_summary for the article matching the given link."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE articles
                    SET openai_summary = ?
                    WHERE link = ?
                """, (summary, link))
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating article summary in DB: {e}")
            print(f"Error updating article summary in DB: {e}")

    async def save_article_to_db(self, source, headline, link, highlights):
        """
        Insert a new article record into SQLite (ignore if link already exists).
        Returns the number of rows inserted (1 if new, 0 if already exists).
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 1) Insert OR IGNORE
                await db.execute("""
                    INSERT OR IGNORE INTO articles (source, headline, link, highlights)
                    VALUES (?, ?, ?, ?)
                """, (source, headline, link, highlights))

                # 2) Check how many rows were changed by the *immediately previous* statement
                cursor = await db.execute("SELECT changes()")
                row = await cursor.fetchone()
                # row[0] will be 1 if inserted, 0 if ignored
                row_inserted = row[0] if row else 0

                # 3) Commit your changes
                await db.commit()

            return row_inserted

        except Exception as e:
            logger.error(f"Error saving article to DB: {e}")
            print(f"Error saving article to DB: {e}")
            return 0

    async def fetch_todays_news(self):
        today_date = datetime.datetime.now().strftime("%Y-%m-%d")  # Get today's date in YYYY-MM-DD format

        async with aiosqlite.connect("articles.db") as conn:
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
        async with aiosqlite.connect(self.db_path) as db:
            cleaned_tag = tag.lstrip('#').lower() if tag else None

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

        :param tags: list of tag strings
        :param limit: max articles to return
        :param match_any: if True, any tag match; if False, all tags must match
        """
        if not tags:
            return []

        if len(tags) == 1:
            return await self.search_articles_by_tag(tags[0])

        # Build query dynamically
        conditions = []
        params = []
        for t in tags:
            cleaned_tag = t.lstrip('#').lower()
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

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return rows

    async def get_daily_article_counts(self):
        """
        Returns how many articles were inserted for each source in the last 24 hours.
        Example row: (source, count)
        """
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT source, COUNT(*) 
                FROM articles
                WHERE date_scraped >= DATETIME('now', '-1 day')
                GROUP BY source
            """
            cursor = await db.execute(query)
            results = await cursor.fetchall()
            # results might look like: [("crypto.news", 5), ("cointelegraph", 8), ...]
            return results

    async def get_weekly_article_counts(self):
        """
        Returns how many articles were inserted for each source in the last 7 days.
        Example return: [("crypto.news", 12), ("cointelegraph", 23), ...]
        """
        async with aiosqlite.connect(self.db_path) as db:
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
        """
        async with aiosqlite.connect(self.db_path) as db:
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
        # Suppose we want to display daily, weekly, and monthly counts
        daily = await self.get_daily_article_counts()
        weekly = await self.get_weekly_article_counts()
        monthly = await self.get_monthly_article_counts()

        # Build a message or log it
        lines = []
        lines.append("Daily Stats:")
        for (src, cnt) in daily:
            lines.append(f" - {src}: {cnt} articles in last 24h")

        lines.append("\nWeekly Stats:")
        for (src, cnt) in weekly:
            lines.append(f" - {src}: {cnt} articles in last 7 days")

        lines.append("\nMonthly Stats:")
        for (src, cnt) in monthly:
            lines.append(f" - {src}: {cnt} articles in this month")

        final_message = "\n".join(lines)

        final_message += "\n #Statistics"

        # Optionally send to Telegram
        await send_telegram_message_update(final_message, update)

    async def store_fear_greed(self, index_value, index_text, last_updated):
        """Stores the Fear & Greed index in an SQLite database."""
        async with aiosqlite.connect("./data_bases/fear_greed.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fear_greed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_value INTEGER,
                    index_text TEXT,
                    last_updated TEXT
                )
            """)
            await db.execute("INSERT INTO fear_greed (index_value, index_text, last_updated) VALUES (?, ?, ?)",
                             (index_value, index_text, last_updated))
            await db.commit()

    async def store_eth_gas_fee(self, safe_gas, propose_gas, fast_gas):
        """Stores the Fear & Greed index in an SQLite database."""
        async with aiosqlite.connect("./data_bases/eth_gas_fee.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fear_greed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    safe_gas REAL,
                    propose_gas REAL,
                    fast_gas REAL,
                    saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("INSERT INTO fear_greed (safe_gas, propose_gas, fast_gas) VALUES (?, ?, ?)",
                             (safe_gas, propose_gas, fast_gas))
            await db.commit()

    async def store_market_sentiment(self, sentiment_counts):
        """Stores the Fear & Greed index in an SQLite database."""
        async with aiosqlite.connect("./data_bases/market_sentiment.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fear_greed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unknown INTEGER,
                    negative INTEGER,
                    neutral INTEGER,
                    positive INTEGER,
                    saved_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("INSERT INTO fear_greed (unknown, negative, neutral, positive) VALUES (?, ?, ?, ?)",
                             (sentiment_counts['Unknown'],
                              sentiment_counts['Negative'],
                              sentiment_counts['Neutral'],
                              sentiment_counts['Positive']))
            await db.commit()
