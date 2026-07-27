import json
import os
import re

def compute_tag_5levels(stats):
    p = stats.get("played", 0)
    if p < 1:
        return {}

    avg_gf = stats["goals_for"] / p
    avg_ga = stats["goals_against"] / p
    draw_rate = stats["draws"] / p
    home_win_rate = (stats["home_wins"] / stats["home_played"]) if stats.get("home_played", 0) > 0 else 0
    comebacks = stats.get("comeback", 0)
    
    tags = {}

    # 1. 灌球高手 (Offensive Master) — 5 阶平滑划分
    if avg_gf >= 2.8:
        tags["灌球高手"] = {"level": 5, "level_name": "史诗级火力", "weight_boost": 0.30, "score": round(avg_gf, 2), "confidence": 98, "desc": f"场均轰入 {avg_gf:.2f} 球，攻击力极其恐怖"}
    elif avg_gf >= 2.3:
        tags["灌球高手"] = {"level": 4, "level_name": "统治级火力", "weight_boost": 0.22, "score": round(avg_gf, 2), "confidence": 92, "desc": f"场均轰入 {avg_gf:.2f} 球，进攻威慑极高"}
    elif avg_gf >= 1.9:
        tags["灌球高手"] = {"level": 3, "level_name": "高效进攻", "weight_boost": 0.15, "score": round(avg_gf, 2), "confidence": 85, "desc": f"场均轰入 {avg_gf:.2f} 球，锋线产出稳定"}
    elif avg_gf >= 1.5:
        tags["灌球高手"] = {"level": 2, "level_name": "火力积极", "weight_boost": 0.08, "score": round(avg_gf, 2), "confidence": 78, "desc": f"场均轰入 {avg_gf:.2f} 球，破门能力顺畅"}
    elif avg_gf >= 1.2:
        tags["灌球高手"] = {"level": 1, "level_name": "偶有爆发", "weight_boost": 0.04, "score": round(avg_gf, 2), "confidence": 70, "desc": f"场均轰入 {avg_gf:.2f} 球，进攻初具威胁"}

    # 2. 铜墙铁壁 (Iron Fortress) — 5 阶平滑划分
    if avg_ga <= 0.4:
        tags["铜墙铁壁"] = {"level": 5, "level_name": "零封壁垒", "weight_boost": 0.30, "score": round(avg_ga, 2), "confidence": 98, "desc": f"场均仅失 {avg_ga:.2f} 球，门前滴水不漏"}
    elif avg_ga <= 0.65:
        tags["铜墙铁壁"] = {"level": 4, "level_name": "金刚防线", "weight_boost": 0.22, "score": round(avg_ga, 2), "confidence": 92, "desc": f"场均仅失 {avg_ga:.2f} 球，防守防空能力极强"}
    elif avg_ga <= 0.85:
        tags["铜墙铁壁"] = {"level": 3, "level_name": "坚固防线", "weight_boost": 0.15, "score": round(avg_ga, 2), "confidence": 85, "desc": f"场均失 {avg_ga:.2f} 球，门前防守严密"}
    elif avg_ga <= 1.05:
        tags["铜墙铁壁"] = {"level": 2, "level_name": "防守稳定", "weight_boost": 0.08, "score": round(avg_ga, 2), "confidence": 78, "desc": f"场均失 {avg_ga:.2f} 球，不易溃败"}
    elif avg_ga <= 1.2:
        tags["铜墙铁壁"] = {"level": 1, "level_name": "防守合格", "weight_boost": 0.04, "score": round(avg_ga, 2), "confidence": 70, "desc": f"场均失 {avg_ga:.2f} 球，具备基础抗压"}

    # 3. 主场狂魔 (Home Dominator) — 5 阶平滑划分
    hp = stats.get("home_played", 0)
    if hp >= 2:
        if home_win_rate >= 0.85:
            tags["主场狂魔"] = {"level": 5, "level_name": "堡垒禁区", "weight_boost": 0.30, "score": round(home_win_rate * 100, 1), "confidence": 96, "desc": f"主场胜率达 {home_win_rate*100:.1f}%，无解主场壁垒"}
        elif home_win_rate >= 0.70:
            tags["主场狂魔"] = {"level": 4, "level_name": "魔鬼主场", "weight_boost": 0.22, "score": round(home_win_rate * 100, 1), "confidence": 90, "desc": f"主场胜率达 {home_win_rate*100:.1f}%，主场威慑力强"}
        elif home_win_rate >= 0.58:
            tags["主场狂魔"] = {"level": 3, "level_name": "主场强势", "weight_boost": 0.15, "score": round(home_win_rate * 100, 1), "confidence": 84, "desc": f"主场胜率达 {home_win_rate*100:.1f}%，主战拿分稳定"}
        elif home_win_rate >= 0.48:
            tags["主场狂魔"] = {"level": 2, "level_name": "主战积极", "weight_boost": 0.08, "score": round(home_win_rate * 100, 1), "confidence": 76, "desc": f"主场胜率达 {home_win_rate*100:.1f}%，主场有心理优势"}
        elif home_win_rate >= 0.40:
            tags["主场狂魔"] = {"level": 1, "level_name": "主场偏向", "weight_boost": 0.04, "score": round(home_win_rate * 100, 1), "confidence": 70, "desc": f"主场胜率达 {home_win_rate*100:.1f}%，略占便宜"}

    # 4. 平局大师 (Draw Specialist) — 5 阶平滑划分
    if draw_rate >= 0.45:
        tags["平局大师"] = {"level": 5, "level_name": "绝对平局控", "weight_boost": 0.30, "score": round(draw_rate * 100, 1), "confidence": 95, "desc": f"平局率高达 {draw_rate*100:.1f}%，极其偏爱平局"}
    elif draw_rate >= 0.38:
        tags["平局大师"] = {"level": 4, "level_name": "平局收割机", "weight_boost": 0.22, "score": round(draw_rate * 100, 1), "confidence": 88, "desc": f"平局率高达 {draw_rate*100:.1f}%，平局期望极高"}
    elif draw_rate >= 0.30:
        tags["平局大师"] = {"level": 3, "level_name": "高发平局", "weight_boost": 0.15, "score": round(draw_rate * 100, 1), "confidence": 82, "desc": f"平局率达 {draw_rate*100:.1f}%，胶着战偏多"}
    elif draw_rate >= 0.25:
        tags["平局大师"] = {"level": 2, "level_name": "防守相持", "weight_boost": 0.08, "score": round(draw_rate * 100, 1), "confidence": 75, "desc": f"平局率达 {draw_rate*100:.1f}%，经常僵持成平"}
    elif draw_rate >= 0.20:
        tags["平局大师"] = {"level": 1, "level_name": "平局倾向", "weight_boost": 0.04, "score": round(draw_rate * 100, 1), "confidence": 70, "desc": f"平局率达 {draw_rate*100:.1f}%"}

    # 5. 逆转专家 (Comeback King)
    if comebacks >= 3:
        tags["逆转专家"] = {"level": 5, "level_name": "绝地打不死", "weight_boost": 0.30, "score": comebacks, "confidence": 95, "desc": "多次下半场落后实现大逆转"}
    elif comebacks >= 2:
        tags["逆转专家"] = {"level": 3, "level_name": "绝境翻盘王", "weight_boost": 0.15, "score": comebacks, "confidence": 85, "desc": "具备强悍落后追平/翻盘韧性"}
    elif comebacks >= 1:
        tags["逆转专家"] = {"level": 1, "level_name": "韧性抗压", "weight_boost": 0.05, "score": comebacks, "confidence": 75, "desc": "具备落后追分能力"}

    # 6. 无心恋战 (Vulnerable Defense) — 5 阶平滑划分
    if avg_ga >= 2.5:
        tags["无心恋战"] = {"level": 5, "level_name": "灾难级崩盘", "weight_boost": 0.30, "score": round(avg_ga, 2), "confidence": 95, "desc": f"场均失球达 {avg_ga:.2f} 球，防线溃不成军"}
    elif avg_ga >= 2.1:
        tags["无心恋战"] = {"level": 4, "level_name": "重度防线漏洞", "weight_boost": 0.22, "score": round(avg_ga, 2), "confidence": 88, "desc": f"场均失球达 {avg_ga:.2f} 球，门前失误频繁"}
    elif avg_ga >= 1.7:
        tags["无心恋战"] = {"level": 3, "level_name": "防线吃紧", "weight_boost": 0.15, "score": round(avg_ga, 2), "confidence": 82, "desc": f"场均失球 {avg_ga:.2f} 球，防空反击隐患大"}
    elif avg_ga >= 1.4:
        tags["无心恋战"] = {"level": 2, "level_name": "防守松懈", "weight_boost": 0.08, "score": round(avg_ga, 2), "confidence": 75, "desc": f"场均失球 {avg_ga:.2f} 球"}
    elif avg_ga >= 1.2:
        tags["无心恋战"] = {"level": 1, "level_name": "防线隐患", "weight_boost": 0.04, "score": round(avg_ga, 2), "confidence": 70, "desc": f"场均失球 {avg_ga:.2f} 球"}

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
        evaluated_tags = compute_tag_5levels(stats)
        if evaluated_tags:
            tags_db[team] = {
                "matches_evaluated": stats["played"],
                "tags": evaluated_tags
            }
            total_evaluated += 1

    with open(tags_path, "w", encoding="utf-8") as f:
        json.dump(tags_db, f, ensure_ascii=False, indent=2)

    print(f"✅ [5阶平滑评级算法演进完毕] 已为 {total_evaluated} 支球队量化评估了 5 阶精细化平滑标签 (Lv.1 到 Lv.5)!")

if __name__ == "__main__":
    evolve_team_tags()
