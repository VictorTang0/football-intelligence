import json
import os
import re
import math

def calculate_sigmoid_score(value, center, scale):
    """
    使用 Sigmoid 连续平滑函数将原始数据指标映射为 0.0 ~ 100.0 的连续百分制 Score
    """
    x = (value - center) / scale
    sigmoid = 1.0 / (1.0 + math.exp(-x))
    return round(sigmoid * 100.0, 1)

def get_level_from_score(score):
    """
    将 0~100 的连续实数 Score 映射为 5 大直观段位
    """
    if score >= 90.0:
        return 5, "史诗壁垒"
    elif score >= 75.0:
        return 4, "统治级"
    elif score >= 60.0:
        return 3, "高能级"
    elif score >= 40.0:
        return 2, "初具规模"
    else:
        return 1, "萌芽级"

def compute_continuous_tags(stats):
    p = stats.get("played", 0)
    if p < 1:
        return {}

    avg_gf = stats["goals_for"] / p
    avg_ga = stats["goals_against"] / p
    draw_rate = stats["draws"] / p
    home_win_rate = (stats["home_wins"] / stats["home_played"]) if stats.get("home_played", 0) > 0 else 0
    comebacks = stats.get("comeback", 0)
    
    tags = {}

    # 1. 灌球高手 (Offensive Master) — 连续实数 Score (0~100)
    if avg_gf >= 1.2:
        score = calculate_sigmoid_score(avg_gf, center=1.8, scale=0.4)
        lvl, lvl_name = get_level_from_score(score)
        weight_boost = round((score / 100.0) * 0.30, 4) # 最大 +30% 加权
        tags["灌球高手"] = {
            "score": score,
            "level": lvl,
            "level_name": lvl_name,
            "weight_boost": weight_boost,
            "confidence": min(99, int(60 + score * 0.4)),
            "desc": f"场均轰入 {avg_gf:.2f} 球 (连续得分: {score}分)"
        }

    # 2. 铜墙铁壁 (Iron Fortress) — 连续实数 Score (失球越低得分越高)
    if avg_ga <= 1.3:
        inv_ga = 2.0 - avg_ga
        score = calculate_sigmoid_score(inv_ga, center=1.2, scale=0.35)
        lvl, lvl_name = get_level_from_score(score)
        weight_boost = round((score / 100.0) * 0.30, 4)
        tags["铜墙铁壁"] = {
            "score": score,
            "level": lvl,
            "level_name": lvl_name,
            "weight_boost": weight_boost,
            "confidence": min(99, int(60 + score * 0.4)),
            "desc": f"场均失球仅 {avg_ga:.2f} 球 (连续得分: {score}分)"
        }

    # 3. 主场狂魔 (Home Dominator)
    hp = stats.get("home_played", 0)
    if hp >= 2 and home_win_rate >= 0.35:
        score = calculate_sigmoid_score(home_win_rate, center=0.55, scale=0.15)
        lvl, lvl_name = get_level_from_score(score)
        weight_boost = round((score / 100.0) * 0.30, 4)
        tags["主场狂魔"] = {
            "score": score,
            "level": lvl,
            "level_name": lvl_name,
            "weight_boost": weight_boost,
            "confidence": min(99, int(60 + score * 0.4)),
            "desc": f"主场胜率达 {home_win_rate*100:.1f}% (连续得分: {score}分)"
        }

    # 4. 平局大师 (Draw Specialist)
    if draw_rate >= 0.20:
        score = calculate_sigmoid_score(draw_rate, center=0.32, scale=0.08)
        lvl, lvl_name = get_level_from_score(score)
        weight_boost = round((score / 100.0) * 0.30, 4)
        tags["平局大师"] = {
            "score": score,
            "level": lvl,
            "level_name": lvl_name,
            "weight_boost": weight_boost,
            "confidence": min(99, int(60 + score * 0.4)),
            "desc": f"平局率达 {draw_rate*100:.1f}% (连续得分: {score}分)"
        }

    # 5. 逆转专家 (Comeback King)
    if comebacks >= 1:
        score = min(98.0, round(55.0 + comebacks * 18.0, 1))
        lvl, lvl_name = get_level_from_score(score)
        weight_boost = round((score / 100.0) * 0.30, 4)
        tags["逆转专家"] = {
            "score": score,
            "level": lvl,
            "level_name": lvl_name,
            "weight_boost": weight_boost,
            "confidence": min(99, int(60 + score * 0.4)),
            "desc": f"多次半场落后追平/翻盘 (连续得分: {score}分)"
        }

    # 6. 无心恋战 (Vulnerable Defense)
    if avg_ga >= 1.3:
        score = calculate_sigmoid_score(avg_ga, center=1.7, scale=0.4)
        lvl, lvl_name = get_level_from_score(score)
        weight_boost = round((score / 100.0) * 0.30, 4)
        tags["无心恋战"] = {
            "score": score,
            "level": lvl,
            "level_name": lvl_name,
            "weight_boost": weight_boost,
            "confidence": min(99, int(60 + score * 0.4)),
            "desc": f"场均失球达 {avg_ga:.2f} 球 (连续得分: {score}分)"
        }

    return tags

