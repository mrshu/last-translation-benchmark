# %%

import json
import os
import copy
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

with open("data/submissions.json", "r") as f:
    submissions = json.load(f)

submissions = [x for x in submissions if x["status"] == "accept"]

campaigns_file = []

MODELS = ["human", "Google Translate", "Gemini 3.5 Flash Lite", "GPT-5.4 Mini", "Qwen 3.7 Flash"]

for lang1, lang2 in [("Chinese (Simplified)", "English"), ("English", "Chinese (Simplified)")]:
    campaign_data = {
        "campaign_id": f"{lang1} -> {lang2}",
        "info": {
            "assignment": "task-based",
            "protocol": "cESA",
            "shuffle": True,
        },
        "data": []
    }
    for submission in submissions:
        if submission["source_lang"] != lang1 or submission["target_lang"] != lang2:
            continue
        if submission["source_media"] is not None or submission["source_instructions"] is not None:
            continue

        doc_obj = {
            "src": submission["source_text"],
            "tgt": {
                model: [x["translation"] for x in submission["translations"] if x["model"] == model][0]
                for model in MODELS
                if any(x["model"] == model for x in submission["translations"])
            }
        }
        doc_obj_rules = copy.deepcopy(doc_obj)
        doc_obj_rules["instructions"] = (
            "<div class='white-box' style='margin: -80px 10px 10px 0px; background-color: #e7e2cf;'>" +
            "Now also verify the translations by considering these rules. You may disagree with their necessity.<br><br>" +
            "<br>\n".join(["<b>Rule: </b>" + x["value"] for x in submission["verification_rules"]]) +
            "<div>"
        )
        campaign_data["data"].append([doc_obj])
        campaign_data["data"].append([doc_obj_rules])

    campaign_data["data"] = [campaign_data["data"]]*2
    print(f"Campaign {lang1} -> {lang2} has {len(campaign_data['data'][0])} items")
    campaigns_file.append(campaign_data)

os.makedirs("humeval", exist_ok=True)
with open("humeval/campaigns.json", "w") as f:
    json.dump(campaigns_file, f, ensure_ascii=False, indent=2)