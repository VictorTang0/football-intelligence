import json
import os
from datetime import datetime

base_dir = r"D:\GitHub File\football-intelligence"
matches_path = os.path.join(base_dir, "data", "matches.json")
history_path = os.path.join(base_dir, "data", "history.json")

# 1. Load data
with open(matches_path, "r", encoding="utf-8") as f:
    matches_db = json.load(f)

with open(history_path, "r", encoding="utf-8") as f:
    history_db = json.load(f)

# Define outcomes for the 6 finished matches
results_info = {
    "match_260717_204": {
        "actual_result": "巴伊亚 0-0 沙佩科",
        "status": "❌ 预测偏差",
        "home_goals": 0,
        "away_goals": 0,
        "is_correct": False,
        "half_full_actual": "平/平",
        "predictions_correctness": {
            "recommendation": False,
            "primary_bet": False,
            "mainstream": False,
            "aggressive": False,
            "upset": True,
            "conservative": True,
            "half_full": False,
            "over_under": True,
            "most_likely_score": False
        }
    },
    "match_260717_205": {
        "actual_result": "弗鲁米嫩 0-0 布拉干RB",
        "status": "❌ 预测偏差",
        "home_goals": 0,
        "away_goals": 0,
        "is_correct": False,
        "half_full_actual": "平/平",
        "predictions_correctness": {
            "recommendation": False,
            "primary_bet": False,
            "mainstream": False,
            "aggressive": False,
            "upset": True,
            "conservative": True,
            "half_full": False,
            "over_under": True,
            "most_likely_score": False
        }
    },
    "match_260717_206": {
        "actual_result": "米拉索尔 0-0 格雷米奥",
        "status": "❌ 预测偏差",
        "home_goals": 0,
        "away_goals": 0,
        "is_correct": False,
        "half_full_actual": "平/平",
        "predictions_correctness": {
            "recommendation": False,
            "primary_bet": False,
            "mainstream": False,
            "aggressive": False,
            "upset": True,
            "conservative": True,
            "half_full": False,
            "over_under": True,
            "most_likely_score": False
        }
    },
    "match_260717_207": {
        "actual_result": "纳什维尔 1-0 亚特联",
        "status": "✅ 预测命中",
        "home_goals": 1,
        "away_goals": 0,
        "is_correct": True,
        "half_full_actual": "主/主",
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": True,
            "aggressive": True,
            "upset": False,
            "conservative": True,
            "half_full": True,
            "over_under": True,
            "most_likely_score": True
        }
    },
    "match_260717_208": {
        "actual_result": "洛城银河 0-3 洛杉矶FC",
        "status": "✅ 预测命中",
        "home_goals": 0,
        "away_goals": 3,
        "is_correct": True,
        "half_full_actual": "客/客",
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": True,
            "aggressive": True,
            "upset": False,
            "conservative": True,
            "half_full": True,
            "over_under": True,
            "most_likely_score": False
        }
    },
    "match_260719_103": {
        "actual_result": "法国 1-1 英格兰",
        "status": "✅ 预测命中",
        "home_goals": 1,
        "away_goals": 1,
        "is_correct": True,
        "half_full_actual": "平/平",
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": False,
            "mainstream": False,
            "aggressive": False,
            "upset": True,
            "conservative": False,
            "half_full": False,
            "over_under": False,
            "most_likely_score": False
        }
    }
}

updated_count = 0
new_records = []
today_str = datetime.now().strftime("%Y-%m-%d")

for m in matches_db["matches"]:
    mid = m["id"]
    if mid in results_info and m["status"] == "pending":
        # Kickoff safety check: Only update if the match is actually finished
        kickoff_str = m.get("kickoff", "")
        try:
            from datetime import datetime, timezone, timedelta
            kickoff_dt = datetime.fromisoformat(kickoff_str)
            now = datetime.now(kickoff_dt.tzinfo)
            
            time_diff = now - kickoff_dt
            if time_diff < timedelta(minutes=150):
                if time_diff < timedelta(minutes=0):
                    print(f"⚠️ Skipping match {m['home']} vs {m['away']} ({mid}): Match has NOT started yet (Kickoff: {kickoff_str})")
                else:
                    print(f"⚠️ Skipping match {m['home']} vs {m['away']} ({mid}): Match is currently IN PROGRESS (Kickoff: {kickoff_str})")
                continue
        except Exception as e:
            print(f"⚠️ Time parsing error for {mid}: {e}")
            continue
            
        info = results_info[mid]
        # Update match status and results
        m["status"] = "finished"
        m["ultimate_conclusion"]["actual_result"] = info["actual_result"]
        m["ultimate_conclusion"]["status"] = info["status"]
        
        # Update team forms
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
        
        # Build history record
        pred_obj = {}
        for k, v_correct in info["predictions_correctness"].items():
            # Get predicted val
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
        new_records.append(record)
        updated_count += 1

# Save matches.json
with open(matches_path, "w", encoding="utf-8") as f:
    json.dump(matches_db, f, ensure_ascii=False, indent=2)

print(f"Updated {updated_count} matches in matches.json to finished.")

# 2. Update history.json
for r in new_records:
    # Avoid duplicates
    if not any(x["match_id"] == r["match_id"] for x in history_db["records"]):
        history_db["records"].append(r)

history_db["total_predictions"] = len(history_db["records"])
history_db["correct_predictions"] = sum(1 for x in history_db["records"] if x["is_correct"])
history_db["accuracy_rate"] = round(history_db["correct_predictions"] / history_db["total_predictions"], 4)

with open(history_path, "w", encoding="utf-8") as f:
    json.dump(history_db, f, ensure_ascii=False, indent=2)

print(f"Updated history.json. Total predictions: {history_db['total_predictions']}, Accuracy: {history_db['accuracy_rate']}")
