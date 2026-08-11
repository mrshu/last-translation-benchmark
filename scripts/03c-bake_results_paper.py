# %%

import collections
import json

import statistics
import os
import utils_fig
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__))+ "/../")

os.makedirs("computed/", exist_ok=True)

with open("data/users.json", "r") as f:
    data_users = json.load(f)

with open("data/submissions.json", "r") as f:
    data_submissions = json.load(f)

data_out = {}

user_counts = collections.defaultdict(set)
user_counts["registered"] = set(x["username"] for x in data_users)
user_counts["submitted"] = set(x["username"] for x in data_submissions)
user_counts["accepted"] = set(x["username"] for x in data_submissions if x["status"] == "accept")
user_counts["reviewers"] = set(x["reviewed_by"] for x in data_submissions if x["reviewed_by"] is not None)
user_counts["admins"] = set(x["username"] for x in data_users if "admin" in x["roles"])

data_out["user_counts"] = {k: len(v) for k, v in user_counts.items()}

# language distribution
language_counts = collections.Counter()
for submission in data_submissions:
    language_counts[submission["source_lang"].strip()] += 1
    language_counts[submission["target_lang"].strip()] += 1


data_out["language_counts"] = dict(language_counts.most_common())

def date_to_delta(date_str):
    # subtract fom 2026-05-01
    # 2026-05-26 23:23
    # remove micros?
    if date_str.count(":") == 2:
        date_str = date_str.rsplit(":", 1)[0]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    delta = date_obj - datetime(2026, 5, 1)
    return delta.days

# number of accepted, rejected, pending submissions
status_counts = collections.Counter()
delta_today = date_to_delta(datetime.now().strftime("%Y-%m-%d %H:%M"))
dates_pending = [0]*(delta_today+1)
dates_accepted = [0]*(delta_today+1)
dates_returned = [0]*(delta_today+1)
for submission in data_submissions:
    status_counts[submission["status"]] += 1
    dates = [submission["created_at"]] + [x["created_at"] for x in submission["comments"]]
    delta_first = date_to_delta(min(dates))
    delta_last = date_to_delta(max(dates))

    if submission["status"] == "accept":
        for i in range(delta_last+1, delta_today+1): 
            dates_accepted[i] += 1
        for i in range(delta_first, delta_last):
            dates_pending[i] += 1
    elif submission["status"] == "return":
        for i in range(delta_first, delta_last+1):
            dates_pending[i] += 1
        for i in range(delta_last, delta_today+1):
            dates_returned[i] += 1
    elif submission["status"] == "pending":
        for i in range(delta_first, delta_today+1):
            dates_pending[i] += 1

dates_accepted = np.array(dates_accepted)
dates_pending = np.array(dates_pending)
dates_returned = np.array(dates_returned)

plt.figure(figsize=(4, 2.5))
plt.plot(range(delta_today+1), dates_accepted, color="green", linewidth=2)
plt.plot(range(delta_today+1), dates_pending, color="orange", linewidth=2)
plt.plot(range(delta_today+1), dates_returned, color="red", linewidth=2)
plt.plot(range(delta_today+1), dates_accepted+dates_pending+dates_returned, color="black", linewidth=2)
plt.ylabel("Number of submissions")
plt.xlabel("Days since 2026-05-01")
plt.text(
    x=delta_today,
    y=dates_accepted[-1],
    s=f" Accepted: {status_counts['accept']}",
    ha="left", va="center"
)
plt.text(
    x=delta_today,
    y=dates_pending[-1],
    s=f"\n\n Pending: {status_counts['pending']}",
    ha="left", va="center",
)
plt.text(
    x=delta_today,
    y=dates_returned[-1],
    s=f" Returned: {status_counts['return']}",
    ha="left", va="center",
)
plt.text(
    x=delta_today,
    y=dates_accepted[-1]+dates_pending[-1]+dates_returned[-1],
    s=f" Total: {len(data_submissions)}",
    ha="left", va="center",
)

plt.gca().spines[["top", "right"]].set_visible(False)
plt.tight_layout(pad=0.5)
plt.gca().patch.set_alpha(0)
plt.gcf().patch.set_alpha(0)
plt.savefig("computed/collection_progress.svg")
plt.show()

data_out["status_counts"] = dict(status_counts.most_common())

# number of quota_used per all submissions
data_out["quota_per_submission"] = f"{sum(x["quota_used"] for x in data_users if x["quota_used"]) / len(data_submissions):.1f}"

# compute per model results


data_models = collections.defaultdict(lambda: collections.defaultdict(list))

with open("computed/autometrics_cache.json", "r") as f:
    data_autometrics_cache = json.load(f)
for submission in data_submissions:
    human_translation = [x for x in submission["translations"] if x["model"] == "human"][0]["translation"]
    for entry in submission["translations"]:
        autometrics_key = f"{submission['source_lang']}_#_{submission['target_lang']}_#_{submission['source_text']}_#_{entry['translation']}_#_{human_translation}"
        if autometrics_key in data_autometrics_cache:
            for metric, score in data_autometrics_cache[autometrics_key].items():
                if score is not None:
                    data_models[entry["model"]]["AUTOMETRIC: " + metric].append(score)
        if "verified" in entry:
            data_models[entry["model"]]["VERIFIER: interactive"].append(all(entry["verified"]))
        for verifier, results in entry.get("verified_extra", {}).items():
            if all(x is not None for x in results):
                data_models[entry["model"]]["VERIFIER: " + verifier].append(all(results))
        for verifier, result in entry.get("judge_extra", {}).items():
            if result is not None:
                data_models[entry["model"]]["JUDGE: " + verifier].append(result)

# fake for now
for model, results in data_models.items():
    results["HUMAN: standalone"] = [70.0]
    results["HUMAN: with rules"] = [50.0]

llm_whitelist = {
    "interactive",
    "Qwen 3.7 Flash",
    "Qwen 3.7 Plus",
    "Gemma 4",
    "Gemini 3.1 Pro",
    "Gemini 3.5 Flash Lite",
    "GPT-5.4-mini",
}

model_whitelist = {
    "human",
    "Gemma 4",
    "Gemini 2.5 Flash",
    "Llama 4 Maverick", 
    "GPT-5.4 Mini",
    "Claude Haiku 4.5",
    "Claude Sonnet 4.5",
    "Cohere Command A", 
    "Qwen 3.7 Plus",
    "Gemini 3.5 Flash Lite",
    "Qwen 3.7 Flash",
    "gpt-oss-20b",
    "Kimi K3",
    "Google Translate",
    "Lara",
    "Nemotron 3 Ultra",
    "Deepseek V4 Pro",
    "TranslateGemma",
    "Tower+",
    "GemmaX2-28-9B",
    "HY-MT2",
    "Seed-X-PPO-7B",
    "NLLB-200",
}

all_keys = {
    k for results in data_models.values()
    for k in results.keys()
    if (not (k.startswith("VERIFIER: ")) and (not k.startswith("JUDGE: "))) or any(k.endswith(k_allowed) for k_allowed in llm_whitelist)
}

data_out["model_results"] = {
    model: {
        key: statistics.mean(results[key]) if key in results else None
        for key in all_keys
    }
    for model, results in data_models.items()
    if model in model_whitelist
    # if any(len(result) >= 50 for result in results.values())
}
                
with open("computed/bake_results.json", "w") as f:
    json.dump(data_out, f, indent=2, ensure_ascii=False)