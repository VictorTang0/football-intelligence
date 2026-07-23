import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
hist_db_path = os.path.join(base_dir, "data", "official_sporttery_2022_2026.json")
real_feed_path = os.path.join(base_dir, "data", "real_team_recent_matches.json")
override_path = os.path.join(base_dir, "data", "team_recent_matches_override.json")

def load_real_recent_matches(team_name):
    # 0. Highest priority: User-provided / Override truth database
    if os.path.exists(override_path):
        try:
            with open(override_path, "r", encoding="utf-8") as f:
                ov = json.load(f)
                for k, matches in ov.items():
                    if team_name in k or k in team_name or (len(team_name) >= 2 and team_name[:2] in k):
                        if matches: return matches
        except Exception: pass

    # 1. First check user-verified / real feed database with fuzzy key matching
    if os.path.exists(real_feed_path):
        try:
            with open(real_feed_path, "r", encoding="utf-8") as f:
                feed = json.load(f)
                for k, matches in feed.items():
                    if team_name in k or k in team_name or (len(team_name) >= 2 and team_name[:2] in k):
                        if matches: return matches
        except Exception: pass

    # 2. Check full historical database strictly by date descending
    matches = []
    if os.path.exists(hist_db_path):
        try:
            with open(hist_db_path, "r", encoding="utf-8") as f:
                hist_db = json.load(f)
            for item in hist_db:
                h = item.get("homeTeam", "")
                a = item.get("awayTeam", "")
                if team_name in h or team_name in a or h in team_name or a in team_name:
                    dt = item.get("matchDate", "")
                    score = item.get("sectionsNo999", "")
                    ht_score = item.get("sectionsNo1", "")
                    if score and ":" in score:
                        hg, ag = map(int, score.split(":"))
                        outcome = "W" if (team_name in h and hg > ag) or (team_name in a and ag > hg) else "L" if (team_name in h and hg < ag) or (team_name in a and ag < hg) else "D"
                        matches.append({
                            "date": dt,
                            "league": item.get("leagueNameAbbr", ""),
                            "home": h,
                            "away": a,
                            "score": score.replace(":", "-"),
                            "half_score": ht_score.replace(":", "-") if ht_score else "",
                            "outcome": outcome
                        })
        except Exception: pass

    matches.sort(key=lambda x: x["date"], reverse=True)
    return matches[:5]

def main():
    if not os.path.exists(matches_path):
        print("matches.json missing.")
        return

    with open(matches_path, "r", encoding="utf-8") as f:
        database = json.load(f)

    updated = False
    for m in database.get("matches", []):
        if m.get("status") == "finished":
            continue
        home = m.get("home")
        away = m.get("away")

        home_recent = load_real_recent_matches(home)
        away_recent = load_real_recent_matches(away)

        if "team_stats" not in m: m["team_stats"] = {}
        if "home" not in m["team_stats"]: m["team_stats"]["home"] = {}
        if "away" not in m["team_stats"]: m["team_stats"]["away"] = {}

        if home_recent:
            m["team_stats"]["home"]["recent_matches"] = home_recent
            m["team_stats"]["home"]["form"] = [r["outcome"] for r in home_recent]
            updated = True

        if away_recent:
            m["team_stats"]["away"]["recent_matches"] = away_recent
            m["team_stats"]["away"]["form"] = [r["outcome"] for r in away_recent]
            updated = True

    if updated:
        with open(matches_path, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print("✅ Enriched real 2026 recent matches safely!")

if __name__ == "__main__":
    main()
