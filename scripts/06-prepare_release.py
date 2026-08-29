# %%

import datetime
import json
import os
import collections
import fastchrf
import numpy as np

os.chdir(os.path.dirname(__file__)+"/..")

from last_translation_benchmark.utils import save_compact_json

with open("data/submissions.json", "r") as f:
    submissions = json.load(f)


with open("data/lang2iso.json", "r") as f:
    lang2iso = json.load(f)

submissions = [
    s for s in submissions
    # take accepted examples before September 1, 2026
    if s["status"] == "accept"
    and datetime.datetime.strptime(s["created_at"].split(" ")[0], "%Y-%m-%d").astimezone(datetime.UTC) < datetime.datetime(2026, 9, 1, tzinfo=datetime.UTC)
]

for submission in submissions:
    submission["translations"] = [
        t for t in submission["translations"]
        if not t["model"].startswith("SKIP: ")
        and not t["model"].startswith("PRIVILEGE-")
    ]

langs_to_examples = collections.defaultdict(list)
for submission in submissions:
    langs_to_examples[(submission["source_lang"], submission["target_lang"])].append(submission)

def translation_similarity(translations: list[dict]) -> float:
    translations = [t["translation"] for t in translations]
    translations = [t for t in translations if t is not None]
    return np.average(fastchrf.pairwise_chrf([translations], [translations])) # type: ignore

ltb_v1_micro_ids = {
    submission["id"]
    for examples in langs_to_examples.values()
    if len(examples) >= 20
    for submission in sorted(examples, key=lambda s: translation_similarity(s["translations"]), reverse=False)[:5]
}

def get_language_iso(lang_name: str) -> str | None:
    return lang2iso.get(lang_name) or lang2iso.get(lang_name.split(" (")[0]) or lang2iso.get(lang_name.split(", ")[0])

submissions_new: list[dict] = []
subset_sizes = collections.Counter()
for submission in submissions:
    submission_new = {
        "id": submission["id"],
        "source_text": submission["source_text"],
        "source_lang": submission["source_lang"],
        "target_lang": submission["target_lang"],
        "source_lang_iso": get_language_iso(submission["source_lang"]),
        "target_lang_iso": get_language_iso(submission["target_lang"]),
        "source_instructions": submission["source_instructions"],
        "source_media": submission["source_media"],
        "translations": [
            {
                "model": mt_obj["model"],
                "translation": mt_obj["translation"],
                "eval_verifier": mt_obj.get("verified_extra", {}).get("Gemini 3.1 Pro"),
            }
            for mt_obj in submission["translations"]
        ],
        "verification_rules": submission["verification_rules"],
        "created_at": submission["created_at"],
        "linguistics": submission.get("linguistics", {}),
        "tags": (
            ["LTBv1"]
            + (["LTBv1-textonly"] if submission["source_media"] is None and submission["source_instructions"] is None else [])
            + (["LTBv1-micro"] if submission["id"] in ltb_v1_micro_ids else [])
        ),
    }
    subset_sizes.update(submission_new["tags"])
    submission_new["linguistics"].pop("observations", None)
    submissions_new.append(submission_new)

print("Subset sizes:", subset_sizes)
save_compact_json(submissions_new, "data/v1.json")

# TODO: send to the server