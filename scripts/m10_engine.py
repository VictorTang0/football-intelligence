import json
import os
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m10_weights_path = os.path.join(base_dir, "data", "m10_weights.json")

def load_m10_weights():
    if os.path.exists(m10_weights_path):
        try:
            with open(m10_weights_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception: pass
    return {
        "thresholds": {
            "had_min_diff": 0.05,
            "hhad_min_scissors": 0.04,
            "crs_min_drop": 0.50,
            "goals_min_cluster": 1.25,
            "hafu_min_drop": 0.40
        }
    }

def get_bonus_data_smart(match_obj, bonus_db):
    mid = match_obj.get("id")
    sp_id = str(match_obj.get("sportteryMatchId") or "")
    home = match_obj.get("home", "")
    away = match_obj.get("away", "")

    direct = bonus_db.get(mid) or bonus_db.get(sp_id) or bonus_db.get(f"match_sp_{sp_id}")
    direct_snaps = len(direct.get("oddsHistory", {}).get("hadList", [])) if direct else 0

    if direct_snaps >= 3:
        return direct

    best_entry = direct or {}
    best_count = direct_snaps

    for k, v in bonus_db.items():
        v_home = v.get("home", "")
        v_away = v.get("away", "")
        if home and away and (home in v_home or v_home in home) and (away in v_away or v_away in away):
            oh = v.get("oddsHistory", {})
            snaps = max(len(oh.get("hadList", [])), len(oh.get("hhadList", [])), len(oh.get("crsList", [])))
            if snaps > best_count:
                best_count = snaps
                best_entry = v

    return best_entry

def deduce_m10_hub_conclusions(match_obj, bonus_db):
    """
    Deduces M10 6-dimensional conclusions for card UI display based on trained weights
    """
    weights_db = load_m10_weights()
    thresholds = weights_db.get("thresholds", {})
    
    b_data = get_bonus_data_smart(match_obj, bonus_db)
    oh = b_data.get("oddsHistory", {})

    had_list = oh.get("hadList", [])
    hhad_list = oh.get("hhadList", [])
    crs_list = oh.get("crsList", [])
    ttg_list = oh.get("ttgList", [])
    hafu_list = oh.get("hafuList", [])

    m10_hub = {}

    snapshot_count = max(len(had_list), len(hhad_list), len(crs_list), len(ttg_list), len(hafu_list), 1)
    m10_hub["snapshot_count"] = snapshot_count

    # 1. 亚欧盘资金流状态
    hhad_line = match_obj.get("handicap_line") or "-1"
    divergence = False
    status_desc = "水温拉锯平稳 (资金分布均衡)"

    if len(had_list) >= 2 and len(hhad_list) >= 2:
        init_h, curr_h = float(had_list[0].get("h", 0)), float(had_list[-1].get("h", 0))
        init_hhad, curr_hhad = float(hhad_list[0].get("h", 0)), float(hhad_list[-1].get("h", 0))
        scissors = (init_hhad - curr_hhad) - (init_h - curr_h)
        if abs(scissors) >= thresholds.get("hhad_min_scissors", 0.04):
            divergence = True
            if scissors > 0:
                status_desc = f"🚨 欧让剪刀差背离 (主胜降水/让胜升水，庄家强防客不败)"
            else:
                status_desc = f"🚨 欧让剪刀差背离 (主胜升水/让负降水，庄家强防主不败)"

    m10_hub["asian_eu_status"] = {
        "has_divergence": divergence,
        "description": status_desc
    }

    # 2. 胜平负水位变动与最/次可能结论
    if len(had_list) >= 2:
        init_h, curr_h = float(had_list[0].get("h", 0)), float(had_list[-1].get("h", 0))
        init_d, curr_d = float(had_list[0].get("d", 0)), float(had_list[-1].get("d", 0))
        init_a, curr_a = float(had_list[0].get("a", 0)), float(had_list[-1].get("a", 0))
        
        diff_h = init_h - curr_h
        diff_d = init_d - curr_d
        diff_a = init_a - curr_a
        max_diff = max(abs(diff_h), abs(diff_d), abs(diff_a))

        arrow_h = "↓" if diff_h > 0 else "↑" if diff_h < 0 else "-"
        arrow_d = "↓" if diff_d > 0 else "↑" if diff_d < 0 else "-"
        arrow_a = "↓" if diff_a > 0 else "↑" if diff_a < 0 else "-"

        water_text = f"主胜 {init_h:.2f}➔{curr_h:.2f}({arrow_h}) | 平 {init_d:.2f}➔{curr_d:.2f}({arrow_d}) | 客胜 {init_a:.2f}➔{curr_a:.2f}({arrow_a})"

        if max_diff < thresholds.get("had_min_diff", 0.05):
            m10_hub["had_analysis"] = {
                "trajectory": water_text,
                "has_recommendation": False,
                "text": "当前无竞彩推荐 (资金变幅未达门槛)"
            }
        else:
            options = [("主胜", diff_h), ("平局", diff_d), ("客胜", diff_a)]
            options.sort(key=lambda x: x[1], reverse=True)
            primary = options[0][0]
            secondary = options[1][0] if options[1][1] > -0.2 else None
            
            rec_text = f"最可能：{primary}" + (f" | 次可能：{secondary}" if secondary else "")
            m10_hub["had_analysis"] = {
                "trajectory": water_text,
                "has_recommendation": True,
                "primary": primary,
                "secondary": secondary,
                "text": rec_text
            }
    else:
        m10_hub["had_analysis"] = {
            "trajectory": "暂无变盘快照",
            "has_recommendation": False,
            "text": "当前无竞彩推荐"
        }

    # 3. 让球胜平负水位变动与最/次可能结论
    if len(hhad_list) >= 2:
        init_hh, curr_hh = float(hhad_list[0].get("h", 0)), float(hhad_list[-1].get("h", 0))
        init_hd, curr_hd = float(hhad_list[0].get("d", 0)), float(hhad_list[-1].get("d", 0))
        init_ha, curr_ha = float(hhad_list[0].get("a", 0)), float(hhad_list[-1].get("a", 0))
        
        diff_hh = init_hh - curr_hh
        diff_hd = init_hd - curr_hd
        diff_ha = init_ha - curr_ha
        max_hdiff = max(abs(diff_hh), abs(diff_hd), abs(diff_ha))

        arrow_hh = "↓" if diff_hh > 0 else "↑" if diff_hh < 0 else "-"
        arrow_hd = "↓" if diff_hd > 0 else "↑" if diff_hd < 0 else "-"
        arrow_ha = "↓" if diff_ha > 0 else "↑" if diff_ha < 0 else "-"

        water_text = f"让胜({hhad_line}) {init_hh:.2f}➔{curr_hh:.2f}({arrow_hh}) | 让平 {init_hd:.2f}➔{curr_hd:.2f}({arrow_hd}) | 让负 {init_ha:.2f}➔{curr_ha:.2f}({arrow_ha})"

        if max_hdiff < 0.03:
            m10_hub["hhad_analysis"] = {
                "trajectory": water_text,
                "has_recommendation": False,
                "text": "当前无竞彩推荐 (盘口让水变幅不足)"
            }
        else:
            h_options = [("让胜", diff_hh), ("让平", diff_hd), ("让负", diff_ha)]
            h_options.sort(key=lambda x: x[1], reverse=True)
            primary_h = h_options[0][0]
            secondary_h = h_options[1][0] if h_options[1][1] > -0.2 else None

            rec_h_text = f"最可能：{primary_h}" + (f" | 次可能：{secondary_h}" if secondary_h else "")
            m10_hub["hhad_analysis"] = {
                "trajectory": water_text,
                "has_recommendation": True,
                "primary": primary_h,
                "secondary": secondary_h,
                "text": rec_h_text
            }
    else:
        m10_hub["hhad_analysis"] = {
            "trajectory": "暂无让球变盘快照",
            "has_recommendation": False,
            "text": "当前无竞彩推荐"
        }

    # 4. 动态比分动向 (Top 3 信心 + 箭头 + 划线删除)
    crs_items = []
    if len(crs_list) >= 2:
        init_crs, curr_crs = crs_list[0], crs_list[-1]
        raw_candidates = []
        for skey in init_crs:
            if skey.startswith("s") and not skey.endswith("f") and skey not in ["s-1sh", "s-1sd", "s-1sa"]:
                try:
                    v_init = float(init_crs.get(skey, 0))
                    v_curr = float(curr_crs.get(skey, 0))
                    if v_init > 0 and v_curr > 0:
                        drop = v_init - v_curr
                        formatted = skey.replace("s", "").split("s")
                        if len(formatted) == 2:
                            score_label = f"{int(formatted[0])}-{int(formatted[1])}"
                            raw_candidates.append({
                                "score": score_label,
                                "drop": drop,
                                "curr": v_curr,
                                "arrow": "↓" if drop > 0 else "↑" if drop < 0 else "-",
                                "is_invalid": (drop <= -1.0) # 降水为负且大涨升水 -> 划线作废
                            })
                except Exception: pass
        
        # Sort candidates by drop descending
        raw_candidates.sort(key=lambda x: x["drop"], reverse=True)
        
        # Filter valid vs invalid
        valid_items = [c for c in raw_candidates if not c["is_invalid"] and c["drop"] >= 0.20][:3]
        invalid_items = [c for c in raw_candidates if c["is_invalid"]][:2]

        crs_items = valid_items + invalid_items

    m10_hub["crs_analysis"] = {
        "items": crs_items,
        "has_recommendation": len([c for c in crs_items if not c["is_invalid"]]) > 0
    }

    # 5. 动态具体总进球数动向 (Top 3 信心 + 箭头 + 划线删除)
    goals_items = []
    if len(ttg_list) >= 2:
        init_ttg, curr_ttg = ttg_list[0], ttg_list[-1]
        raw_goals = []
        for gkey in ["s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7"]:
            try:
                v_init = float(init_ttg.get(gkey, 0))
                v_curr = float(curr_ttg.get(gkey, 0))
                if v_init > 0 and v_curr > 0:
                    drop = v_init - v_curr
                    g_label = f"{gkey.replace('s', '')}球" if gkey != "s7" else "7+球"
                    raw_goals.append({
                        "goal": g_label,
                        "drop": drop,
                        "arrow": "↓" if drop > 0 else "↑" if drop < 0 else "-",
                        "is_invalid": (drop <= -0.50)
                    })
            except Exception: pass
            
        raw_goals.sort(key=lambda x: x["drop"], reverse=True)
        valid_goals = [g for g in raw_goals if not g["is_invalid"] and g["drop"] >= 0.10][:3]
        invalid_goals = [g for g in raw_goals if g["is_invalid"]][:2]
        goals_items = valid_goals + invalid_goals

    m10_hub["goals_analysis"] = {
        "items": goals_items,
        "has_recommendation": len([g for g in goals_items if not g["is_invalid"]]) > 0
    }

    # 6. 动态半全场胜平负动向 (最多 Top 2 有效 + 箭头 + 划线删除)
    hafu_items = []
    if len(hafu_list) >= 2:
        init_hafu, curr_hafu = hafu_list[0], hafu_list[-1]
        raw_hafu = []
        hf_map = {"hh":"胜胜", "hd":"胜平", "ha":"胜负", "dh":"平胜", "dd":"平平", "da":"平负", "ah":"负胜", "ad":"负平", "aa":"负负"}
        for hfkey, label_text in hf_map.items():
            try:
                v_init = float(init_hafu.get(hfkey, 0))
                v_curr = float(curr_hafu.get(hfkey, 0))
                if v_init > 0 and v_curr > 0:
                    drop = v_init - v_curr
                    raw_hafu.append({
                        "hafu": label_text,
                        "drop": drop,
                        "arrow": "↓" if drop > 0 else "↑" if drop < 0 else "-",
                        "is_invalid": (drop <= -0.80)
                    })
            except Exception: pass

        raw_hafu.sort(key=lambda x: x["drop"], reverse=True)
        valid_hafu = [h for h in raw_hafu if not h["is_invalid"] and h["drop"] >= 0.20][:2]
        invalid_hafu = [h for h in raw_hafu if h["is_invalid"]][:2]
        hafu_items = valid_hafu + invalid_hafu

    m10_hub["hafu_analysis"] = {
        "items": hafu_items,
        "has_recommendation": len([h for h in hafu_items if not h["is_invalid"]]) > 0
    }

    return m10_hub
