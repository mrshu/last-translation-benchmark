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

MODEL = "google/gemini-3.1-pro-preview"
PROMPT_FILE = "data/linguistics_prompt.txt"
DATA_FILE = "data/submissions.json"

COOKIES = {
    "ltb_user": urllib.parse.quote(get_config("LTB_API_USER")),
    "ltb_token": urllib.parse.quote(get_config("LTB_API_TOKEN"))
}

CHUNK_SIZE = 20

async def annotate(model, prompt, sub):
    if "linguistics" in sub:
        return False

    # deduplicate and hide identity
    translations = list({
        frozendict.frozendict({
            "translation": mt_obj["translation"],
            "verified": tuple(mt_obj["verified_extra"]["Gemini 3.1 Pro"]),
        })
        for mt_obj in sub["translations"]
        if not mt_obj["model"].startswith("SKIP: ") and "verified_extra" in mt_obj and "Gemini 3.1 Pro" in mt_obj["verified_extra"]
    })
    if len(translations) < 5:
        translations = list({
            frozendict.frozendict({
                "translation": mt_obj["translation"],
                "verified": tuple(mt_obj["verified"]),
            })
            for mt_obj in sub["translations"]
            if not mt_obj["model"].startswith("SKIP: ") and "verified" in mt_obj
        })

    translations.sort(key=lambda x: sum(x["verified"]), reverse=True)
    if len(translations) < 2:
        print(f"Not enough unique translations for line {sub['id']}: {len(translations)}")
        return False

    payload_example = {
        "source_text": sub["source_text"],
        "translations": translations,
        "verification_rules": sub["verification_rules"],
        "source_lang": sub["source_lang"],
        "target_lang": sub["target_lang"],
    }
    if sub["source_instructions"] is not None:
        payload_example["source_instructions"] = sub["source_instructions"]
    
    payload = {
        "model": model,
        "prompt": (
            prompt
            + "\n\n-----\n\n"
            + json.dumps(payload_example, ensure_ascii=False, indent=2)
        ),
    }

    if sub.get("source_media") is not None:
        payload["source_media"] = sub["source_media"]
    
    response = await utils.request_post_with_backoff(url=get_config("LTB_API_URL"), json=payload, cookies=COOKIES)
    try:
        response.raise_for_status()
        res_text = response.json().strip("`").removeprefix("json").strip().strip("`")
        result = json.loads(res_text)
        assert isinstance(result, dict)
        assert "main_tags" in result and isinstance(result["main_tags"], list)
        assert "parallel_tags_1" in result and isinstance(result["parallel_tags_1"], list)
        assert "parallel_tags_2" in result and isinstance(result["parallel_tags_2"], list)
        assert "observations" in result and isinstance(result["observations"], str)
        sub["linguistics"] = result
        return True
    except Exception as e:
        print(e)
        print(f"Error in response: {response.status_code} - {response.text}")
        return False

async def main():
    with open(PROMPT_FILE, "r") as f:
        prompt = f.read()

    with open(DATA_FILE, "r") as f:
        submissions = json.load(f)

    submissions_accepted = [sub for sub in submissions if sub["status"] == "accept"]

    print(f"Loaded {len(submissions)} submissions\n")

    cost_input, cost_output = utils.model_price_per_token(MODEL)
    tokens = utils.estimate_tokens(prompt) * 2500
    print(f"Annotating with {MODEL} costs ${cost_input*tokens + cost_output*tokens:.2f}")

    for chunk_i in tqdm.tqdm(range(0, len(submissions_accepted), CHUNK_SIZE), unit="chunks"):
        sub_chunk = submissions_accepted[chunk_i:chunk_i+CHUNK_SIZE]
        sub_changed = any(await asyncio.gather(*[annotate(MODEL, prompt, sub) for sub in sub_chunk]))

        # re-save *everything* after each chunk
        if sub_changed:
            with open(DATA_FILE, "w") as f:
                json.dump(submissions, f, indent=2, ensure_ascii=False)

    with open(DATA_FILE, "w") as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())