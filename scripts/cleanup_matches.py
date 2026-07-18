import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
input_path = os.path.join(base_dir, "data", "new_matches_input.json")

if not os.path.exists(matches_path) or not os.path.exists(input_path):
    print("Files missing for cleanup.")
    exit(1)

with open(matches_path, "r", encoding="utf-8") as f:
    database = json.load(f)

with open(input_path, "r", encoding="utf-8") as f:
    new_input = json.load(f)

cleaned_matches = []
removed_matches = []
for m in database["matches"]:
    # We always keep finished matches
    if m["status"] == "finished":
        cleaned_matches.append(m)
    else:
        removed_matches.append(f"{m['home']} vs {m['away']} ({m['id']})")

database["matches"] = cleaned_matches

with open(matches_path, "w", encoding="utf-8") as f:
    json.dump(database, f, ensure_ascii=False, indent=2)

print(f"Cleanup completed! Removed {len(removed_matches)} obsolete/incorrect pending matches:")
for r in removed_matches:
    print(f"  - {r}")
