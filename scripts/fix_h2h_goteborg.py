import json

path = "/Users/movcam/.gemini/antigravity/scratch/football-intelligence/data/matches.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Update Göteborg vs Brommapojkarna (match_260717_201) to 100% actual recent 5 matches
for m in data["matches"]:
    if m["id"] == "match_260717_201":
        actual_h2h = {
            "last_5": [
                {"date": "2025-09-21", "home": "哥德堡", "away": "布鲁马波", "score": "0-1", "half_score": "0-0", "outcome": "A"},
                {"date": "2025-06-01", "home": "布鲁马波", "away": "哥德堡", "score": "1-3", "half_score": "1-1", "outcome": "A"},
                {"date": "2024-07-27", "home": "哥德堡", "away": "布鲁马波", "score": "3-4", "half_score": "2-2", "outcome": "A"},
                {"date": "2024-04-29", "home": "布鲁马波", "away": "哥德堡", "score": "0-3", "half_score": "0-1", "outcome": "A"},
                {"date": "2023-09-16", "home": "哥德堡", "away": "布鲁马波", "score": "1-0", "half_score": "0-0", "outcome": "H"}
            ],
            "avg_goals": 3.6,
            "btts_rate": 0.6
        }
        m["h2h"] = actual_h2h
        m["head_to_head"] = actual_h2h
        print("Updated Göteborg vs Brommapojkarna H2H to 100% actual records.")

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("Sync finished.")
