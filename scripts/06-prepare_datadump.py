# %%

import json
from compact_json import Formatter
import os

os.chdir(os.path.dirname(__file__)+"/..")

with open("data/submissions.json", "r") as f:
    submissions = json.load(f)

# TODO: filter to v1

submissions = [s for s in submissions if s["status"] == "accept"]
submissions_new: list[dict] = []
for submission in submissions:
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
    if "observations" in submission_new["linguistics"]:
        submission_new["linguistics"].pop("observations", None)

    submissions_new.append(submission_new)

# with open("data/submissions_anonymous.json", "w") as f:
#     json.dump(submissions_new, f, indent=2, ensure_ascii=False)

# max_inline_length controls the maximum character width for one-line arrays
formatter = Formatter(
    indent_spaces=2,
    max_inline_length=200,
    ensure_ascii=False
)

with open("data/submissions_anonymous.json", "w", encoding="utf-8") as f:
    f.write(formatter.serialize(submissions_new)) # type: ignore