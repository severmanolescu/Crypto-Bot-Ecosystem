import os

import aiosqlite
import logging

from logging.handlers import RotatingFileHandler

from sdk.SendTelegramMessage import send_telegram_message_update

handler = RotatingFileHandler('log.log', maxBytes=100_000_000, backupCount=3)
logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)

class DataBaseHandler:
    def __init__(self, db_path="./articles.db"):
        self.db_path = db_path

    async def init_db(self):
        """
        Creates the 'articles' table only if the DB file doesn't exist yet.
        If the file already exists, we assume the table was previously created.
        """
        db_file_exists = os.path.exists(self.db_path)

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
            logging.error(f"Error updating article summary in DB: {e}")
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
            logging.error(f"Error saving article to DB: {e}")
            print(f"Error saving article to DB: {e}")
            return 0


    async def search_articles_by_tag(self, tag, limit=10):
        """
        Search articles in SQLite by a single tag.
        We'll look in the 'highlights' column, e.g. searching for #Bitcoin or just 'Bitcoin'.
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Remove leading '#' if user typed it
            cleaned_tag = tag.lstrip('#').lower()
            # We'll do a LIKE match, ignoring case by storing everything in highlights as #UPPER or #LOWER if needed
            query = f"""
                   SELECT source, headline, link, highlights, openai_summary, date_scraped
                   FROM articles
                   WHERE lower(highlights) LIKE ?
                   ORDER BY date_scraped DESC
                   LIMIT {limit}
               """
            param = f"%{cleaned_tag}%"
            cursor = await db.execute(query, (param,))
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

        # Optionally send to Telegram
        await send_telegram_message_update(final_message, update)
