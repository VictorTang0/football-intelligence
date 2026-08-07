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

        # Always perform fresh dynamic evaluation to prevent stale cache bugs
        rec = uc.get("recommendation", "")
        rec_correct = False
        if is_home_win:
            if any(x in rec for x in ["主胜", "主队胜", "主不败", "主队不败", "双选胜平", "胜平", "双选胜负", "胜负", "分出胜负", "双选不败"]) or rec == "胜":
                rec_correct = True
        elif is_draw:
            if any(x in rec for x in ["平局", "主不败", "主队不败", "客不败", "客队不败", "双选胜平", "双选平负", "胜平", "平负", "不败", "双选不败"]) or rec == "平":
                rec_correct = True
        elif is_away_win:
            if any(x in rec for x in ["客胜", "客队胜", "客不败", "客队不败", "双选平负", "平负", "双选胜负", "胜负", "分出胜负", "双选不败"]) or rec == "负":
                rec_correct = True
            
        # Check primary_bet correctness
        pb = uc.get("primary_bet", "")
        pb_correct = False
        if is_home_win:
            if any(x in pb for x in ["主胜", "主队胜", "主不败", "主队不败", "双选胜平", "胜平", "双选胜负", "胜负", "分出胜负", "双选不败"]) or pb == "胜":
                pb_correct = True
        elif is_draw:
            if any(x in pb for x in ["平局", "主不败", "主队不败", "客不败", "客队不败", "双选胜平", "双选平负", "胜平", "平负", "不败", "双选不败"]) or pb == "平":
                pb_correct = True
        elif is_away_win:
            if any(x in pb for x in ["客胜", "客队胜", "客不败", "客队不败", "双选平负", "平负", "双选胜负", "胜负", "分出胜负", "双选不败"]) or pb == "负":
                pb_correct = True

        # Check mainstream correctness
        ms = conc.get("mainstream", "")
        ms_correct = False
        if is_home_win:
            if any(x in ms for x in ["全取三分", "主胜", "主队捷", "捍卫主场", "主不败"]):
                ms_correct = True
        elif is_draw:
            if any(x in ms for x in ["平局", "拉锯", "不败", "带走分数", "主不败", "客不败"]):
                ms_correct = True
        elif is_away_win:
            if any(x in ms for x in ["客胜", "客队捷", "反客为主", "带走分数", "客不败"]):
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
            if "主+1" in cons: cons_correct = (h_g + 1 > a_g)
            elif "主-1" in cons: cons_correct = (h_g - 1 > a_g)
            else: cons_correct = (h_g > a_g)
        elif "让负" in cons:
            if "主-1" in cons: cons_correct = (h_g - 1 < a_g)
            elif "主+1" in cons: cons_correct = (h_g + 1 < a_g)
            else: cons_correct = (h_g < a_g)
        elif "胜" == cons or "主胜" in cons: cons_correct = (h_g > a_g)
        elif "平" == cons or "平局" in cons: cons_correct = (h_g == a_g)
        elif "负" == cons or "客胜" in cons: cons_correct = (h_g < a_g)
        elif "主不败" in cons or "让主捷" in cons: cons_correct = (h_g >= a_g)
        elif "客不败" in cons: cons_correct = (h_g <= a_g)

        # Check over_under correctness
        ou = conc.get("over_under", "")
        ou_correct = False
        total_goals = h_g + a_g
        if "大 2.5" in ou: ou_correct = (total_goals > 2.5)
        elif "小 2.5" in ou: ou_correct = (total_goals < 2.5)

        # Check most_likely_score correctness
        mls = conc.get("most_likely_score", "")
        mls_parts = mls.replace("或", " ").split()
        mls_correct = False
        for part in mls_parts:
            clean_part = part.split('(')[0].strip()
            if clean_part == f"{h_g}-{a_g}":
                mls_correct = True

        # Check half_full correctness automatically from actual_result if needed
        hf_correct = False
        half_m = re.search(r'\(\s*(\d+)\s*[-–:]\s*(\d+)\s*\)', actual_result)
        actual_hf = uc.get("half_full_actual")
        if not actual_hf and half_m:
            h1, h2 = int(half_m.group(1)), int(half_m.group(2))
            hh_g, ha_g = (h1, h2) if pos_home < pos_away else (h2, h1)
            h_res = "胜" if hh_g > ha_g else ("平" if hh_g == ha_g else "负")
            f_res = "胜" if h_g > a_g else ("平" if h_g == a_g else "负")
            actual_hf = h_res + f_res

        if actual_hf:
            hf = conc.get("half_full", "")
            if actual_hf in hf or actual_hf in hf.replace("/", ""):
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
        odds = m.get("odds_analysis", {})
        m10_h = m.get("m10_hub_analysis", {})
        upset_idx = m.get("upset_risk_index") or conc.get("upset_risk_index", 0)
        divergence = conc.get("had_hhad_divergence", False)
        radar_trig = m.get("radar_triggered", False) or m.get("is_radar_alert", False)

        if not alert:
            # 仅当真正触发欧亚背离、高冷门指数 (>=65%) 或风控雷达干预时，才纳入风控雷达历史记录
            if divergence or upset_idx >= 65 or radar_trig:
                rec_desc = m10_h.get("had_recommendation") or uc.get("recommendation", "主不败")
                if rec_desc == "无推荐": rec_desc = "主不败"
                
                alert_is_correct = False
                if "主胜" in rec_desc and is_home_win: alert_is_correct = True
                elif "客胜" in rec_desc and is_away_win: alert_is_correct = True
                elif "平" in rec_desc and is_draw: alert_is_correct = True
                elif "主不败" in rec_desc and (is_home_win or is_draw): alert_is_correct = True
                elif "客不败" in rec_desc and (is_away_win or is_draw): alert_is_correct = True

                alert_type = "欧亚指数严重背离" if divergence else ("冷门爆冷高度预警" if upset_idx >= 65 else "induce")
                alert = {
                    "type": alert_type,
                    "target": rec_desc.split("(")[0].strip(),
                    "diff": -0.05 if upset_idx >= 65 else -0.03,
                    "recommendation": rec_desc.split("(")[0].strip(),
                    "actual_result": actual_result,
                    "is_correct": alert_is_correct
                }
            else:
                alert = None
        else:
            # 存在原始 radar_alert 时同步准确率
            rec_desc = alert.get("recommendation") or uc.get("recommendation", "")
            alert_is_correct = False
            if "主胜" in rec_desc and is_home_win: alert_is_correct = True
            elif "客胜" in rec_desc and is_away_win: alert_is_correct = True
            elif "平" in rec_desc and is_draw: alert_is_correct = True
            elif "主不败" in rec_desc and (is_home_win or is_draw): alert_is_correct = True
            elif "客不败" in rec_desc and (is_away_win or is_draw): alert_is_correct = True
            alert["is_correct"] = alert_is_correct
            alert["actual_result"] = actual_result

        raw_ko = m.get("kickoff") or m.get("date") or ""
        time_part = ""
        if " " in raw_ko:
            time_part = raw_ko.split(" ")[1]
        elif "T" in raw_ko:
            time_part = raw_ko.split("T")[1]
            
        if time_part and ":" in time_part:
            time_part = time_part[:5]

        conclusions_map = {
            "sporttery_hot_scores": conc.get("sporttery_hot_scores", []),
            "m10_snapshot_count": conc.get("m10_snapshot_count", 1),
            "had_hhad_divergence": conc.get("had_hhad_divergence", False)
        }

        # ─── AUTOMATIC SPORTTERY TAGS & PURE M10 DEDUCTION INTEGRATION ───
        code_num = None
        m_code = re.search(r"match_\d{6}_(\d+)", mid)
        if m_code:
            code_num = int(m_code.group(1))
        elif m.get("code"):
            try:
                code_num = int(m.get("code"))
            except:
                pass

        match_no = f"周日 {code_num:03d}" if (code_num is not None and code_num < 500) else m.get("match_no", "周日 201")
        m_issue = re.search(r"match_(\d{6})_", mid)
        issue_date = m_issue.group(1) if m_issue else "260726"

        m10_hub = m.get("m10_hub_analysis", {})
        if not m10_hub or not m10_hub.get("had_recommendation") or m10_hub.get("had_recommendation") == "无推荐":
            try:
                from scripts.generate_pure_m10_conclusions import deduce_pure_m10
                m10_res = deduce_pure_m10(m)
                m10_hub = {
                    "had_recommendation": m10_res["m10_had"],
                    "hhad_recommendation": m10_res["m10_hhad"],
                    "predicted_score": m10_res["m10_score"],
                    "over_under": m10_res["m10_goals"],
                    "half_full": m10_res["m10_hf"],
                    "confidence": m10_res["confidence"]
                }
            except Exception as e:
                pass

        record = {
            "match_id": mid,
            "id": mid,
            "code": str(code_num) if code_num else "201",
            "match_no": match_no,
            "issue_date": issue_date,
            "league": m["league"],
            "home": home,
            "away": away,
            "date": m.get("kickoff", "").split("T")[0].split(" ")[0] if m.get("kickoff") else m.get("date", "").split(" ")[0],
            "time": time_part,
            "actual_result": actual_result,
            "is_correct": is_correct,
            "confidence": uc.get("confidence", 0),
            "predictions": predictions_map,
            "conclusions": conclusions_map,
            "m10_hub_analysis": m10_hub,
            "injury_analysis": m.get("injury_analysis", {})
        }
        if alert:
            record["radar_alert"] = alert
        new_records.append(record)
        
    new_records.sort(key=lambda x: (x["date"], x.get("time", "00:00"), x["match_id"]), reverse=True)
    
    history_db["records"] = new_records
    history_db["total_predictions"] = len(new_records)
    history_db["correct_predictions"] = sum(1 for r in new_records if r["is_correct"])
    history_db["accuracy_rate"] = round(history_db["correct_predictions"] / history_db["total_predictions"], 4) if history_db["total_predictions"] > 0 else 0.0

    try:
        with open(os.path.join(base_dir, "data", "m10_weights.json"), "r", encoding="utf-8") as mf:
            m10_w = json.load(mf)
            history_db["m10_stats"] = m10_w.get("accuracy_stats", {})
    except Exception: pass
    
    # 计算比分与半全场预测准确率
    score_correct = sum(1 for r in new_records if r.get("predictions", {}).get("most_likely_score", {}).get("correct"))
    hf_correct = sum(1 for r in new_records if r.get("predictions", {}).get("half_full", {}).get("correct"))
    history_db["score_accuracy_rate"] = round(score_correct / history_db["total_predictions"], 4) if history_db["total_predictions"] > 0 else 0.0
    history_db["half_full_accuracy_rate"] = round(hf_correct / history_db["total_predictions"], 4) if history_db["total_predictions"] > 0 else 0.0
    
    # 专属计算：M10 竞彩大师在【胜平负/方向】、【进球数】、【比分】、【半全场】四大维度的 (竞彩) 独立命中率
    sp_dir_hits, sp_dir_total = 0, 0
    sp_goals_hits, sp_goals_total = 0, 0
    sp_score_hits, sp_score_total = 0, 0
    sp_hafu_hits, sp_hafu_total = 0, 0

    for m in matches_db.get("matches", []):
        if m.get("status") != "finished":
            continue
        actual = m.get("ultimate_conclusion", {}).get("actual_result", "")
        if not actual or "-" not in actual:
            continue

        m_score = re.search(r'(\d+)\s*[-–:]\s*(\d+)\s*\((.*?)\)', actual)
        if not m_score:
            m_score_simple = re.search(r'(\d+)\s*[-–:]\s*(\d+)', actual)
            if not m_score_simple: continue
            hg, ag = int(m_score_simple.group(1)), int(m_score_simple.group(2))
            ht_str = ""
        else:
            hg, ag = int(m_score.group(1)), int(m_score.group(2))
            ht_str = m_score.group(3)

        ft_score_clean = f"{hg}-{ag}"
        is_home_win = (hg > ag)
        is_draw = (hg == ag)
        is_away_win = (hg < ag)
        total_goals = hg + ag

        actual_hafu = ""
        if ht_str and "-" in ht_str:
            try:
                ht1, ht2 = map(int, ht_str.split("-"))
                ht_res = "胜" if ht1 > ht2 else "负" if ht2 > ht1 else "平"
                ft_res = "胜" if hg > ag else "负" if ag > hg else "平"
                actual_hafu = f"{ht_res}{ft_res}"
            except Exception: pass

        uc = m.get("ultimate_conclusion", {})
        conc = m.get("conclusions", {})
        rec = uc.get("recommendation", "")
        mls = conc.get("most_likely_score", "")
        ou = conc.get("over_under", "")
        hf = conc.get("half_full", "")

        # 1. 竞彩方向/胜平负
        if "(竞彩)" in rec:
            sp_dir_total += 1
            dir_correct = False
            if is_home_win and any(x in rec for x in ["主胜", "主队胜", "主不败", "胜"]): dir_correct = True
            elif is_draw and any(x in rec for x in ["平局", "主不败", "客不败", "平"]): dir_correct = True
            elif is_away_win and any(x in rec for x in ["客胜", "客队胜", "客不败", "负"]): dir_correct = True
            if dir_correct: sp_dir_hits += 1

        # 2. 竞彩总进球数：改成 M10 系统具体推荐的进球数命中率评估
        m10_goals = []
        m10_scores = conc.get("sporttery_hot_scores", [])
        snapshot_count = conc.get("m10_snapshot_count", 1)
        if snapshot_count >= 2 and m10_scores:
            limit = 1 if conc.get("had_hhad_divergence") else 2
            target_scores = m10_scores[:limit]
            
            matches_m = re.findall(r'\d+[:\-]\d+', " ".join(target_scores))
            if matches_m:
                for s in matches_m:
                    parts = re.split(r'[:\-]', s)
                    m10_goals.append(int(parts[0]) + int(parts[1]))
                m10_goals = sorted(list(set(m10_goals)))[:2]
        
        if m10_goals:
            sp_goals_total += 1
            if int(total_goals) in m10_goals:
                sp_goals_hits += 1

        # 3. 竞彩比分
        if "(竞彩)" in mls:
            parts = mls.split("或")
            primary_score = None
            for p in parts:
                if "竞彩" in p:
                    primary_score = p.split("(")[0].strip().replace(":", "-")
                    break
            if primary_score:
                sp_score_total += 1
                if primary_score == ft_score_clean:
                    sp_score_hits += 1

        # 4. 竞彩半全场
        if "(竞彩)" in hf:
            parts = hf.split("或")
            primary_hafu = None
            for p in parts:
                if "竞彩" in p:
                    primary_hafu = p.split("(")[0].strip().replace("/", "").replace(" ", "")
                    break
            if primary_hafu and actual_hafu:
                sp_hafu_total += 1
                if primary_hafu == actual_hafu:
                    sp_hafu_hits += 1

    sp_dir_acc = round(sp_dir_hits / sp_dir_total, 4) if sp_dir_total > 0 else 0.0
    sp_goals_acc = round(sp_goals_hits / sp_goals_total, 4) if sp_goals_total > 0 else 0.0
    sp_score_acc = round(sp_score_hits / sp_score_total, 4) if sp_score_total > 0 else 0.0
    sp_hafu_acc = round(sp_hafu_hits / sp_hafu_total, 4) if sp_hafu_total > 0 else 0.0

    history_db["sporttery_primary_stats"] = {
        "direction": {
            "hits": sp_dir_hits,
            "total": sp_dir_total,
            "accuracy_rate": sp_dir_acc
        },
        "goals": {
            "hits": sp_goals_hits,
            "total": sp_goals_total,
            "accuracy_rate": sp_goals_acc
        },
        "score": {
            "hits": sp_score_hits,
            "total": sp_score_total,
            "accuracy_rate": sp_score_acc
        },
        "half_full": {
            "hits": sp_hafu_hits,
            "total": sp_hafu_total,
            "accuracy_rate": sp_hafu_acc
        }
    }

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
    print(f"🎯 Sporttery Primary Score Accuracy: {sp_score_acc} ({sp_score_hits}/{sp_score_total}), Primary Hafu Accuracy: {sp_hafu_acc} ({sp_hafu_hits}/{sp_hafu_total})")
    print(f"📊 Radar Stats: Total {radar_count}, Correct {radar_correct}, Accuracy {history_db['radar_stats']['accuracy_rate']}")
    return True

if __name__ == "__main__":
    sync()
