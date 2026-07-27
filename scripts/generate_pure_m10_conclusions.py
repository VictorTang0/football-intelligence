import json
import os
import re

def deduce_pure_m10(match):
    """
    100% 纯 M10 资金水温与背离系统独立推理引擎
    只根据 M10 水温偏好、欧亚赔率背离 (lottery vs pinnacle/asian) 独立推导五项结论
    """
    conclusions = match.get("conclusions", {})
    m10_pref = conclusions.get("m10_preference", "无推荐")
    m10_applied = conclusions.get("m10_applied", False)
    m10_count = conclusions.get("m10_snapshot_count", 0)
    
    odds = match.get("odds_analysis", {})
    lot = odds.get("lottery_handicap", {}).get("current", {})
    pin = odds.get("pinnacle", {}).get("current", {})
    ah = odds.get("asian_handicap", {}).get("current", {})
    
    w_lot = float(lot.get("win", 0)) if lot.get("win") else 0
    d_lot = float(lot.get("draw", 0)) if lot.get("draw") else 0
    l_lot = float(lot.get("lose", 0)) if lot.get("lose") else 0

    w_pin = float(pin.get("home", 0)) if pin.get("home") else 0
    l_pin = float(pin.get("away", 0)) if pin.get("away") else 0

    # 1. 胜平负 (HAD) M10 推导 (降低触发门槛至 N >= 3 次快照)
    m10_had = "无推荐"
    if m10_applied or m10_count >= 3:
        if w_lot > 0 and w_pin > 0:
            if w_lot < w_pin:
                m10_had = "主胜"
            elif l_lot < l_pin:
                m10_had = "客胜"
            else:
                m10_had = "主不败"
        elif "主" in m10_pref:
            m10_had = "主胜"
        elif "客" in m10_pref:
            m10_had = "客胜"
        elif "平" in m10_pref:
            m10_had = "平局"

    # 2. 让球胜平负 (HHAD) M10 推导
    m10_hhad = "无推荐"
    if m10_had != "无推荐":
        if "主胜" in m10_had:
            m10_hhad = "让胜" if w_lot < 2.0 else "让平"
        elif "客" in m10_had:
            m10_hhad = "让负"
        elif "平局" in m10_had:
            m10_hhad = "让平"
        elif "主不败" in m10_had:
            m10_hhad = "让胜"

    # 3. 比分 (Predicted Score) M10 推导
    m10_score = "无推荐"
    if m10_had == "主胜":
        m10_score = "2-0 或 2-1"
    elif m10_had == "客胜":
        m10_score = "0-2 或 1-2"
    elif m10_had == "平局":
        m10_score = "1-1 或 0-0"
    elif m10_had == "主不败":
        m10_score = "1-0 或 1-1"

    # 4. 具体进球数 (Total Goals) M10 推导
    m10_goals = "无推荐"
    if m10_had != "无推荐":
        if "大" in m10_pref or w_lot >= 2.5 or l_lot >= 2.5:
            m10_goals = "大 2.5"
        else:
            m10_goals = "小 2.5"

    # 5. 半全场 (Half-Full) M10 推导
    m10_hf = "无推荐"
    if m10_had == "主胜":
        m10_hf = "胜胜 或 平胜"
    elif m10_had == "客胜":
        m10_hf = "负负 或 平负"
    elif m10_had == "平局":
        m10_hf = "平平"
    elif m10_had == "主不败":
        m10_hf = "平胜 或 平平"

    # 动态置信度计算：N=3起步 75%，随着快照次数增加递增，最高95%
    if m10_count >= 3:
        conf = min(95, 66 + m10_count * 4)
    else:
        conf = 50

    return {
        "m10_had": m10_had,
        "m10_hhad": m10_hhad,
        "m10_score": m10_score,
        "m10_goals": m10_goals,
        "m10_hf": m10_hf,
        "confidence": conf
    }

def update_pure_m10_hub():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    
    if not os.path.exists(matches_path):
        return

    with open(matches_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    updated_count = 0
    for m in db.get("matches", []):
        res = deduce_pure_m10(m)
        m10_dict = {
            "had_recommendation": res["m10_had"],
            "hhad_recommendation": res["m10_hhad"],
            "predicted_score": res["m10_score"],
            "over_under": res["m10_goals"],
            "half_full": res["m10_hf"],
            "confidence": res["confidence"]
        }
        m["m10_hub_analysis"] = m10_dict
        updated_count += 1

    with open(matches_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"✅ [纯M10独立中枢生成完毕] 已为 {updated_count} 场比赛写全100%纯度的M10五项推演结论!")

if __name__ == "__main__":
    update_pure_m10_hub()
