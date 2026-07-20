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
            "rank": 6,
            "played": 12,
            "won": 6,
            "drawn": 1,
            "lost": 5,
            "points": 19,
            "goals_for": 21,
            "goals_against": 15,
            "zone": "晋级希望区"
        },
        "佐加顿斯": {
            "rank": 4,
            "played": 11,
            "won": 6,
            "drawn": 1,
            "lost": 4,
            "points": 19,
            "goals_for": 18,
            "goals_against": 13,
            "zone": "晋级希望区"
        },
        "卡尔马": {
            "rank": 12,
            "played": 12,
            "won": 4,
            "drawn": 1,
            "lost": 7,
            "points": 13,
            "goals_for": 14,
            "goals_against": 19,
            "zone": "晋级风险区"
        },
        "厄格里特": {
            "rank": 15,
            "played": 12,
            "won": 2,
            "drawn": 3,
            "lost": 7,
            "points": 9,
            "goals_for": 10,
            "goals_against": 21,
            "zone": "晋级无望区"
        },
        "坦山猫": {
            "rank": 9,
            "played": 15,
            "won": 4,
            "drawn": 4,
            "lost": 7,
            "points": 16,
            "goals_for": 25,
            "goals_against": 29,
            "zone": "晋级风险区"
        },
        "国际图尔": {
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
            "rank": 7,
            "played": 15,
            "won": 6,
            "drawn": 4,
            "lost": 5,
            "points": 22,
            "goals_for": 20,
            "goals_against": 16,
            "zone": "晋级希望区"
        },
        "玛丽港": {
            "rank": 12,
            "played": 15,
            "won": 0,
            "drawn": 4,
            "lost": 11,
            "points": 4,
            "goals_for": 8,
            "goals_against": 33,
            "zone": "晋级无望区"
        },
        "拉赫蒂": {
            "rank": 8,
            "played": 15,
            "won": 5,
            "drawn": 4,
            "lost": 6,
            "points": 19,
            "goals_for": 18,
            "goals_against": 15,
            "zone": "晋级希望区"
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
