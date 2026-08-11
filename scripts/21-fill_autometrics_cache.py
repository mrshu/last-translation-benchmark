# %%

import json
import os
import collections
import random
import sacrebleu
from frozendict import frozendict

os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

with open("data/submissions.json", "r") as f:
    data_submissions = json.load(f)

data_to_score = set()

for submission in data_submissions:
    translation_reference = [x for x in submission["translations"] if x["model"] == "human"][0]
    for translation in submission["translations"]:
        # store lang1 _#_ lang2 _#_ source _#_ translation _#_ reference
        data_to_score.add(frozendict({
            "lang1": submission["source_lang"],
            "lang2": submission["target_lang"],
            "source_text": submission["source_text"],
            "translation": translation["translation"],
            "reference": translation_reference["translation"]
        }))

data_to_score = list(data_to_score)
random.Random(0).shuffle(data_to_score)
data_to_score = data_to_score

if not os.path.exists("computed/autometrics_cache.json"):
    with open("computed/autometrics_cache.json", "w") as f:
        json.dump({}, f)

with open("computed/autometrics_cache.json", "r") as f:
    data_cache = collections.defaultdict(dict)
    data_cache.update(json.load(f))


# COMET
import  comet
model = comet.load_from_checkpoint(comet.download_model("Unbabel/wmt22-cometkiwi-da"))
data = [
    {
        "src": x["source_text"],
        "mt": x["translation"]
    }
    for x in data_to_score
]
scores = model.predict(data, batch_size=8, gpus=1).scores # type: ignore
for score, x in zip(scores, data_to_score):
    data_cache[f"{x['lang1']}_#_{x['lang2']}_#_{x['source_text']}_#_{x['translation']}_#_{x['reference']}"]["CometKiwi22"] = score

# ChrF
for x in data_to_score:
    chrf = sacrebleu.corpus_chrf(
        [x["translation"]],
        [[x["reference"]]],
    ).score
    data_cache[f"{x['lang1']}_#_{x['lang2']}_#_{x['source_text']}_#_{x['translation']}_#_{x['reference']}"]["ChrF"] = chrf

with open("computed/autometrics_cache.json", "w") as f:
    json.dump(data_cache, f, indent=2, ensure_ascii=False)