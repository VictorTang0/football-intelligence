import json
import os

base_dir = r"D:\GitHub File\football-intelligence"
matches_path = os.path.join(base_dir, "data", "matches.json")
history_path = os.path.join(base_dir, "data", "history.json")

# 1. Load data
with open(matches_path, "r", encoding="utf-8") as f:
    matches_db = json.load(f)

with open(history_path, "r", encoding="utf-8") as f:
    history_db = json.load(f)

# Define correct outcomes for the 5 finished matches
results_info = {
    "match_260717_204": {
        "actual_result": "巴伊亚 2-0 沙佩科",
        "status": "✅ 预测命中",
        "home_goals": 2,
        "away_goals": 0,
        "is_correct": True,
        "half_full_actual": "主/主",
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": True,
            "upset": False,
            "aggressive": False,
            "conservative": True,
            "half_full": True,
            "over_under": False,
            "most_likely_score": False
        }
    },
    "match_260717_205": {
        "actual_result": "弗鲁米嫩 1-1 布拉干RB",
        "status": "❌ 预测偏差",
        "home_goals": 1,
        "away_goals": 1,
        "is_correct": False,
        "half_full_actual": "平/平",
        "predictions_correctness": {
            "recommendation": False,
            "primary_bet": False,
            "mainstream": False,
            "upset": True,
            "aggressive": False,
            "conservative": False,
            "half_full": False,
            "over_under": False,
            "most_likely_score": False
        }
    },
    "match_260717_206": {
        "actual_result": "米拉索尔 2-1 格雷米奥",
        "status": "✅ 预测命中",
        "home_goals": 2,
        "away_goals": 1,
        "is_correct": True,
        "half_full_actual": "主/主",
        "predictions_correctness": {
            "recommendation": True,
            "primary_bet": True,
            "mainstream": True,
            "upset": False,
            "aggressive": False,
            "conservative": True,
            "half_full": False,
            "over_under": False,
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
            "upset": False,
            "aggressive": True,
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
            "upset": False,
            "aggressive": True,
            "conservative": True,
            "half_full": True,
            "over_under": True,
            "most_likely_score": False
        }
    }
}

# 1. Reset match_260718_103 to pending
for m in matches_db["matches"]:
    mid = m["id"]
    if mid == "match_260718_103":
        m["status"] = "pending"
        m["ultimate_conclusion"]["actual_result"] = None
        m["ultimate_conclusion"]["status"] = None
        # Remove the last form element (which was D)
        if len(m["team_stats"]["home"]["form"]) > 0:
            m["team_stats"]["home"]["form"].pop()
        if len(m["team_stats"]["away"]["form"]) > 0:
            m["team_stats"]["away"]["form"].pop()
        print("Reverted match_260718_103 (法国 vs 英格兰) back to pending.")
        
    elif mid in results_info:
        info = results_info[mid]
        # Update/Correct match status and results
        m["status"] = "finished"
        m["ultimate_conclusion"]["actual_result"] = info["actual_result"]
        m["ultimate_conclusion"]["status"] = info["status"]
        
        # Replace the last element of form lists with corrected form
        h_form = m["team_stats"]["home"].get("form", [])
        a_form = m["team_stats"]["away"].get("form", [])
        
        # Remove the dummy 'D' we added in the previous run
        if len(h_form) > 0: h_form.pop()
        if len(a_form) > 0: a_form.pop()
        
        # Append correct form
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
        print(f"Corrected forms and results for {mid}.")

# Save matches.json
with open(matches_path, "w", encoding="utf-8") as f:
    json.dump(matches_db, f, ensure_ascii=False, indent=2)

# 2. Update history.json (remove France vs England, and correct the rest)
filtered_records = []
for r in history_db["records"]:
    mid = r["match_id"]
    if mid == "match_260718_103":
        # Skip France vs England since it is now pending
        continue
    elif mid in results_info:
        # Correct the existing record
        info = results_info[mid]
        
        # Re-fetch matching match details for correct predictions list
        match_detail = [x for x in matches_db["matches"] if x["id"] == mid][0]
        
        pred_obj = {}
        for k, v_correct in info["predictions_correctness"].items():
            val = "--"
            if k == "recommendation":
                val = match_detail["ultimate_conclusion"].get("recommendation", "--")
            elif k == "primary_bet":
                val = match_detail["ultimate_conclusion"].get("primary_bet", "--")
            else:
                val = match_detail.get("conclusions", {}).get(k, "--")
            
            pred_obj[k] = {
                "val": val,
                "correct": v_correct
            }
            
        r["actual_result"] = info["actual_result"]
        r["is_correct"] = info["is_correct"]
        r["predictions"] = pred_obj
        filtered_records.append(r)
    else:
        filtered_records.append(r)

history_db["records"] = filtered_records
history_db["total_predictions"] = len(history_db["records"])
history_db["correct_predictions"] = sum(1 for x in history_db["records"] if x["is_correct"])
history_db["accuracy_rate"] = round(history_db["correct_predictions"] / history_db["total_predictions"], 4)

with open(history_path, "w", encoding="utf-8") as f:
    json.dump(history_db, f, ensure_ascii=False, indent=2)

print(f"Updated history.json. Total predictions: {history_db['total_predictions']}, Accuracy: {history_db['accuracy_rate']}")
