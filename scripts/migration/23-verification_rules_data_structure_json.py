import json
import os


def migrate_json(filepath):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    changed = 0
    
    for sub in data:
        if "verification_rules" in sub:
            new_rules = []
            for r in sub["verification_rules"]:
                if isinstance(r, dict) and "value" in r:
                    new_rules.append(r["value"])
                    changed += 1
                else:
                    new_rules.append(r)
            sub["verification_rules"] = new_rules
                
    if changed:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Migrated {changed} rules in {filepath} successfully.")
    else:
        print("No changes were needed.")

if __name__ == "__main__":
    migrate_json("data/submissions.json")
