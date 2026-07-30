import asyncio

from last_translation_benchmark.db import get_submissions, save_submission


async def migrate():
    submissions = await get_submissions()
    print(f"Migrating {len(submissions)} submissions...")

    for s in submissions:
        if "verification_model" not in s:
            s["verification_model"] = "google/gemini-2.5-pro"
            await save_submission(s)

    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
