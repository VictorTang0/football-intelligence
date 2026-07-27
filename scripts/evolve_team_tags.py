import json
import os
import re
import math
from datetime import datetime

def calculate_sigmoid_score(value, center, scale):
    x = (value - center) / scale
    sigmoid = 1.0 / (1.0 + math.exp(-x))
    return round(sigmoid * 100.0, 1)

def get_level_from_score(score):
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

# 标签互斥与消融矩阵 (Tag Mutual Exclusion Matrix)
MUTUAL_EXCLUSIONS = [
    ("铜墙铁壁", "无心恋战"),   # 防守好 vs 防守烂 互斥
    ("抢分狂魔", "连败沉沦"),   # 拿分强 vs 连败 互斥
    ("主场狂魔", "主场陷落")    # 主场强 vs 主场弱 互斥
]

def resolve_mutual_exclusions(tags_dict):
    """
    当球队同时触发互斥标签时，保留 Score 较高者，强行消融 (Suppress) 低 Score 标签
    """
    for tag_a, tag_b in MUTUAL_EXCLUSIONS:
        if tag_a in tags_dict and tag_b in tags_dict:
            score_a = tags_dict[tag_a].get("score", 0)
            score_b = tags_dict[tag_b].get("score", 0)
            if score_a >= score_b:
                del tags_dict[tag_b]
            else:
                del tags_dict[tag_a]
    return tags_dict

def compute_continuous_tags_with_decay(stats):
    p = stats.get("played", 0)
    if p < 1:
        return {}

    # 1. 小样本惩罚与贝叶斯收缩 (Bayesian Shrinkage Factor)
    # 比赛少于 5 场时，算出的指标强制打折收缩，防止 2 场零封就给 90 分的虚高！
    sample_factor = min(1.0, p / 5.0)

    # 2. 近期指数加权 (EWMA Weighted Stats)
    raw_gf = stats["goals_for"] / p
    raw_ga = stats["goals_against"] / p
    draw_rate = stats["draws"] / p
    home_win_rate = (stats["home_wins"] / stats["home_played"]) if stats.get("home_played", 0) > 0 else 0
    comebacks = stats.get("comeback", 0)
    
    # 结合样本系数修正指标
    avg_gf = raw_gf * (0.6 + 0.4 * sample_factor)
    avg_ga = raw_ga / (0.6 + 0.4 * sample_factor)

    tags = {}

    # 1. 灌球高手 (Offensive Master)
    if avg_gf >= 1.3:
        score = calculate_sigmoid_score(avg_gf, center=1.8, scale=0.4) * sample_factor
        score = round(score, 1)
        if score >= 35.0: # 只有 Score >= 35 才授予，低于 35 自动降级剥夺！
            lvl, lvl_name = get_level_from_score(score)
            weight_boost = round((score / 100.0) * 0.30, 4)
            tags["灌球高手"] = {
                "score": score,
                "level": lvl,
                "level_name": lvl_name,
                "weight_boost": weight_boost,
                "confidence": min(99, int(50 + score * 0.45 * sample_factor)),
                "desc": f"近 {p} 场轰入 {raw_gf:.2f} 球 (连续得分: {score}分)"
            }

    # 2. 铜墙铁壁 (Iron Fortress)
    if avg_ga <= 1.2:
        inv_ga = 2.0 - avg_ga
        score = calculate_sigmoid_score(inv_ga, center=1.2, scale=0.35) * sample_factor
        score = round(score, 1)
        if score >= 35.0:
            lvl, lvl_name = get_level_from_score(score)
            weight_boost = round((score / 100.0) * 0.30, 4)
            tags["铜墙铁壁"] = {
                "score": score,
                "level": lvl,
                "level_name": lvl_name,
                "weight_boost": weight_boost,
                "confidence": min(99, int(50 + score * 0.45 * sample_factor)),
                "desc": f"近 {p} 场失球仅 {raw_ga:.2f} 球 (连续得分: {score}分)"
            }

    # 3. 主场狂魔 (Home Dominator)
    hp = stats.get("home_played", 0)
    if hp >= 2 and home_win_rate >= 0.40:
        h_sample_factor = min(1.0, hp / 4.0)
        score = calculate_sigmoid_score(home_win_rate, center=0.55, scale=0.15) * h_sample_factor
        score = round(score, 1)
        if score >= 35.0:
            lvl, lvl_name = get_level_from_score(score)
            weight_boost = round((score / 100.0) * 0.30, 4)
            tags["主场狂魔"] = {
                "score": score,
                "level": lvl,
                "level_name": lvl_name,
                "weight_boost": weight_boost,
                "confidence": min(99, int(50 + score * 0.45 * h_sample_factor)),
                "desc": f"主场胜率达 {home_win_rate*100:.1f}% (连续得分: {score}分)"
            }

    # 4. 平局大师 (Draw Specialist)
    if draw_rate >= 0.22:
        score = calculate_sigmoid_score(draw_rate, center=0.32, scale=0.08) * sample_factor
        score = round(score, 1)
        if score >= 35.0:
            lvl, lvl_name = get_level_from_score(score)
            weight_boost = round((score / 100.0) * 0.30, 4)
            tags["平局大师"] = {
                "score": score,
                "level": lvl,
                "level_name": lvl_name,
                "weight_boost": weight_boost,
                "confidence": min(99, int(50 + score * 0.45 * sample_factor)),
                "desc": f"平局率达 {draw_rate*100:.1f}% (连续得分: {score}分)"
            }

    # 5. 逆转专家 (Comeback King)
    if comebacks >= 1:
        score = min(98.0, round((50.0 + comebacks * 18.0) * sample_factor, 1))
        if score >= 35.0:
            lvl, lvl_name = get_level_from_score(score)
            weight_boost = round((score / 100.0) * 0.30, 4)
            tags["逆转专家"] = {
                "score": score,
                "level": lvl,
                "level_name": lvl_name,
                "weight_boost": weight_boost,
                "confidence": min(99, int(50 + score * 0.45 * sample_factor)),
                "desc": f"多次半场落后追平/翻盘 (连续得分: {score}分)"
            }

    # 6. 无心恋战 (Vulnerable Defense)
    if raw_ga >= 1.4:
        score = calculate_sigmoid_score(raw_ga, center=1.7, scale=0.4) * sample_factor
        score = round(score, 1)
        if score >= 35.0:
            lvl, lvl_name = get_level_from_score(score)
            weight_boost = round((score / 100.0) * 0.30, 4)
            tags["无心恋战"] = {
                "score": score,
                "level": lvl,
                "level_name": lvl_name,
                "weight_boost": weight_boost,
                "confidence": min(99, int(50 + score * 0.45 * sample_factor)),
                "desc": f"近 {p} 场失球达 {raw_ga:.2f} 球 (连续得分: {score}分)"
            }

    # 3. 触发互斥消融处理 (Resolve Mutual Exclusions)
    tags = resolve_mutual_exclusions(tags)

    return tags

