import json
import os
import urllib.parse
import requests
import tiktoken
import random
import asyncio
import tqdm

os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

from last_translation_benchmark.utils import get_config

MODELS_VERIFIERS = [
    {"name": "Qwen 3.7 Flash", "model": "qwen/qwen3.7-flash"},
    {"name": "Qwen 3.7 Plus", "model": "qwen/qwen3.7-plus"},
    {"name": "Gemma 4", "model": "google/gemma-4-31b-it"},
    {"name": "Gemini 3.1 Pro", "model": "google/gemini-3.1-pro-preview"},
    {"name": "Gemini 3.5 Flash Lite", "model": "google/gemini-3.5-flash-lite"},
    {"name": "GPT-5.4-mini", "model": "openai/gpt-5.4-mini"},
]
API_URL = "https://last-translation-benchmark.vilda.net/api/llm"
DATA_FILE = "data/submissions.json"

COOKIES = {
    "ltb_user": urllib.parse.quote(get_config("LTB_API_USER")),
    "ltb_token": urllib.parse.quote(get_config("LTB_API_TOKEN"))
}

def get_prompt_verify(source_text: str, translation: str, rule: str, source_media: str | None) -> str:
    prompt = f"Your goal is to verify whether a translation fulfills a criterion.\n\nCriterion: {rule}\n\nInput: {source_text}\n\nTranslation to verify: {translation}\n\nOutput only pass or fail and nothing else."
    
    if source_media:
        mime = source_media.split(",")[0]
        context_type = "audio" if "audio" in mime else ("video" if "video" in mime else "image")
        prompt += f"\n\nUse the provided {context_type} as additional context."
        
    return prompt

def get_prompt_judge(source_text: str, translation: str, source_media: str | None) -> str:
    prompt = f"Your goal is to evaluate the quality of a translation. Translation quality is evaluated as follows:\n\n85-100% (Very Good): Complete meaning transfer; perfectly natural; no or minimal proofreading.\n65-80% (Good): Near complete transfer, minor inaccuracies; mostly natural, minor awkwardness; needs light proofreading.\n45-60% (Acceptable): Main ideas conveyed, noticeable inaccuracies or omissions; uneven naturalness, awkward phrasing; usable only after substantial revision.\n25-40% (Borderline): Partial transfer; frequent misinterpretation or omission confusing the message; often unnatural; requires major rewrite.\n0-20% (Not acceptable): Violation of meaning; large portions mistranslated, missing, or incoherent; unusable without complete retranslation.\n\nInput: {source_text}\n\nTranslation to evaluate: {translation}\n\nOutput a single number between 0 and 100, representing the quality of the translation, and nothing else."

    if source_media:
        mime = source_media.split(",")[0]
        context_type = "audio" if "audio" in mime else ("video" if "video" in mime else "image")
        prompt += f"\n\nUse the provided {context_type} as additional context."

    return prompt


def model_price_per_token(model_name: str, tokens: int) -> float:
    resp = requests.get("https://openrouter.ai/api/v1/models")
    resp.raise_for_status()
    models = resp.json()["data"]
    
    model = next((m for m in models if m["id"] == model_name), None)
    if model is None:
        raise ValueError(f"Model '{model_name}' unrecognized by OpenRouter.")
        
    price_per_token_input = float(model["pricing"]["prompt"])
    price_per_token_output = float(model["pricing"]["completion"])

    return tokens * price_per_token_input + tokens * price_per_token_output * 3


def estimate_tokens(text: str) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))

async def request_post_with_backoff(**kwargs):
    delay = 1
    await asyncio.sleep(0.5)
    for _ in range(3):
        response = requests.post(**kwargs)
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            print(response.text)
            print(f"Rate limited. Retrying in {delay} seconds...")
        else:
            raise Exception(f"Request failed with status {response.status_code}: {response.text}")
        await asyncio.sleep(delay)
        delay *= 2

    raise Exception(f"Request failed after 3 retries")

