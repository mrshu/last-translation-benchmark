import asyncio

from last_translation_benchmark.db import get_submissions, save_submission


async def migrate():
    submissions = await get_submissions()
    for sub in submissions:
        rules = sub.get("verification_rules", [])
        changed = False
        new_rules = []
        for r in rules:
            if isinstance(r, dict) and "value" in r:
                new_rules.append(r["value"])
                changed = True
            else:
                new_rules.append(r)
        
        if changed:
            sub["verification_rules"] = new_rules
            await save_submission(sub)
            print(f"Migrated submission {sub['id']}")

if __name__ == "__main__":
    asyncio.run(migrate())