def evolve_team_tags():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    history_path = os.path.join(base_dir, "data", "history.json")
    train_path = os.path.join(base_dir, "data", "historical_train_2026.json")
    val_path = os.path.join(base_dir, "data", "historical_val_202512.json")
    tags_path = os.path.join(base_dir, "data", "team_tags.json")

    all_match_sources = []
    
    # 1. Load matches.json
    if os.path.exists(matches_path):
        with open(matches_path, "r", encoding="utf-8") as f:
            m_db = json.load(f)
            for m in m_db.get("matches", []):
                res = m.get("ultimate_conclusion", {}).get("actual_result")
                if res and m.get("home") and m.get("away"):
                    all_match_sources.append({"home": m["home"], "away": m["away"], "res": res})
                    
    # 2. Load history.json
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            h_db = json.load(f)
            for r in h_db.get("records", []):
                res = r.get("actual_result")
                if res and r.get("home") and r.get("away"):
                    all_match_sources.append({"home": r["home"], "away": r["away"], "res": res})
                    
    # 3. Load Datasets
    for p in [train_path, val_path]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                db = json.load(f)
                for item in db:
                    home, away, score = item.get("home"), item.get("away"), item.get("fullTimeScore")
                    ht_score = item.get("halfTimeScore", "0:0")
                    if home and away and score:
                        all_match_sources.append({"home": home, "away": away, "res": f"{home} {score} {away} ({ht_score})"})

    team_stats = {}

    for m in all_match_sources:
        home, away, res = m.get("home"), m.get("away"), m.get("res")
        if not home or not away or not res:
            continue
            
        m_ft = re.search(r"(\d+)-(\d+)", str(res))
        if not m_ft:
            continue
        h_g, a_g = int(m_ft.group(1)), int(m_ft.group(2))
        
        m_ht = re.search(r"\((\d+)-(\d+)\)", str(res))
        ht_h, ht_a = (int(m_ht.group(1)), int(m_ht.group(2))) if m_ht else (None, None)
        
        for t_name in [home, away]:
            if t_name not in team_stats:
                team_stats[t_name] = {
                    "played": 0, "home_played": 0, "away_played": 0,
                    "home_wins": 0, "away_wins": 0, "goals_for": 0,
                    "goals_against": 0, "draws": 0, "losses": 0, "comeback": 0
                }

        # Home stats
        team_stats[home]["played"] += 1
        team_stats[home]["home_played"] += 1
        team_stats[home]["goals_for"] += h_g
        team_stats[home]["goals_against"] += a_g
        if h_g > a_g:
            team_stats[home]["home_wins"] += 1
        elif h_g == a_g:
            team_stats[home]["draws"] += 1
        else:
            team_stats[home]["losses"] += 1
            
        if ht_h is not None and ht_h < ht_a and h_g >= a_g:
            team_stats[home]["comeback"] += 1

        # Away stats
        team_stats[away]["played"] += 1
        team_stats[away]["away_played"] += 1
        team_stats[away]["goals_for"] += a_g
        team_stats[away]["goals_against"] += h_g
        if a_g > h_g:
            team_stats[away]["away_wins"] += 1
        elif a_g == h_g:
            team_stats[away]["draws"] += 1
        else:
            team_stats[away]["losses"] += 1

        if ht_a is not None and ht_a < ht_h and a_g >= h_g:
            team_stats[away]["comeback"] += 1

    tags_db = {}
    total_evaluated = 0
    for team, stats in team_stats.items():
        evaluated_tags = compute_continuous_tags(stats)
        if evaluated_tags:
            tags_db[team] = {
                "matches_evaluated": stats["played"],
                "tags": evaluated_tags
            }
            total_evaluated += 1

    with open(tags_path, "w", encoding="utf-8") as f:
        json.dump(tags_db, f, ensure_ascii=False, indent=2)

    print(f"✅ [连续实数 Scoring 升级成功] 已为 {total_evaluated} 支球队演进生成了 0~100 连续精度 Score 评分与 5 大段位!")

if __name__ == "__main__":
    evolve_team_tags()
