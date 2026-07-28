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
    # 6. 💥 真·动态大胆预测比分算子 (True Dynamic Mathematical Outlier Engine)
    m10_bold_score = "无"
    m10_bold_reason = ""
    
    collapse_ratio = (w_pin / w_lot) if (w_lot > 0 and w_pin > 0) else 1.0
    upset_index = match.get("upset_risk_index") or match.get("conclusions", {}).get("upset_risk_index", 50)
    
    # 根据各场比赛的具体赔率区间与水温参数，精准计算个性化极端尾部:
    if m10_had == "主胜":
        if w_pin > 0 and w_pin < 1.65:
            m10_bold_score = "💥 4-0 或 5-0 (屠杀血洗)"
            m10_bold_reason = f"主胜赔率 {w_pin:.2f} 低于 1.65，客队防线崩盘指数 CollapseRatio={collapse_ratio:.2f} 触发"
        elif w_pin >= 1.65 and w_pin < 2.20:
            m10_bold_score = "💥 3-1 或 4-1 (强攻大胜)"
            m10_bold_reason = f"主胜赔率 {w_pin:.2f} 属于强攻区间，攻防两端压制"
        else:
            m10_bold_score = "💥 3-2 或 4-2 (险胜进球大战)"
            m10_bold_reason = f"主胜赔率 {w_pin:.2f} 偏高，防线互相对流对轰"
    elif m10_had == "客胜" or m10_had == "客不败":
        if l_pin > 0 and l_pin < 2.40:
            m10_bold_score = "💥 0-3 或 1-3 (客胜爆冷)"
            m10_bold_reason = f"资金暗中支持客队 (客胜赔 {l_pin:.2f})，冷门指数 UpsetIndex={upset_index}% 触发"
        else:
            m10_bold_score = "💥 1-2 或 2-3 (逆袭对轰)"
            m10_bold_reason = f"客队受让优势明显，反击效率极高"
    elif m10_had == "主不败":
        if d_lot > 0 and d_lot < 3.50:
            m10_bold_score = "💥 2-2 或 3-3 (狂野对轰平局)"
            m10_bold_reason = f"平赔 {d_lot:.2f} 诱导对冲，大球跳水引发惊天高比分平局"
        else:
            m10_bold_score = "💥 3-0 或 4-1 (深盘防冷大胜)"
            m10_bold_reason = "主不败水温锁死下盘，防守反击打穿对手"
    elif m10_had == "平局":
        m10_bold_score = "💥 0-0 (极限闷宫)"
        m10_bold_reason = "水温极度看小，两队铁桶阵密不透风"

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
        "m10_bold_score": m10_bold_score,
        "m10_bold_reason": m10_bold_reason,
        "confidence": conf
    }

def run_python_simulation_1000(m):
    import random
    import math

    odds = m.get("odds_analysis", {}).get("pinnacle", {}).get("current", {})
    h_win_prob = 1.0 / odds.get("home", 2.10) if odds.get("home") else 0.45
    a_win_prob = 1.0 / odds.get("away", 3.10) if odds.get("away") else 0.30

    lambda_h = max(0.6, min(3.8, h_win_prob * 2.7 + 0.35))
    lambda_a = max(0.5, min(3.5, a_win_prob * 2.4))

    inj = m.get("injury_analysis", {})
    lambda_h *= max(0.75, 1.0 - (inj.get("home_absences", 0) * 0.06))
    lambda_a *= max(0.75, 1.0 - (inj.get("away_absences", 0) * 0.06))

    def sample_poisson(lam):
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1

    iterations = 1000
    home_wins, draws, away_wins = 0, 0, 0
    score_freq, hf_freq, wild_map = {}, {}, {}

    for _ in range(iterations):
        fh = 0.85 + random.random() * 0.30
        fa = 0.85 + random.random() * 0.30
        lh, la = lambda_h * fh, lambda_a * fa

        if random.random() < 0.025: lh *= 0.60; la *= 1.35
        if random.random() < 0.025: la *= 0.60; lh *= 1.35

        pen_h = 0.7 if random.random() < 0.10 else 0.0
        pen_a = 0.7 if random.random() < 0.10 else 0.0

        lh1, la1 = lh * 0.42, la * 0.42
        hg1 = sample_poisson(lh1)
        ag1 = sample_poisson(la1)

        bh = 1.30 if hg1 < ag1 else 1.0
        ba = 1.30 if ag1 < hg1 else 1.0

        lh2 = (lh * 0.58 * bh) + pen_h
        la2 = (la * 0.58 * ba) + pen_a
        hg2 = sample_poisson(lh2)
        ag2 = sample_poisson(la2)

        htot, atot = hg1 + hg2, ag1 + ag2
        if htot > atot: home_wins += 1
        elif htot == atot: draws += 1
        else: away_wins += 1

        score_key = f"{htot}-{atot}"
        score_freq[score_key] = score_freq.get(score_key, 0) + 1

        ht_r = "胜" if hg1 > ag1 else "平" if hg1 == ag1 else "负"
        ft_r = "胜" if htot > atot else "平" if htot == atot else "负"
        hf_key = f"{ht_r}{ft_r}"
        hf_freq[hf_key] = hf_freq.get(hf_key, 0) + 1

        if (htot + atot >= 5) or (htot == atot and htot >= 3) or (htot == 0 and atot >= 3) or (atot == 0 and htot >= 4):
            wild_map[score_key] = wild_map.get(score_key, 0) + 1

    top_scores = sorted(score_freq.items(), key=lambda x: x[1], reverse=True)[:4]
    top_hf = sorted(hf_freq.items(), key=lambda x: x[1], reverse=True)[:3]
    top_wild = sorted(wild_map.items(), key=lambda x: x[1], reverse=True)[:2]

    return {
        "iterations": 1000,
        "winRate": {
            "homePct": f"{(home_wins / iterations) * 100:.1f}",
            "drawPct": f"{(draws / iterations) * 100:.1f}",
            "awayPct": f"{(away_wins / iterations) * 100:.1f}"
        },
        "topScores": [{"score": k, "count": v, "pct": f"{(v/iterations)*100:.1f}%"} for k, v in top_scores],
        "topHalfFull": [{"hf": k, "count": v, "pct": f"{(v/iterations)*100:.1f}%"} for k, v in top_hf],
        "wildOutliers": [{"score": k, "count": v, "pct": f"{(v/iterations)*100:.1f}%"} for k, v in top_wild]
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
        sim_res = run_python_simulation_1000(m)
        m10_dict = {
            "had_recommendation": res["m10_had"],
            "hhad_recommendation": res["m10_hhad"],
            "predicted_score": res["m10_score"],
            "over_under": res["m10_goals"],
            "half_full": res["m10_hf"],
            "m10_bold_score": res["m10_bold_score"],
            "m10_bold_reason": res["m10_bold_reason"],
            "confidence": res["confidence"],
            "simulation_1000": sim_res
        }
        m["m10_hub_analysis"] = m10_dict
        updated_count += 1

    with open(matches_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"✅ [纯M10独立中枢生成完毕] 已为 {updated_count} 场比赛写全100%纯度的M10结论与1,000次 Monte Carlo 沙盘推演结果!")

if __name__ == "__main__":
    update_pure_m10_hub()