def evolve_team_tags():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    history_path = os.path.join(base_dir, "data", "history.json")
    tags_path = os.path.join(base_dir, "data", "team_tags.json")

    all_match_sources = []
    
    # 优先加载近期 matches.json & history.json 最新战绩 (注重近期样本)
    if os.path.exists(matches_path):
        with open(matches_path, "r", encoding="utf-8") as f:
            m_db = json.load(f)
            for m in m_db.get("matches", []):
                res = m.get("ultimate_conclusion", {}).get("actual_result")
                if res and m.get("home") and m.get("away"):
                    all_match_sources.append({"home": m["home"], "away": m["away"], "res": res})
                    
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            h_db = json.load(f)
            for r in h_db.get("records", []):
                res = r.get("actual_result")
                if res and r.get("home") and r.get("away"):
                    all_match_sources.append({"home": r["home"], "away": r["away"], "res": res})

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
    archived_count = 0
    
    for team, stats in team_stats.items():
        evaluated_tags = compute_continuous_tags_with_decay(stats)
        if evaluated_tags:
            tags_db[team] = {
                "matches_evaluated": stats["played"],
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "tags": evaluated_tags
            }
            total_evaluated += 1
        else:
            # 若 Score 均低或不符合标准，触发销号剥夺逻辑！
            archived_count += 1

    with open(tags_path, "w", encoding="utf-8") as f:
        json.dump(tags_db, f, ensure_ascii=False, indent=2)

    print(f"✅ [升级/降级/消融生命周期演进完毕] 成功为 {total_evaluated} 支球队更新标签，销号/剥夺不符合标准球队 {archived_count} 支!")

if __name__ == "__main__":
    evolve_team_tags()
