"""
Add a 'date' column to the 'daily_stats' table in a SQLite database and populate it with decreasing dates.
"""

import asyncio
from datetime import datetime, timedelta

import aiosqlite


async def update_dates():
    """
    This script updates the 'date' column in the 'daily_stats' table of a SQLite database.
    """
    db_path = "data_base_path"  # Replace with your actual database file
    async with aiosqlite.connect(db_path) as db:
        # Step 1: Add the 'date' column if it doesn't exist
        await db.execute("ALTER TABLE daily_stats ADD COLUMN date DATE")
        await db.commit()

        # Step 2: Fetch all records ordered by ID
        async with db.execute("SELECT id FROM daily_stats ORDER BY id ASC") as cursor:
            rows = await cursor.fetchall()

        # Step 3: Update each row with a decreasing date
        start_date = datetime.today().date() - timedelta(days=1)  # Yesterday
        for index, (row_id,) in enumerate(rows):
            date_value = start_date - timedelta(days=index)
            await db.execute(
                "UPDATE daily_stats SET date = ? WHERE id = ?", (date_value, row_id)
            )
        await db.commit()
        print("Dates updated successfully!")


# Run the async function
asyncio.run(update_dates())
