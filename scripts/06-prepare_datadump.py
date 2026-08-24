# %%

import json
from datetime import datetime
import os

os.chdir(os.path.dirname(__file__)+"/..")

from last_translation_benchmark.utils import save_compact_json

with open("data/submissions.json", "r") as f:
    submissions = json.load(f)



submissions = [s for s in submissions if s["status"] == "accept"]
submissions_new: list[dict] = []
for submission in submissions:
    # TODO test/dev split

    # check if date is before September 1, 2026
    if datetime.strptime(submission["created_at"].split(" ")[0], "%Y-%m-%d") >= datetime(2026, 9, 1):
        continue

    submission_new = {
        "id": submission["id"],
        "source_text": submission["source_text"],
        "source_lang": submission["source_lang"],
        "target_lang": submission["target_lang"],
        # TODO: iso codes
        "source_instructions": submission["source_instructions"],
        "translations": [
            {
                "model": mt_obj["model"],
                "translation": mt_obj["translation"],
                "eval_verified": mt_obj.get("verified_extra", {}),
                "eval_judge": mt_obj.get("judge_extra", {}),
            }
            for mt_obj in submission["translations"]
            if (
                not mt_obj["model"].startswith("SKIP: ")
                and not mt_obj["model"].startswith("PRIVILEGE-")
            )

        ],
        "verification_rules": submission["verification_rules"],
        "created_at": submission["created_at"],
        "linguistics": submission.get("linguistics", {}),
    }
    submission_new["linguistics"].pop("observations", None)

    submissions_new.append(submission_new)


save_compact_json(submissions_new, "data/submissions_anonymous.json")