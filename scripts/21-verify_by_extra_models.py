import json
import os
import urllib.parse
import requests
from tqdm import tqdm

os.chdir(os.path.dirname(os.path.abspath(__file__))+"/..")

from last_translation_benchmark.utils import get_config

# TODO: verify that this code is correct

MODEL = "google/gemma-4-31b-it"
API_URL = "https://last-translation-benchmark.vilda.net/api/llm"
DATA_FILE = "data/submissions.json"

COOKIES = {
    "ltb_user": urllib.parse.quote(get_config("LTB_API_USER")),
    "ltb_token": urllib.parse.quote(get_config("LTB_API_TOKEN"))
}

def verify_rule(sub, translation_text, rule_value):
    source_text = sub["source_text"]
    source_media = sub.get("source_media", None)
    
    if not source_text and source_media:
        source_text = "(attached)"
        
    prompt = f"Your goal is to verify whether a translation fulfills a criterion.\n\nCriterion: {rule_value}\n\nInput: {source_text}\n\nTranslation to verify: {translation_text}\n\nOutput only pass or fail and nothing else."
    
    if source_media:
        mime = source_media.split(",")[0]
        context_type = "audio" if "audio" in mime else ("video" if "video" in mime else "image")
        prompt += f"\n\nUse the provided {context_type} as additional context."
        
    payload = {
        "model": MODEL,
        "prompt": prompt,
    }
    if source_media:
        payload["source_media"] = source_media
        
    response = requests.post(API_URL, json=payload, cookies=COOKIES)
    if response.status_code == 200:
        text = response.json()
        text_clean = str(text).strip().lower().strip(" \t\n\r.,!?\"'*")
        if text_clean == "pass":
            return True
        elif text_clean == "fail":
            return False
        else:
            raise ValueError(f"Invalid LLM response: {text}")
    else:
        raise RuntimeError(f"Error {response.status_code}: {response.text}")

def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        submissions = json.load(f)

    for sub in tqdm(submissions, desc="Processing submissions"):
        if "verification_extra" not in sub:
            sub["verification_extra"] = {}
        if MODEL not in sub["verification_extra"]:
            sub["verification_extra"][MODEL] = {}
            
        changed = False
        
        # Re-use existing verifications if the submission was verified by the same model
        if sub["verification_model"] == MODEL:
            for t in sub["translations"]:
                t_model = t["model"]
                if "verified" in t and isinstance(t["verified"], list):
                    if t_model not in sub["verification_extra"][MODEL]:
                        sub["verification_extra"][MODEL][t_model] = t["verified"]
                        changed = True

        for t in sub["translations"]:
            t_model = t["model"]
            if t_model in sub["verification_extra"][MODEL]:
                continue
                
            print(f"Verifying translation {t_model} for submission {sub['id']} with {MODEL}...")
            translation_text = t["translation"]
            
            try:
                results = []
                for rule in sub["verification_rules"]:
                    res = verify_rule(sub, translation_text, rule["value"])
                    results.append(res)
                    
                sub["verification_extra"][MODEL][t_model] = results
                changed = True
                print(f"  Saved verification for submission {sub['id']}, model {t_model}.")
            except Exception as e:
                print(f"  Request failed: {e}")
                
        if changed:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(submissions, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
