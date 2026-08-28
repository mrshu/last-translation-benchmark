import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

MODEL = "Google Translate"

with open("data/submissions.json", "r") as f:
    data = json.load(f)

out = []
for s in data:
    t_val = None
    for t in s["translations"]:
        if t["model"] == MODEL:
            t_val = t.get("translation")
            break
    out.append({"id": s["id"], "translation": t_val})

os.makedirs("computed/submissions/", exist_ok=True)
with open(f"computed/submissions/{MODEL}.json", "w") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
