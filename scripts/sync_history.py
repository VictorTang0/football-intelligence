import json
import os
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
history_path = os.path.join(base_dir, "data", "history.json")

def clean_team(name):
    name = re.sub(r'（[^）]*）', '', name)
    name = re.sub(r'\([^)]*\)', '', name)
    return name.strip()

def sync():
    print("🔄 Synchronizing history.json from matches.json...")
    
    if not os.path.exists(matches_path):
        print(f"❌ Error: {matches_path} does not exist!")
        return False
        
    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)
        
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            history_db = json.load(f)
    else:
        history_db = {"total_predictions": 0, "correct_predictions": 0, "accuracy_rate": 0.0, "records": []}

    # Map existing history records by match_id to preserve correctness for manually verified records
    existing_records = {r["match_id"]: r for r in history_db.get("records", [])}
    
    new_records = []
    
    for m in matches_db["matches"]:
        if m["status"] != "finished":
            continue
            
        mid = m["id"]
        home = m["home"]
        away = m["away"]
        uc = m.get("ultimate_conclusion", {})
        conc = m.get("conclusions", {})
        
        actual_result = uc.get("actual_result", "")
        if not actual_result:
            print(f"⚠️ Warning: Finished match {mid} has no actual_result. Skipping.")
            continue
            
        # Parse scores
        match = re.search(r'(\d+)\s*[-–:]\s*(\d+)', actual_result)
        if not match:
            print(f"⚠️ Warning: Could not parse goals from actual_result '{actual_result}' for {mid}. Skipping.")
            continue
            
        g1, g2 = int(match.group(1)), int(match.group(2))
        pos_home = actual_result.find(clean_team(home))
        pos_away = actual_result.find(clean_team(away))
        
        if pos_home < pos_away:
            h_g, a_g = g1, g2
        else:
            h_g, a_g = g2, g1
            
        # Determine actual standard outcome flags
        is_home_win = (h_g > a_g)
        is_draw = (h_g == a_g)
        is_away_win = (h_g < a_g)

        # Check if we can preserve correctness from existing record
        preserve_existing = False
        if mid in existing_records:
            existing_rec = existing_records[mid]
            if existing_rec.get("actual_result") == actual_result:
                preserve_existing = True

        if preserve_existing:
            existing_rec = existing_records[mid]
            preds = existing_rec.get("predictions", {})
            rec_correct = preds.get("recommendation", {}).get("correct", False)
            pb_correct = preds.get("primary_bet", {}).get("correct", False)
            ms_correct = preds.get("mainstream", {}).get("correct", False)
            up_correct = preds.get("upset", {}).get("correct", False)
            agg_correct = preds.get("aggressive", {}).get("correct", False)
            cons_correct = preds.get("conservative", {}).get("correct", False)
            hf_correct = preds.get("half_full", {}).get("correct", False)
            ou_correct = preds.get("over_under", {}).get("correct", False)
            mls_correct = preds.get("most_likely_score", {}).get("correct", False)
            is_correct = existing_rec.get("is_correct", rec_correct)
        else:
            # Calculate correctness of recommendation
            rec = uc.get("recommendation", "")
            rec_correct = False
            if is_home_win:
                if any(x in rec for x in ["主胜", "主队胜", "主不败", "主队不败", "双选胜平", "胜平", "双选胜负", "胜负", "分出胜负"]) or rec == "胜":
                    rec_correct = True
            elif is_draw:
                if any(x in rec for x in ["平局", "主不败", "主队不败", "客不败", "客队不败", "双选胜平", "双选平负", "胜平", "平负", "不败"]) or rec == "平":
                    rec_correct = True
            elif is_away_win:
                if any(x in rec for x in ["客胜", "客队胜", "客不败", "客队不败", "双选平负", "平负", "双选胜负", "胜负", "分出胜负"]) or rec == "负":
                    rec_correct = True
                
            # Check primary_bet correctness
            pb = uc.get("primary_bet", "")
            pb_correct = False
            if is_home_win:
                if any(x in pb for x in ["主胜", "主队胜", "主不败", "主队不败", "双选胜平", "胜平", "双选胜负", "胜负", "分出胜负"]) or pb == "胜":
                    pb_correct = True
            elif is_draw:
                if any(x in pb for x in ["平局", "主不败", "主队不败", "客不败", "客队不败", "双选胜平", "双选平负", "胜平", "平负", "不败"]) or pb == "平":
                    pb_correct = True
            elif is_away_win:
                if any(x in pb for x in ["客胜", "客队胜", "客不败", "客队不败", "双选平负", "平负", "双选胜负", "胜负", "分出胜负"]) or pb == "负":
                    pb_correct = True

            # Check mainstream correctness
            ms = conc.get("mainstream", "")
            ms_correct = False
            if is_home_win:
                if any(x in ms for x in ["全取三分", "主胜", "主队捷", "捍卫主场"]):
                    ms_correct = True
            elif is_draw:
                if any(x in ms for x in ["平局", "拉锯", "不败", "带走分数"]):
                    ms_correct = True
            elif is_away_win:
                if any(x in ms for x in ["客胜", "客队捷", "反客为主", "带走分数"]):
                    ms_correct = True

            # Check upset correctness
            up = conc.get("upset", "")
            up_correct = False
            if is_home_win:
                if any(x in up for x in ["主胜", "主队", "爆冷"]):
                    up_correct = True
            elif is_draw:
                if any(x in up for x in ["平局", "握手言和"]):
                    up_correct = True
            elif is_away_win:
                if any(x in up for x in ["客胜", "客队", "爆冷", "分出胜负"]):
                    up_correct = True

            # Check aggressive correctness
            agg = conc.get("aggressive", "")
            agg_score = agg.replace("比分", "").strip()
            agg_correct = (agg_score == f"{h_g}-{a_g}")

            # Check conservative correctness
            cons = conc.get("conservative", "")
            cons_correct = False
            if "让胜" in cons:
                if "主+1" in cons:
                    cons_correct = (h_g + 1 > a_g)
                elif "主-1" in cons:
                    cons_correct = (h_g - 1 > a_g)
                else:
                    cons_correct = (h_g > a_g)
            elif "让负" in cons:
                if "主-1" in cons:
                    cons_correct = (h_g - 1 < a_g)
                elif "主+1" in cons:
                    cons_correct = (h_g + 1 < a_g)
                else:
                    cons_correct = (h_g < a_g)
            elif "胜" == cons:
                cons_correct = (h_g > a_g)
            elif "平" == cons:
                cons_correct = (h_g == a_g)
            elif "负" == cons:
                cons_correct = (h_g < a_g)
            elif "主不败" in cons or "让主捷" in cons:
                cons_correct = (h_g >= a_g)
            elif "客不败" in cons:
                cons_correct = (h_g <= a_g)

            # Check over_under correctness
            ou = conc.get("over_under", "")
            ou_correct = False
            total_goals = h_g + a_g
            if "大 2.5" in ou:
                ou_correct = (total_goals > 2.5)
            elif "小 2.5" in ou:
                ou_correct = (total_goals < 2.5)

            # Check most_likely_score correctness
            mls = conc.get("most_likely_score", "")
            mls_parts = mls.replace("或", " ").split()
            mls_correct = False
            for part in mls_parts:
                clean = part.split('(')[0].strip()
                if clean == f"{h_g}-{a_g}":
                    mls_correct = True

            # Check half_full correctness
            hf_correct = False
            half_full_actual = uc.get("half_full_actual")
            if half_full_actual:
                hf = conc.get("half_full", "")
                hf_parts = hf.replace("或", " ").replace("/", "").replace(" ", "").split()
                actual_hf_clean = half_full_actual.replace("/", "")
                for part in hf_parts:
                    if part == actual_hf_clean:
                        hf_correct = True
            
            is_correct = rec_correct

        # Build predictions dict
        predictions_map = {
            "recommendation": {"val": uc.get("recommendation", "--"), "correct": rec_correct},
            "primary_bet": {"val": uc.get("primary_bet", "--"), "correct": pb_correct},
            "mainstream": {"val": conc.get("mainstream", "--"), "correct": ms_correct},
            "upset": {"val": conc.get("upset", "--"), "correct": up_correct},
            "aggressive": {"val": conc.get("aggressive", "--"), "correct": agg_correct},
            "conservative": {"val": conc.get("conservative", "--"), "correct": cons_correct},
            "half_full": {"val": conc.get("half_full", "--"), "correct": hf_correct},
            "over_under": {"val": conc.get("over_under", "--"), "correct": ou_correct},
            "most_likely_score": {"val": conc.get("most_likely_score", "--"), "correct": mls_correct}
        }
        
        # Calculate or sync radar alert correctness
        alert = m.get("radar_alert")
        if not alert:
            odds = m.get("odds_analysis", {})
            pinnacle = odds.get("pinnacle", {})
            current = pinnacle.get("current")
            initial = pinnacle.get("initial")
            if current and initial:
                oh, od, oa = current.get("home"), current.get("draw"), current.get("away")
                ih, id_, ia = initial.get("home"), initial.get("draw"), initial.get("away")
                if oh and od and oa and ih and id_ and ia:
                    sentiment = odds.get("retail_sentiment", {})
                    sh = sentiment.get("home_pct", 33.3) / 100
                    sd = sentiment.get("draw_pct", 33.3) / 100
                    sa = sentiment.get("away_pct", 33.3) / 100
                    
                    kh = oh * sh
                    kd = od * sd
                    ka = oa * sa
                    
                    diff_h = oh - ih
                    diff_d = od - id_
                    diff_a = oa - ia
                    
                    kellys = [
                        {"label": "主胜", "val": kh, "diff": diff_h, "outcome": "H"},
                        {"label": "平局", "val": kd, "diff": diff_d, "outcome": "D"},
                        {"label": "客胜", "val": ka, "diff": diff_a, "outcome": "A"}
                    ]
                    kellys.sort(key=lambda x: x["val"], reverse=True)
                    worst = kellys[0]
                    
                    if worst["diff"] <= -0.01:
                        rec_outcome = worst["outcome"]
                        rec_desc = f"{worst['label']}（庄家降水防范）"
                        actual_outcome = "H" if is_home_win else "A" if is_away_win else "D"
                        alert_is_correct = (actual_outcome == rec_outcome)
                        alert = {
                            "type": "protect",
                            "target": worst["label"],
                            "diff": worst["diff"],
                            "recommendation": rec_desc,
                            "is_correct": alert_is_correct
                        }
                    elif worst["diff"] >= 0.01:
                        rec_desc = "客不败" if worst["outcome"] == "H" else "主不败" if worst["outcome"] == "A" else "分出胜负"
                        actual_outcome = "H" if is_home_win else "A" if is_away_win else "D"
                        alert_is_correct = False
                        if worst["outcome"] == "H" and actual_outcome in ["D", "A"]:
                            alert_is_correct = True
                        elif worst["outcome"] == "A" and actual_outcome in ["H", "D"]:
                            alert_is_correct = True
                        elif worst["outcome"] == "D" and actual_outcome in ["H", "A"]:
                            alert_is_correct = True
                        alert = {
                            "type": "trap",
                            "target": worst["label"],
                            "diff": worst["diff"],
                            "recommendation": rec_desc,
                            "is_correct": alert_is_correct
                        }

        raw_ko = m.get("kickoff") or m.get("date") or ""
        time_part = ""
        if " " in raw_ko:
            time_part = raw_ko.split(" ")[1]
        elif "T" in raw_ko:
            time_part = raw_ko.split("T")[1]
            
        if time_part and ":" in time_part:
            time_part = time_part[:5]

        record = {
            "match_id": mid,
            "league": m["league"],
            "home": home,
            "away": away,
            "date": m.get("kickoff", "").split("T")[0].split(" ")[0] if m.get("kickoff") else m.get("date", "").split(" ")[0],
            "time": time_part,
            "actual_result": actual_result,
            "is_correct": is_correct,
            "confidence": uc.get("confidence", 0),
            "predictions": predictions_map
        }
        if alert:
            record["radar_alert"] = alert
        new_records.append(record)
        
    new_records.sort(key=lambda x: (x["date"], x["match_id"]))
    
    history_db["records"] = new_records
    history_db["total_predictions"] = len(new_records)
    history_db["correct_predictions"] = sum(1 for r in new_records if r["is_correct"])
    history_db["accuracy_rate"] = round(history_db["correct_predictions"] / history_db["total_predictions"], 4) if history_db["total_predictions"] > 0 else 0.0
    
    # 计算比分与半全场预测准确率
    score_correct = sum(1 for r in new_records if r.get("predictions", {}).get("most_likely_score", {}).get("correct"))
    hf_correct = sum(1 for r in new_records if r.get("predictions", {}).get("half_full", {}).get("correct"))
    history_db["score_accuracy_rate"] = round(score_correct / history_db["total_predictions"], 4) if history_db["total_predictions"] > 0 else 0.0
    history_db["half_full_accuracy_rate"] = round(hf_correct / history_db["total_predictions"], 4) if history_db["total_predictions"] > 0 else 0.0
    
    # Calculate cumulative radar accuracy stats
    radar_alerts = [r["radar_alert"] for r in new_records if r.get("radar_alert")]
    radar_count = len(radar_alerts)
    radar_correct = sum(1 for a in radar_alerts if a["is_correct"])
    history_db["radar_stats"] = {
        "total_alerts": radar_count,
        "correct_alerts": radar_correct,
        "accuracy_rate": round(radar_correct / radar_count, 4) if radar_count > 0 else 0.0
    }
    
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_db, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Successfully synchronized history.json! Total predictions: {history_db['total_predictions']}, Correct: {history_db['correct_predictions']}, Accuracy: {history_db['accuracy_rate']}")
    print(f"📊 Score Accuracy: {history_db['score_accuracy_rate']}, Half/Full Accuracy: {history_db['half_full_accuracy_rate']}")
    print(f"📊 Radar Stats: Total {radar_count}, Correct {radar_correct}, Accuracy {history_db['radar_stats']['accuracy_rate']}")
    return True

if __name__ == "__main__":
    sync()
