# %%

import json
import os
import copy
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

with open("data/submissions.json", "r") as f:
    submissions = json.load(f)

submissions = [x for x in submissions if x["status"] == "accept"]

campaigns_file = []

MODELS = ["human", "Google Translate", "Gemini 3.5 Flash Lite", "GPT-5.4 Mini", "Gemma 4"]
STYLE_FORM = "<style>.form-container { max-width: 1000px !important; }</style>"
STYLE_CESA = """
<style>
.output_scrollable { flex-direction: column; gap: 20px !important; }
.output_item { display: block !important; }
.output_src { width: calc(100% - 10px) !important; margin-bottom: 30px; }
.output_block { width: 1000px; margin-left: auto; margin-right: auto;}
.output_response { width: 400px !important; display: inline-block !important; }
.slider_label_cESA { width: 200px; text-align: left; display: inline-block; }
</style>
"""

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
            },
            "instructions": STYLE_CESA,
        }
        doc_obj_rules = copy.deepcopy(doc_obj)
        doc_obj_rules["instructions"] = (
            "<div class='white-box' style='margin: -80px 10px 10px 0px; background-color: #e7e2cf;'>" +
            "Now also verify the translations by considering these rules. You may disagree with their necessity.<br><br>" +
            "<br>\n".join(["<b>Rule: </b>" + x["value"] for x in submission["verification_rules"]]) +
            "<div>"+STYLE_CESA
        )
        doc_obj_form = [
            {
                "text": "<b>Source text:</b> " + submission["source_text"] + STYLE_FORM,
                "form": None,
            },
        ]

        for rule in submission["verification_rules"]:
            doc_obj_form.append({
                "text": f"<br><br>Do you think the rule is realistic, or would it fail correct translations?<br><br><b>Rule:</b> {rule['value']}",
                "form": "choices",
                "choices": ["This rule is realistic and reasonable", "This rule is too strict", "Not sure"],
            })
        doc_obj_form.append({
            "text": (
                "<br><br>Are there translations that are incorrect but would pass all of these verifications at the same time?<br><br>"+
                "<br>".join(["<b>Rule: </b>" + x["value"] for x in submission["verification_rules"]])
            ),
            "form": "choices",
            "choices": ["These rules are fine as they cover most cases", "Some incorrect translations might pass through", "Not sure"],
        })


        campaign_data["data"].append([doc_obj])
        campaign_data["data"].append([doc_obj_rules])
        campaign_data["data"].append(doc_obj_form)

    campaign_data["data"] = [campaign_data["data"]]*2
    print(f"Campaign {lang1} -> {lang2} has {len(campaign_data['data'][0])} items")
    campaigns_file.append(campaign_data)

os.makedirs("humeval", exist_ok=True)
with open("humeval/campaigns.json", "w") as f:
    json.dump(campaigns_file, f, ensure_ascii=False, indent=2)