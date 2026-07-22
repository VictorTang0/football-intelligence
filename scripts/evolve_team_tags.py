import json
import os
import re

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
                    
    # 3. Load 2026 Training Dataset
    if os.path.exists(train_path):
        with open(train_path, "r", encoding="utf-8") as f:
            tr_db = json.load(f)
            for item in tr_db:
                home = item.get("home")
                away = item.get("away")
                score = item.get("fullTimeScore")
                ht_score = item.get("halfTimeScore", "0:0")
                if home and away and score:
                    res_str = f"{home} {score} {away} ({ht_score})"
                    all_match_sources.append({"home": home, "away": away, "res": res_str})

    # 4. Load 2025 December Validation Dataset
    if os.path.exists(val_path):
        with open(val_path, "r", encoding="utf-8") as f:
            v_db = json.load(f)
            for item in v_db:
                home = item.get("home")
                away = item.get("away")
                score = item.get("fullTimeScore")
                ht_score = item.get("halfTimeScore", "0:0")
                if home and away and score:
                    res_str = f"{home} {score} {away} ({ht_score})"
                    all_match_sources.append({"home": home, "away": away, "res": res_str})
    tags_db = {}
    if os.path.exists(tags_path):
        with open(tags_path, "r", encoding="utf-8") as f:
            tags_db = json.load(f)

    team_stats = {}

    for m in all_match_sources:
        home = m.get("home")
        away = m.get("away")
        res = m.get("res")
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

    tags_added = 0
    for team, stats in team_stats.items():
        p = stats["played"]
        if p < 1:
            continue
        
        avg_gf = stats["goals_for"] / p
        avg_ga = stats["goals_against"] / p
        draw_rate = stats["draws"] / p
        home_win_rate = (stats["home_wins"] / stats["home_played"]) if stats["home_played"] > 0 else 0
        
        evolved_tags = set()
        if avg_gf >= 2.0: evolved_tags.add("灌球高手")
        if avg_ga <= 0.8: evolved_tags.add("铜墙铁壁")
        if home_win_rate >= 0.6: evolved_tags.add("主场狂魔")
        if draw_rate >= 0.35: evolved_tags.add("平局大师")
        if stats["goals_for"] >= 3 and stats["losses"] == 0: evolved_tags.add("抢分狂魔")
        if stats["comeback"] >= 1: evolved_tags.add("逆转专家")
        if avg_ga >= 2.0: evolved_tags.add("无心恋战")
        
        if team not in tags_db:
            tags_db[team] = {"tags": {t: "赛果进化模型赋予" for t in evolved_tags}}
            tags_added += len(evolved_tags)
        else:
            existing = tags_db[team].get("tags", {})
            for t in evolved_tags:
                if t not in existing:
                    existing[t] = "赛果进化模型更新"
                    tags_added += 1
            tags_db[team]["tags"] = existing

    with open(tags_path, "w", encoding="utf-8") as f:
        json.dump(tags_db, f, ensure_ascii=False, indent=2)

    print(f"🏷️ [Tag Evolution] Automatically evolved team tags for {len(team_stats)} teams ({len(tags_db)} teams total in database, +{tags_added} tag entries updated).")

if __name__ == "__main__":
    evolve_team_tags()
