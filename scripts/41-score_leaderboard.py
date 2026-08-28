import argparse
import json
import os
import sqlite3
import statistics
import sys
import urllib.parse

import requests

os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")
from last_translation_benchmark.utils import get_config

args = argparse.ArgumentParser()
args.add_argument("uid", type=int, help="Leaderboard entry ID to score")
args = args.parse_args()

db = sqlite3.connect(get_config("LTB_DB_PATH"))
lb_entry = db.execute("SELECT submissions, info FROM leaderboard WHERE id = ?", (args.uid,)).fetchone()
if not lb_entry:
    sys.exit(1)

lb_subs, lb_info = json.loads(lb_entry[0]), json.loads(lb_entry[1])
# TODO: replace this with some more static copy, like huggingface?
with open("data/submissions.json") as f:
    id_to_submission = {x["id"]: x for x in json.load(f)}
cookies = {"ltb_user": urllib.parse.quote(get_config("LTB_SCORER_USER")), "ltb_token": urllib.parse.quote(get_config("LTB_SCORER_TOKEN"))}

def get_prompt_verify(source_text: str, translation: str, rule: str, source_media: str | None) -> str:
    prompt = f"Your goal is to verify whether a translation fulfills a criterion.\n\nCriterion: {rule}\n\nInput: {source_text}\n\nTranslation to verify: {translation}\n\nOutput only pass or fail and nothing else."
    if source_media:
        mime = source_media.split(",")[0]
        context_type = "audio" if "audio" in mime else ("video" if "video" in mime else "image")
        prompt += f"\n\nUse the provided {context_type} as additional context."
    return prompt

for sub_obj_lb in lb_subs:
    sub_obj = id_to_submission.get(sub_obj_lb["id"])
    if not sub_obj or not sub_obj_lb["translation"]:
        sub_obj_lb["verification"] = None
        continue

    rule_results = []
    for rule in sub_obj["verification_rules"]:
        prompt = get_prompt_verify(sub_obj["source_text"] or "(attached)", sub_obj_lb["translation"], rule, sub_obj["source_media"])
        payload = {"model": "google/gemma-4-31b-it:free", "prompt": prompt}
        if sub_obj["source_media"]:
            payload["source_media"] = sub_obj["source_media"]
            
        r = requests.post(get_config("LTB_API_URL"), json=payload, cookies=cookies)
        if r.status_code == 200:
            res_text = r.json()
            if res_text is None:
                rule_results.append(False)
                continue
                
            text_clean = res_text.strip().lower().strip(" \t\n\r.,!?\"'*").split()[-1] if res_text.strip().lower().strip(" \t\n\r.,!?\"'*") else ""
            if "pass" in text_clean:
                rule_results.append(True)
            elif "fail" in text_clean:
                rule_results.append(False)
            elif "pass" in res_text.lower():
                rule_results.append(True)
            elif "fail" in res_text.lower():
                rule_results.append(False)
            else:
                rule_results.append(False)
        else:
            rule_results.append(False)

    sub_obj_lb["verification"] = rule_results

lb_info["score"] = statistics.mean([all(sub_obj_lb["verification"]) for sub_obj_lb in lb_subs if sub_obj_lb["verification"] is not None])
db.execute("UPDATE leaderboard SET status = 'scored', info = ?, submissions = ? WHERE id = ?", (json.dumps(lb_info), json.dumps(lb_subs), args.uid))
db.commit()
