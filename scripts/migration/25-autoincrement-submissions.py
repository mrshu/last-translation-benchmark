import asyncio

from last_translation_benchmark.db import _open_db


async def migrate():
    async with _open_db() as db:
        await db.execute("BEGIN EXCLUSIVE")
        try:
            async with db.execute(
                "SELECT sql FROM sqlite_master "
                "WHERE type = 'table' AND name = 'submissions'"
            ) as cur:
                row = await cur.fetchone()
            if row is None:
                raise RuntimeError("Submissions table not found.")

            if "AUTOINCREMENT" in row[0].upper():
                await db.commit()
                return

            await db.execute(
                "CREATE TABLE submissions_new "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)"
            )
            await db.execute(
                "INSERT INTO submissions_new (id, data) "
                "SELECT id, data FROM submissions"
            )
            await db.execute("DROP TABLE submissions")
            await db.execute("ALTER TABLE submissions_new RENAME TO submissions")
            await db.commit()
        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
