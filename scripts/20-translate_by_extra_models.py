import json
import os
import urllib.parse
import requests
from tqdm import tqdm
import os
os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

from last_translation_benchmark.utils import get_config

MODEL = "google/gemma-4-31b-it"
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
    source_media = sub.get("source_media", None)
    source_instructions = sub.get("source_instructions", None)

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

def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        submissions = json.load(f)

    for sub in tqdm(submissions, desc="Processing submissions"):
        # Skip if this model has already provided a translation
        # if any(t["model"] == MODEL for t in sub["translations"]):
        #     continue

        prompt = get_prompt(sub)
        payload = {
            "model": MODEL,
            "prompt": prompt,
        }
        if sub.get("source_media", None):
            payload["source_media"] = sub.get("source_media", None)

        print(f"Translating submission {sub['id']} with {MODEL}...")
        try:
            response = requests.post(API_URL, json=payload, cookies=COOKIES)
            if response.status_code == 200:
                translation = response.json()
                new_t = {
                    "model": MODEL,
                    "translation": translation,
                }
                
                if "translations" not in sub:
                    sub["translations"] = []
                # Just add it to the list
                sub["translations"].append(new_t)

                # Save on each received translation
                with open(DATA_FILE, "w") as f:
                    json.dump(submissions, f, indent=2, ensure_ascii=False)
                print(f"  Saved translation for submission {sub['id']}.")
            else:
                print(f"  Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"  Request failed: {e}")

if __name__ == "__main__":
    main()
