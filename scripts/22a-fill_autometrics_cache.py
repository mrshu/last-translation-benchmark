# %%

import json
import os
import collections
import sacrebleu
from frozendict import frozendict

os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

with open("data/submissions.json", "r") as f:
    data_submissions = json.load(f)

data_to_score = set()

for submission in data_submissions:
    if submission["source_media"] is not None or submission["source_instructions"] is not None:
        continue
    translation_reference = [x for x in submission["translations"] if x["model"] == "human"][0]
    for translation in submission["translations"]:
        data_to_score.add(frozendict({
            "source_lang": submission["source_lang"],
            "target_lang": submission["target_lang"],
            "source_text": submission["source_text"] or "",
            "translation": translation["translation"] or "",
            "reference": translation_reference["translation"] or "",
        }))

data_to_score = list(data_to_score)

if not os.path.exists("computed/autometrics_cache.json"):
    with open("computed/autometrics_cache.json", "w") as f:
        json.dump({}, f)

with open("computed/autometrics_cache.json", "r") as f:
    data_cache = collections.defaultdict(dict)
    data_cache.update(json.load(f))

def submission_to_key(submission, translation):
    return f"{submission['source_lang']}_#_{submission['target_lang']}_#_{submission['source_text']}_#_{translation['translation']}_#_{submission['reference']}"

def filter_unscored(data_to_score, data_cache, metric):
    unscored = []
    for x in data_to_score:
        key = submission_to_key(x, x)
        if key not in data_cache or metric not in data_cache[key]:
            unscored.append(x)
    return unscored

# COMET
import  comet
model = comet.load_from_checkpoint(comet.download_model("Unbabel/wmt22-cometkiwi-da"))
data_to_score_local = filter_unscored(data_to_score, data_cache, "CometKiwi22")
data = [
    {
        "src": x["source_text"],
        "mt": x["translation"],
    }
    for x in data_to_score_local
]
scores = model.predict(data, batch_size=8, gpus=1).scores # type: ignore
for score, x in zip(scores, data_to_score_local):
    data_cache[submission_to_key(x, x)]["CometKiwi22"] = score

# ChrF
data_to_score_local = filter_unscored(data_to_score, data_cache, "ChrF")
for x in data_to_score_local:
    chrf = sacrebleu.corpus_chrf(
        [x["translation"]],
        [[x["reference"]]],
    ).score
    data_cache[submission_to_key(x, x)]["ChrF"] = chrf

with open("computed/autometrics_cache.json", "w") as f:
    json.dump(data_cache, f, indent=2, ensure_ascii=False)