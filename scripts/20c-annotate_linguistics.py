# %%

import glob
import itertools
import json
import os
import urllib.parse

import frozendict
import tqdm
import utils
import asyncio

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

from last_translation_benchmark.utils import get_config

MODELS_ANNOTATORS = [
    {"name": "Gemini 3.1 Pro", "model": "google/gemini-3.1-pro-preview"},
    # {"name": "GPT-5.6 Sol Pro", "model": "openai/gpt-5.6-sol-pro"},
]
PROMPTS = [
    {"name": os.path.basename(file).removesuffix(".txt"), "prompt": open(file, "r").read()}
    for file in glob.glob("data/linguistics_prompts/*.txt")
]

DATA_LINGUISTICS_FILE = "data/linguistics_gold.json"
DATA_FILE = "data/submissions.json"

COOKIES = {
    "ltb_user": urllib.parse.quote(get_config("LTB_API_USER")),
    "ltb_token": urllib.parse.quote(get_config("LTB_API_TOKEN"))
}

FIRST_N = None
CHUNK_SIZE = 10

def evaluate_annotations_prec_recall(annotations: list[dict | None], annotations_gold: list[dict]) -> tuple[float, float]:
    out_precision = []
    out_recall = []
    for ann, ann_gold in zip(annotations, annotations_gold):
        if ann is None:
            out_precision.append(0.0)
            out_recall.append(0.0)
        else:
            ann = set(ann["main_tags"] or ann["parallel_tags_1"] or ann["parallel_tags_2"])
            ann_gold = set(ann_gold["main_tags"] or ann_gold["parallel_tags_1"] or ann_gold["parallel_tags_2"])

            ann = {tag.lower() for tag in ann}
            ann_gold = {tag.lower() for tag in ann_gold}

            true_positives = len(ann.intersection(ann_gold))
            precision = true_positives / len(ann) if ann else 0.0
            recall = true_positives / len(ann_gold) if ann_gold else 0.0
            out_precision.append(precision)
            out_recall.append(recall)

    return float(sum(out_precision)) / len(out_precision), float(sum(out_recall)) / len(out_recall)

async def annotate(model, prompt, line):
    signature = f"{model['name']} ||| {prompt['name']}"
    if signature in line["linguistics"]:
        return False

    # deduplicate and hide identity
    translations = list({
        frozendict.frozendict({
            "translation": mt_obj["translation"],
            "verified": tuple(mt_obj["verified_extra"]["Gemini 3.1 Pro"]),
        })
        for mt_obj in line["translations"]
        if not mt_obj["model"].startswith("SKIP: ") and "verified_extra" in mt_obj
    })
    if len(translations) < 5:
        translations = list({
            frozendict.frozendict({
                "translation": mt_obj["translation"],
                "verified": tuple(mt_obj["verified"]),
            })
            for mt_obj in line["translations"]
            if not mt_obj["model"].startswith("SKIP: ") and "verified" in mt_obj
        })

    translations.sort(key=lambda x: sum(x["verified"]), reverse=True)
    if len(translations) < 3:
        raise ValueError(f"Not enough unique translations for line {line['id']}: {len(translations)}")

    payload_example = {
        "source_text": line["source_text"],
        "translations": translations,
        "verification_rules": [x["value"] for x in line["verification_rules"]],
        "source_lang": line["source_lang"],
        "target_lang": line["target_lang"],
    }
    if line["source_instructions"] is not None:
        payload_example["source_instructions"] = line["source_instructions"]
    
    payload = {
        "model": model["model"],
        "prompt": (
            prompt["prompt"]
            + "\n\n-----\n\n"
            + json.dumps(payload_example, ensure_ascii=False, indent=2)
        ),
    }

    if line.get("source_media") is not None:
        payload["source_media"] = line["source_media"]
    
    response = await utils.request_post_with_backoff(url=get_config("LTB_API_URL"), json=payload, cookies=COOKIES)
    try:
        response.raise_for_status()
        res_text = response.json().strip("`").removeprefix("json").strip()
        result = json.loads(res_text)
        assert isinstance(result, dict)
        assert "main_tags" in result and isinstance(result["main_tags"], list)
        assert "parallel_tags_1" in result and isinstance(result["parallel_tags_1"], list)
        assert "parallel_tags_2" in result and isinstance(result["parallel_tags_2"], list)
        assert "observations" in result and isinstance(result["observations"], str)
    except Exception as e:
        print(e)
        print(f"Error in response: {response.status_code} - {response.text}")
        result = None

    line["linguistics"][signature] = result
    return True

async def main():
    with open(DATA_LINGUISTICS_FILE, "r") as f:
        data_linguistics = json.load(f)

    with open(DATA_FILE, "r") as f:
        submissions = json.load(f)

    for line in data_linguistics:
        matching_submissions = [
            sub for sub in submissions
            if (
                sub["status"] == "accept"
                and [mt_obj["translation"] for mt_obj in sub["translations"] if mt_obj["model"] == "human"][0] == line["human_translation"]
                and sub["source_lang"] == line["source_lang"] and sub["target_lang"] == line["target_lang"]
            )
        ]

        assert len(matching_submissions) == 1

        sub = matching_submissions[0]

        sub["linguistics"] = sub.get("linguistics", {})
        sub["linguistics"]["human"] = line["labels"]

    submissions_relevant = [
        sub for sub in submissions
        if "linguistics" in sub and "human" in sub["linguistics"]
    ]

    print(f"Loaded {len(submissions)} submissions\n")
    print(f"Loaded {len(submissions_relevant)} submissions with human annotations\n")

    for model, prompt in itertools.product(MODELS_ANNOTATORS, PROMPTS):
        signature = f"{model['name']} ||| {prompt['name']}"
        cost_input, cost_output = utils.model_price_per_token(model["model"])
        tokens = utils.estimate_tokens(prompt["prompt"]) * 2500
        print(f"Annotating with {signature} costs ${cost_input*tokens + cost_output*tokens:.2f}")
        annotations = []

        for chunk_i in tqdm.tqdm(range(0, len(submissions_relevant), CHUNK_SIZE), desc=f"{signature:<50}", unit="chunks"):
            sub_chunk = submissions_relevant[chunk_i:chunk_i+CHUNK_SIZE]
            sub_changed = any(await asyncio.gather(*[annotate(model, prompt, line) for line in sub_chunk]))

            # re-save *everything* after each chunk
            if sub_changed:
                with open(DATA_FILE, "w") as f:
                    json.dump(submissions, f, indent=2, ensure_ascii=False)

        annotations = [line["linguistics"][signature] for line in submissions_relevant[:FIRST_N]]
        annotations_gold = [line["linguistics"]["human"] for line in submissions_relevant[:FIRST_N]]
        precision, recall = evaluate_annotations_prec_recall(annotations, annotations_gold)
        print(f"Precision: {precision:.1%}, Recall: {recall:.1%}\n")

    with open(DATA_FILE, "w") as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())