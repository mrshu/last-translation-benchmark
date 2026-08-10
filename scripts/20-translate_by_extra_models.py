import json
import os
import urllib.parse
import requests
from tqdm import tqdm
import tiktoken
import asyncio
import random
import os
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

from last_translation_benchmark.utils import get_config

MODELS = [
    # {"name": "gpt-oss-20b", "model": "openai/gpt-oss-20b", "support_image": False, "support_audio": False, "support_video": False, "support_textonly": True},
    {"name": "Gemma 4 a4b", "model": "google/gemma-4-26b-a4b-it", "support_image": True, "support_audio": False, "support_video": True, "support_textonly": True},
    # {"name": "Gemini 3.6 Flash", "model": "google/gemini-3.6-flash", "support_image": True, "support_audio": True, "support_video": True, "support_textonly": True},
    {"name": "Gemini 3.5 Flash Lite", "model": "google/gemini-3.5-flash-lite", "support_image": True, "support_audio": True, "support_video": True, "support_textonly": True},
    # {"name": "Kimi K3", "model": "moonshotai/kimi-k3", "support_image": True, "support_audio": False, "support_video": False, "support_textonly": True},
    # {"name": "Claude Opus 4.8", "model": "anthropic/claude-opus-4.8", "support_image": True, "support_audio": False, "support_video": False, "support_textonly": True},
    # {"name": "Minimax M3", "model": "minimax/minimax-m3", "support_image": True, "support_audio": False, "support_video": True, "support_textonly": True},
    # {"name": "GLM 5.2", "model": "z-ai/glm-5.2", "support_image": False, "support_audio": False, "support_video": False, "support_textonly": True},
    # {"name": "Nemotron 3 Ultra", "model": "nvidia/nemotron-3-ultra-550b-a55b", "support_image": False, "support_audio": False, "support_video": False, "support_textonly": True},
    # {"name": "Qwen 3.7 Flash", "model": "qwen/qwen3.7-flash", "support_image": True, "support_audio": False, "support_video": True, "support_textonly": True},
    # {"name": "DeepSeek V4 Pro", "model": "deepseek/deepseek-v4-pro", "support_image": False, "support_audio": False, "support_video": False, "support_textonly": True},
]
API_URL = "https://last-translation-benchmark.vilda.net/api/llm"
DATA_FILE = "data/submissions.json"

COOKIES = {
    "ltb_user": urllib.parse.quote(get_config("LTB_API_USER")),
    "ltb_token": urllib.parse.quote(get_config("LTB_API_TOKEN"))
}

def get_prompt(sub):
    text = sub["source_text"]
    src_lang = sub["source_lang"]
    tgt_lang = sub["target_lang"]
    source_media = sub["source_media"]
    source_instructions = sub["source_instructions"]

    if not source_media:
        prompt = f"Translate the following text from {src_lang} to {tgt_lang}. Output only the translation and nothing else:\n{text}"
    else:
        mime = source_media.split(",")[0]
        has_audio = "audio" in mime
        has_video = "video" in mime
        context_type = "audio" if has_audio else ("video" if has_video else "image")

        if text:
            prompt = (
                f"Translate the following text from {src_lang} to {tgt_lang}. "
                f"Use the provided {context_type} as additional context. "
                f"Output only the translation and nothing else:\n{text}"
            )
        else:
            prompt = f"Translate the provide {context_type} from {src_lang} to {tgt_lang}. Output only the textual translation and nothing else."
            
    if source_instructions:
        prompt += f'\nAdditional instructions for this translation are: "{source_instructions}"'
        
    return prompt

def model_price_per_token(model_name: str, tokens: int) -> float:
    resp = requests.get("https://openrouter.ai/api/v1/models")
    resp.raise_for_status()
    models = resp.json().get("data", [])
    
    model = next((m for m in models if m["id"] == model_name), None)
    if model is None:
        raise ValueError(f"Model '{model_name}' unrecognized by OpenRouter.")
        
    # OpenRouter returns pricing as strings representing cost per token.
    price_per_token_input = float(model["pricing"]["prompt"])
    price_per_token_output = float(model["pricing"]["completion"])

    return tokens * price_per_token_input + tokens * price_per_token_output


def estimate_tokens(text: str) -> int:
    encoder = tiktoken.get_encoding("cl100k_base")
    return len(encoder.encode(text))


async def main():
    with open(DATA_FILE, "r") as f:
        submissions = json.load(f)

    text_count = estimate_tokens(" ".join([get_prompt(sub) for sub in submissions if sub["status"] == "accept"]))
    print(f"Total tokens: {text_count}")
    for model in MODELS:
        print(f"Cost for {model['model']:<40} ${model_price_per_token(model["model"], text_count):.4f}")

    input("Do you wish to continue? (Ctrl+C to cancel)")

    pbar = tqdm(submissions, desc="Processing submissions")
    for sub in pbar:
        # skip submissions which are not accepted
        if sub["status"] != "accept":
            continue

        sub_changed = False
        for model in MODELS:
            # skip if this model has already provided a translation
            if any(t["model"] == model["name"] for t in sub["translations"]):
                continue

            if sub["source_media"]:
                mime = sub["source_media"].split(",")[0]
                has_audio = "audio" in mime
                has_video = "video" in mime
                has_image = not has_audio and not has_video
                if (
                    (has_audio and not model["support_audio"]) or
                    (has_video and not model["support_video"]) or
                    (has_image and not model["support_image"])
                ):
                    continue

            prompt = get_prompt(sub)
            payload = {
                "model": model["model"],
                "prompt": prompt,
            }
            if sub["source_media"]:
                payload["source_media"] = sub["source_media"]

            pbar.set_description(f"Translating #{sub['id']} with {model['model']}")
            try:
                response = requests.post(url=API_URL, json=payload, cookies=COOKIES)
                if response.status_code == 200:
                    translation = response.json()
                    new_t = {
                        "model": model["name"],
                        "translation": translation,
                    }
                    
                    if "translations" not in sub:
                        sub["translations"] = []
                    # Just add it to the list
                    sub["translations"].append(new_t)
                    sub_changed = True

                else:
                    print(f"  Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"  Request failed: {e}")

        if sub_changed:
            # save on each finalized changed submission
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(submissions, f, indent=2, ensure_ascii=False)


    # save finally
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(main())
