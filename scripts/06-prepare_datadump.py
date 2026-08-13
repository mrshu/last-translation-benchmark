# %%

import json
import os

os.chdir(os.path.dirname(__file__)+"/..")

with open("data/submissions.json", "r") as f:
    submissions = json.load(f)

submissions = [s for s in submissions if s["status"] == "accept" and s["source_media"] is None]
for submission in submissions:
    for key in ["username", "created_at", "reviewer_comment", "status", "comments", "reviewed_by"]:
        submission.pop(key, None)

with open("data/submissions_anonymous.json", "w") as f:
    json.dump(submissions, f, indent=2, ensure_ascii=False)