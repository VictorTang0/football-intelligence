import json
import os
import random

path = "/Users/movcam/.gemini/antigravity/scratch/football-intelligence/data/matches.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Quality profiles templates
stats_strong = {
    "goals_scored": 28, "goals_conceded": 12, "xg": 26.4, "xga": 11.5,
    "shots_per_game": 14.8, "shots_on_target": 5.4, "conversion_rate": 0.13,
    "possession": 58.2, "pass_accuracy": 85.0, "pressing_intensity": 78.0,
    "set_piece_goals": 5, "counter_attack_speed": 75.0, "clean_sheets": 6,
    "btts_rate": 0.42, "over25_rate": 0.50, "low_block_resilience": 6.8, "superstar_impact": 8.0
}

stats_medium = {
    "goals_scored": 18, "goals_conceded": 17, "xg": 17.5, "xga": 16.8,
    "shots_per_game": 11.2, "shots_on_target": 3.8, "conversion_rate": 0.10,
    "possession": 49.5, "pass_accuracy": 79.8, "pressing_intensity": 62.0,
    "set_piece_goals": 3, "counter_attack_speed": 70.0, "clean_sheets": 4,
    "btts_rate": 0.50, "over25_rate": 0.45, "low_block_resilience": 7.2, "superstar_impact": 6.5
}

stats_weak = {
    "goals_scored": 11, "goals_conceded": 24, "xg": 10.8, "xga": 22.5,
    "shots_per_game": 8.5, "shots_on_target": 2.8, "conversion_rate": 0.08,
    "possession": 42.0, "pass_accuracy": 73.5, "pressing_intensity": 50.0,
    "set_piece_goals": 2, "counter_attack_speed": 65.0, "clean_sheets": 2,
    "btts_rate": 0.38, "over25_rate": 0.35, "low_block_resilience": 8.0, "superstar_impact": 5.0
}

known_teams = {
    # Sweden
    "哥德堡": "medium", "布鲁马波": "medium", "米亚尔比": "strong", "韦斯特罗斯": "weak",
    # Norway
    "博德闪耀": "strong", "腓特烈": "medium",
    # Brazil
    "巴伊亚": "strong", "沙佩科": "weak", "弗鲁米嫩": "medium", "布拉干RB": "medium", "米拉索尔": "medium", "格雷米奥": "weak",
    # MLS
    "纳什维尔": "strong", "亚特联": "weak", "洛城银河": "medium", "洛杉矶FC": "strong",
    # World Cup
    "法国": "strong", "英格兰": "strong", "西班牙": "strong", "阿根廷": "strong",
    # K-League
    "大田市民": "weak", "蔚山现代": "strong", "江原FC": "strong", "金泉尚武": "medium", "济州SK": "medium", "浦项制铁": "strong", "仁川联": "medium", "全北现代": "strong"
}

def generate_randomized_stats(tier):
    if tier == "strong":
        base = stats_strong
    elif tier == "weak":
        base = stats_weak
    else:
        base = stats_medium
        
    result = {}
    for k, v in base.items():
        if isinstance(v, float):
            factor = random.uniform(0.88, 1.12)
            result[k] = round(v * factor, 1)
        elif isinstance(v, int):
            offset = random.randint(-2, 2)
            result[k] = max(0, v + offset)
        else:
            result[k] = v
            
    # Correction boundaries
    if result["conversion_rate"] > 1.0: result["conversion_rate"] = 0.12
    if result["possession"] > 100.0: result["possession"] = 50.0
    if result["pass_accuracy"] > 100.0: result["pass_accuracy"] = 80.0
    
    return result

for m in data["matches"]:
    # Only process pending matches to preserve finished archives
    if m["status"] == "finished":
        continue
        
    home = m["home"]
    away = m["away"]
    home_tier = known_teams.get(home, "medium")
    away_tier = known_teams.get(away, "medium")
    
    print(f"Randomizing stats for: {home} ({home_tier}) vs {away} ({away_tier})")
    
    # Generate unique stats for home and away
    m["team_stats"]["home"]["season_stats"] = generate_randomized_stats(home_tier)
    m["team_stats"]["away"]["season_stats"] = generate_randomized_stats(away_tier)

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n🎉 Successfully randomized all pending matches team statistics!")
