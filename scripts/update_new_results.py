import json
import os
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
history_path = os.path.join(base_dir, "data", "history.json")

# Load databases
with open(matches_path, "r", encoding="utf-8") as f:
    matches_db = json.load(f)

with open(history_path, "r", encoding="utf-8") as f:
    history_db = json.load(f)

# Define outcomes for the 5 finished matches
new_results = {
    "match_260720_104": {
        "actual_result": "西班牙 0-0 阿根廷",
        "status": "✅ 预测命中",
        "home_goals": 0,
        "away_goals": 0,
        "is_correct": True,
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": False,
            "aggressive": False,
            "upset": False,
            "conservative": True,
            "half_full": True,
            "over_under": False,
            "most_likely_score": True
        }
    },
    "match_260719_203": {
        "actual_result": "埃夫斯堡 1-3 天狼星",
        "status": "✅ 预测命中",
        "home_goals": 1,
        "away_goals": 3,
        "is_correct": True,
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": True,
            "aggressive": False,
            "upset": True,
            "conservative": True,
            "half_full": True,
            "over_under": True,
            "most_likely_score": True
        }
    },
    "match_260719_204": {
        "actual_result": "哈尔姆斯 0-2 赫根",
        "status": "✅ 预测命中",
        "home_goals": 0,
        "away_goals": 2,
        "is_correct": True,
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": True,
            "aggressive": False,
            "upset": False,
            "conservative": True,
            "half_full": False,
            "over_under": False,
            "most_likely_score": False
        }
    },
    "match_260719_205": {
        "actual_result": "哈马比 4-0 代格福什",
        "status": "✅ 预测命中",
        "home_goals": 4,
        "away_goals": 0,
        "is_correct": True,
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": True,
            "aggressive": False,
            "upset": False,
            "conservative": True,
            "half_full": True,
            "over_under": True,
            "most_likely_score": False
        }
    },
    "match_260719_206": {
        "actual_result": "雅罗 0-0 国际图尔",
        "status": "❌ 预测偏差",
        "home_goals": 0,
        "away_goals": 0,
        "is_correct": False,
        "predictions_correctness": {
            "recommendation": False,
            "primary_bet": False,
            "mainstream": False,
            "aggressive": False,
            "upset": False,
            "conservative": False,
            "half_full": False,
            "over_under": False,
            "most_likely_score": True
        }
    }
}

updated_count = 0
today_str = datetime.now().strftime("%Y-%m-%d")

for m in matches_db["matches"]:
    mid = m["id"]
    if mid in new_results and m["status"] == "pending":
        info = new_results[mid]
        m["status"] = "finished"
        m["ultimate_conclusion"]["actual_result"] = info["actual_result"]
        m["ultimate_conclusion"]["status"] = info["status"]
        
        # Update forms
        h_form = m["team_stats"]["home"].get("form", [])
        a_form = m["team_stats"]["away"].get("form", [])
        if info["home_goals"] > info["away_goals"]:
            h_form.append("W")
            a_form.append("L")
        elif info["home_goals"] < info["away_goals"]:
            h_form.append("L")
            a_form.append("W")
        else:
            h_form.append("D")
            a_form.append("D")
            
        m["team_stats"]["home"]["form"] = h_form[-6:]
        m["team_stats"]["away"]["form"] = a_form[-6:]
        
        # Build predictions correctness
        pred_obj = {}
        for k, v_correct in info["predictions_correctness"].items():
            val = "--"
            if k == "recommendation":
                val = m["ultimate_conclusion"].get("recommendation", "--")
            elif k == "primary_bet":
                val = m["ultimate_conclusion"].get("primary_bet", "--")
            else:
                val = m.get("conclusions", {}).get(k, "--")
            
            pred_obj[k] = {
                "val": val,
                "correct": v_correct
            }
            
        # Append record to history
        record = {
            "match_id": mid,
            "league": m["league"],
            "home": m["home"],
            "away": m["away"],
            "date": today_str,
            "actual_result": info["actual_result"],
            "is_correct": info["is_correct"],
            "confidence": m["ultimate_conclusion"]["confidence"],
            "predictions": pred_obj
        }
        
        # Check if already exists in history to prevent duplicates
        if not any(x["match_id"] == mid for x in history_db["records"]):
            history_db["records"].append(record)
            
        updated_count += 1

# Save matches.json
with open(matches_path, "w", encoding="utf-8") as f:
    json.dump(matches_db, f, ensure_ascii=False, indent=2)

# Save history.json
history_db["total_predictions"] = len(history_db["records"])
history_db["correct_predictions"] = sum(1 for x in history_db["records"] if x["is_correct"])
history_db["accuracy_rate"] = round(history_db["correct_predictions"] / history_db["total_predictions"], 4)

with open(history_path, "w", encoding="utf-8") as f:
    json.dump(history_db, f, ensure_ascii=False, indent=2)

print(f"✅ Settle results: Updated {updated_count} matches in matches.json and synchronized history.json.")
print(f"📊 Accuracy stats: Total {history_db['total_predictions']}, Correct {history_db['correct_predictions']}, Accuracy {history_db['accuracy_rate']}")