async def main():
    with open(DATA_FILE, "r") as f:
        submissions = json.load(f)

    # Estimate tokens
    prompts_verifier = []
    prompts_judge = []
    for sub in submissions:
        if sub["status"] != "accept":
            continue

        if not sub["source_text"] and sub["source_media"]:
            source_text_display = "(attached)"
        else:
            source_text_display = sub["source_text"]

        for mt_obj in sub["translations"]:
            for rule_obj in sub["verification_rules"]:
                prompts_verifier.append(get_prompt_verify(source_text_display, mt_obj["translation"], rule_obj["value"], sub["source_media"]))
            prompts_judge.append(get_prompt_judge(source_text_display, mt_obj["translation"], sub["source_media"]))

    text_count_verifier = estimate_tokens(" ".join(prompts_verifier))
    text_count_judge = estimate_tokens(" ".join(prompts_judge))
    print(f"Total tokens (verifier): {text_count_verifier}")
    for model in MODELS_VERIFIERS:
        print(f"Cost for {model['model']:<40} ${model_price_per_token(model['model'], text_count_verifier):.4f}")
    print(f"Total tokens (judge): {text_count_judge}")
    for model in MODELS_VERIFIERS:
        print(f"Cost for {model['model']:<40} ${model_price_per_token(model['model'], text_count_judge):.4f}")

    input("Do you wish to continue? (Ctrl+C to cancel)")

    pbar = tqdm.tqdm(submissions, desc="Processing submissions")
    pbar_desc = ""
    pbar_tasks = set()

    def update_pbar():
        pbar.set_description(f"{pbar_desc} with {', '.join(sorted(pbar_tasks))}")

    for sub in pbar:
        if sub["status"] != "accept":
            continue
        
        # take 10% of submissions, randomly
        if 0.1 < random.Random(f"{sub["id"]}|{0}").random():
            continue

        if not sub["source_text"] and sub["source_media"]:
            source_text_display = "(attached)"
        else:
            source_text_display = sub["source_text"]

        sub_changed = False
        for mt_obj in sub["translations"]:
            if mt_obj["model"].startswith("SKIP: "):
                continue

            pbar_desc = f"Verifying #{sub['id']} of {mt_obj['model']}"
            update_pbar()

            # verifier section
            if "verified_extra" not in mt_obj:
                mt_obj["verified_extra"] = {}

            async def _process_model_verifier(model):
                # skip if this model has already verified this translation
                if model["name"] in mt_obj["verified_extra"] and len(mt_obj["verified_extra"][model["name"]]) == len(sub["verification_rules"]):
                    return False

                results = []
                for rule_i, rule_obj in enumerate(sub["verification_rules"]):
                    prompt = get_prompt_verify(source_text_display, mt_obj["translation"], rule_obj["value"], sub["source_media"])

                    payload = {
                        "model": model["model"],
                        "prompt": prompt,
                    }
                    if sub["source_media"]:
                        payload["source_media"] = sub["source_media"]

                    progress_id = f"{rule_i}§{model['name']}"
                    try:
                        pbar_tasks.add(progress_id)
                        update_pbar()
                        response = await request_post_with_backoff(url=API_URL, json=payload, cookies=COOKIES)
                        if response.status_code == 200:
                            res_text = response.json()
                            if res_text is None:
                                print(f"  Empty LLM response for #{sub['id']}")
                                results.append(None)
                                continue

                            text_clean = res_text.strip().lower().strip(" \t\n\r.,!?\"'*").split()[-1]
                            if text_clean == "pass":
                                results.append(True)
                            elif text_clean == "fail":
                                results.append(False)
                            else:
                                print(f"  Invalid LLM response: {res_text}")
                                results.append(None)
                        else:
                            print(f"  Error {response.status_code}: {response.text}")
                            results.append(None)
                    except Exception as e:
                        print(f"  Request failed: {e}")
                        results.append(None)
                    finally:
                        pbar_tasks.discard(progress_id)
                        update_pbar()

                # store the result
                mt_obj["verified_extra"][model["name"]] = results
                return True

            # parallelize all rules at the same time
            tasks = await asyncio.gather(*[_process_model_verifier(model) for model in MODELS_VERIFIERS])
            sub_changed = sub_changed or any(tasks)

            # judge section
            if "judge_extra" not in mt_obj:
                mt_obj["judge_extra"] = {}

            async def _process_model_judge(model):
                # skip if this model has already verified this translation
                if model["name"] in mt_obj["judge_extra"]:
                    return False

                prompt = get_prompt_judge(source_text_display, mt_obj["translation"], sub["source_media"])

                payload = {
                    "model": model["model"],
                    "prompt": prompt,
                }
                if sub["source_media"]:
                    payload["source_media"] = sub["source_media"]

                progress_id = f"j§{model['name']}"
                result = None
                try:
                    pbar_tasks.add(progress_id)
                    update_pbar()
                    response = await request_post_with_backoff(url=API_URL, json=payload, cookies=COOKIES)
                    if response.status_code == 200:
                        res_text = response.json()
                        if res_text is None:
                            print(f"  Empty LLM response for #{sub['id']}")
                        else:
                            try:
                                # take only the last word, in case the model outputs extra text
                                text_clean = res_text.strip().lower().strip(" \t\n\r.,!?\"'*%").split()[-1]
                                result = int(float(text_clean))
                                if not (0 <= result <= 100):
                                    print(f"  Invalid LLM response: {res_text}")
                                    result = None
                            except ValueError:
                                print(f"  Invalid LLM response: {res_text}")
                                result = None
                    else:
                        print(f"  Error {response.status_code}: {response.text}")
                        result = None
                except Exception as e:
                    print(f"  Request failed: {e}")
                    result = None
                finally:
                    pbar_tasks.discard(progress_id)
                    update_pbar()

                mt_obj["judge_extra"][model["name"]] = result
                return True

            # parallelize all rules at the same time
            tasks = await asyncio.gather(*[_process_model_judge(model) for model in MODELS_VERIFIERS])
            sub_changed = sub_changed or any(tasks)

        if sub_changed:
            with open(DATA_FILE, "w") as f:
                json.dump(submissions, f, indent=2, ensure_ascii=False)

    # save finally
    with open(DATA_FILE, "w") as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())
