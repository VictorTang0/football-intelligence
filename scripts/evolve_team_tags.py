import json
import os
import re

def compute_tag_levels(stats):
    p = stats.get("played", 0)
    if p < 1:
        return {}

    avg_gf = stats["goals_for"] / p
    avg_ga = stats["goals_against"] / p
    draw_rate = stats["draws"] / p
    home_win_rate = (stats["home_wins"] / stats["home_played"]) if stats.get("home_played", 0) > 0 else 0
    comebacks = stats.get("comeback", 0)
    
    tags = {}

    # 1. 灌球高手 (Offensive Master)
    if avg_gf >= 2.5:
        tags["灌球高手"] = {"level": 3, "level_name": "统治级火力", "score": round(avg_gf, 2), "confidence": 95, "desc": f"场均轰入 {avg_gf:.2f} 球，攻击力极其强悍"}
    elif avg_gf >= 2.0:
        tags["灌球高手"] = {"level": 2, "level_name": "高效进攻", "score": round(avg_gf, 2), "confidence": 85, "desc": f"场均轰入 {avg_gf:.2f} 球，锋线产出稳定"}
    elif avg_gf >= 1.6:
        tags["灌球高手"] = {"level": 1, "level_name": "火力积极", "score": round(avg_gf, 2), "confidence": 75, "desc": f"场均轰入 {avg_gf:.2f} 球，具备破门能力"}

    # 2. 铜墙铁壁 (Iron Fortress)
    if avg_ga <= 0.5:
        tags["铜墙铁壁"] = {"level": 3, "level_name": "金刚不坏", "score": round(avg_ga, 2), "confidence": 95, "desc": f"场均仅失 {avg_ga:.2f} 球，防线极具韧性"}
    elif avg_ga <= 0.8:
        tags["铜墙铁壁"] = {"level": 2, "level_name": "坚固防线", "score": round(avg_ga, 2), "confidence": 85, "desc": f"场均失 {avg_ga:.2f} 球，门前防守严密"}
    elif avg_ga <= 1.0:
        tags["铜墙铁壁"] = {"level": 1, "level_name": "防守稳定", "score": round(avg_ga, 2), "confidence": 75, "desc": f"场均失 {avg_ga:.2f} 球，不易溃败"}

    # 3. 主场狂魔 (Home Dominator)
    if home_win_rate >= 0.75 and stats.get("home_played", 0) >= 3:
        tags["主场狂魔"] = {"level": 3, "level_name": "魔鬼主场", "score": round(home_win_rate * 100, 1), "confidence": 92, "desc": f"主场胜率高达 {home_win_rate*100:.1f}%，主场威慑极强"}
    elif home_win_rate >= 0.60 and stats.get("home_played", 0) >= 2:
        tags["主场狂魔"] = {"level": 2, "level_name": "主场强势", "score": round(home_win_rate * 100, 1), "confidence": 82, "desc": f"主场胜率达 {home_win_rate*100:.1f}%，主战拿分稳定"}

    # 4. 平局大师 (Draw Specialist)
    if draw_rate >= 0.40:
        tags["平局大师"] = {"level": 3, "level_name": "平局收割机", "score": round(draw_rate * 100, 1), "confidence": 90, "desc": f"平局率高达 {draw_rate*100:.1f}%，极易打成平局"}
    elif draw_rate >= 0.30:
        tags["平局大师"] = {"level": 2, "level_name": "高发平局", "score": round(draw_rate * 100, 1), "confidence": 80, "desc": f"平局率达 {draw_rate*100:.1f}%，胶着战偏多"}

    # 5. 逆转专家 (Comeback King)
    if comebacks >= 2:
        tags["逆转专家"] = {"level": 3, "level_name": "绝境翻盘王", "score": comebacks, "confidence": 88, "desc": f"多次完成半场落后逆转/追平"}
    elif comebacks >= 1:
        tags["逆转专家"] = {"level": 2, "level_name": "韧性抗压", "score": comebacks, "confidence": 78, "desc": f"具备落后顽强追分能力"}

    # 6. 无心恋战 (Vulnerable Defense)
    if avg_ga >= 2.2:
        tags["无心恋战"] = {"level": 3, "level_name": "重度防线崩盘", "score": round(avg_ga, 2), "confidence": 90, "desc": f"场均失球达 {avg_ga:.2f} 球，防守漏洞大"}
    elif avg_ga >= 1.8:
        tags["无心恋战"] = {"level": 2, "level_name": "防线吃紧", "score": round(avg_ga, 2), "confidence": 80, "desc": f"场均失球 {avg_ga:.2f} 球，防空反击隐患多"}

    # 7. 抢分狂魔 (Points Collector)
    if stats["goals_for"] >= 15 and stats["losses"] <= 2:
        tags["抢分狂魔"] = {"level": 2, "level_name": "强悍抢分", "score": stats["goals_for"], "confidence": 85, "desc": f"不败率高，抢分势头猛"}

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
                    
    # 3. Load 2026 Training & Validation Datasets
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
        evaluated_tags = compute_tag_levels(stats)
        if evaluated_tags:
            tags_db[team] = {
                "matches_evaluated": stats["played"],
                "tags": evaluated_tags
            }
            total_evaluated += 1

    with open(tags_path, "w", encoding="utf-8") as f:
        json.dump(tags_db, f, ensure_ascii=False, indent=2)

    print(f"✅ [球队标签系统演算成功] 已为 {total_evaluated} 支球队量化评估了带有 Level 等级与置信度的标签!")

if __name__ == "__main__":
    evolve_team_tags()
