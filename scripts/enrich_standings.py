import json
import os

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    
    if not os.path.exists(matches_path):
        print("matches.json not found!")
        return
        
    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)
        
    # Standing presets for active teams
    standings_map = {
        "马尔默": {
            "rank": 1,
            "played": 15,
            "won": 11,
            "drawn": 2,
            "lost": 2,
            "points": 35,
            "goals_for": 32,
            "goals_against": 11,
            "zone": "安全晋级区"
        },
        "佐加顿斯": {
            "rank": 2,
            "played": 15,
            "won": 9,
            "drawn": 3,
            "lost": 3,
            "points": 30,
            "goals_for": 27,
            "goals_against": 13,
            "zone": "安全晋级区"
        },
        "卡尔马": {
            "rank": 14,
            "played": 15,
            "won": 4,
            "drawn": 3,
            "lost": 8,
            "points": 15,
            "goals_for": 17,
            "goals_against": 26,
            "zone": "晋级风险区"
        },
        "厄格里特": {
            "rank": 16,
            "played": 15,
            "won": 2,
            "drawn": 3,
            "lost": 10,
            "points": 9,
            "goals_for": 11,
            "goals_against": 30,
            "zone": "晋级无望区"
        },
        "坦山猫": {
            "rank": 2,
            "played": 16,
            "won": 9,
            "drawn": 4,
            "lost": 3,
            "points": 31,
            "goals_for": 29,
            "goals_against": 16,
            "zone": "安全晋级区"
        },
        "TPS图尔": {
            "rank": 6,
            "played": 16,
            "won": 7,
            "drawn": 4,
            "lost": 5,
            "points": 25,
            "goals_for": 22,
            "goals_against": 18,
            "zone": "晋级希望区"
        },
        "玛丽港": {
            "rank": 10,
            "played": 16,
            "won": 4,
            "drawn": 4,
            "lost": 8,
            "points": 16,
            "goals_for": 15,
            "goals_against": 24,
            "zone": "晋级风险区"
        },
        "拉赫蒂": {
            "rank": 12,
            "played": 16,
            "won": 2,
            "drawn": 5,
            "lost": 9,
            "points": 11,
            "goals_for": 12,
            "goals_against": 29,
            "zone": "晋级无望区"
        }
    }
    
    updated_count = 0
    for m in matches_db["matches"]:
        home_name = m["team_stats"]["home"]["name"]
        away_name = m["team_stats"]["away"]["name"]
        
        # Populate home standing
        if home_name in standings_map:
            m["team_stats"]["home"]["standing"] = standings_map[home_name]
            updated_count += 1
            
        # Populate away standing
        if away_name in standings_map:
            m["team_stats"]["away"]["standing"] = standings_map[away_name]
            updated_count += 1
            
    with open(matches_path, "w", encoding="utf-8") as f:
        json.dump(matches_db, f, ensure_ascii=False, indent=2)
        
    print(f"🎉 Successfully enriched standing data for {updated_count} teams in matches.json!")

if __name__ == "__main__":
    main()
