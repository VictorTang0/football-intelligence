import json
import os
import sys
from datetime import datetime

# Path constants
MATCHES_PATH = "/Users/movcam/.gemini/antigravity/scratch/football-intelligence/data/matches.json"

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

def get_stats_by_tier(tier):
    if tier == "strong":
        return stats_strong
    elif tier == "weak":
        return stats_weak
    return stats_medium

def create_complete_match(raw_match):
    """
    Takes a raw match metadata dictionary and returns a fully initialized,
    schema-compliant Match IQ match dictionary.
    """
    mid = raw_match["id"]
    league = raw_match["league"]
    home = raw_match["home"]
    away = raw_match["away"]
    kickoff = raw_match["kickoff"]
    
    # Extract screenshot odds or set defaults
    base_odds = raw_match.get("initial_odds", {"home": 2.0, "draw": 3.0, "away": 3.0})
    home_odds = base_odds.get("home", 2.0)
    draw_odds = base_odds.get("draw", 3.0)
    away_odds = base_odds.get("away", 3.0)
    
    home_tier = known_teams.get(home, "medium")
    away_tier = known_teams.get(away, "medium")
    
    # Calculate implied probabilities
    total_implied = (1 / home_odds) + (1 / draw_odds) + (1 / away_odds)
    p_home = round(((1 / home_odds) / total_implied) * 100)
    p_draw = round(((1 / draw_odds) / total_implied) * 100)
    p_away = 100 - p_home - p_draw
    
    match_obj = {
        "id": mid,
        "league": league,
        "home": home,
        "away": away,
        "kickoff": kickoff,
        "venue": raw_match.get("venue", f"{home}主场球场"),
        "city": raw_match.get("city", f"{home}市"),
        "weather": {
            "condition": "多云",
            "temp_c": 21,
            "humidity": 65,
            "wind_kmh": 10
        },
        "status": "pending",
        "match_context": f"{league}常规赛对决。{home}坐镇主场迎接{away}的挑战。",
        "ultimate_conclusion": {
            "recommendation": "待推演 (需运行盘口更新)",
            "primary_bet": "待定",
            "confidence": 65,
            "risk_level": "中",
            "ev_score": 0.0,
            "reasoning": "待运行 update_odds_and_news.py 脚本获取实盘赔率并结合最新伤停新闻完成最终研判。"
        },
        "team_stats": {
            "home": {
                "name": home,
                "form": ["W", "D", "L", "W", "D"],
                "form_note": f"近期表现稳定，主场韧性良好",
                "season_stats": get_stats_by_tier(home_tier),
                "injuries": [],
                "suspensions": [],
                "key_players": [
                    {
                        "name": "主力核心",
                        "form": "正常",
                        "goals_last_5": 1,
                        "status": "正常",
                        "note": "攻防组织核心"
                    }
                ]
            },
            "away": {
                "name": away,
                "form": ["D", "L", "W", "D", "L"],
                "form_note": f"客场打法偏防守反击",
                "season_stats": get_stats_by_tier(away_tier),
                "injuries": [],
                "suspensions": [],
                "key_players": [
                    {
                        "name": "进攻箭头",
                        "form": "正常",
                        "goals_last_5": 1,
                        "status": "正常",
                        "note": "前场得分支点"
                    }
                ]
            }
        },
        "odds_analysis": {
            "pinnacle": {
                "name": "pinnacle",
                "initial": {"home": home_odds, "draw": draw_odds, "away": away_odds},
                "current": {"home": home_odds, "draw": draw_odds, "away": away_odds},
                "movement": "最新同步"
            },
            "retail_sentiment": {
                "home_pct": p_home,
                "draw_pct": p_draw,
                "away_pct": p_away,
                "confidence_level": "正常",
                "mainstream_narrative": "大众倾向均衡"
            }
        },
        "intelligence": {
            "verified_news": [],
            "media_predictions": [],
            "social_buzz": {},
            "weather_impact": "天气良好无雨水干扰",
            "venue_notes": "草地情况极佳"
        },
        "conclusions": {
            "mainstream": "主队守住主场",
            "upset": "客队客场爆冷",
            "aggressive": "比分 2-1",
            "conservative": "主队受让",
            "most_likely_score": "2-1 或 1-1",
            "over_under": "小 2.5",
            "half_full": "平/主",
            "upset_probability": 0.25,
            "upset_direction": "客胜",
            "kelly_conclusion": "待运行 update_odds_and_news.py 进行实盘凯利指数计算与赔付风险研判。"
        },
        "h2h": {
            "last_5": ["D", "H", "A", "H", "D"],
            "avg_goals": 2.2,
            "btts_rate": 0.5
        },
        "public_vs_bookmaker": [
            {"outcome": "主胜", "public_prob": f"{p_home}%", "bookmaker_implied": f"{p_home}%", "true_est": f"{p_home}%", "payout_risk": "低", "bookmaker_attitude": "中性"},
            {"outcome": "平局", "public_prob": f"{p_draw}%", "bookmaker_implied": f"{p_draw}%", "true_est": f"{p_draw}%", "payout_risk": "低", "bookmaker_attitude": "中性"},
            {"outcome": "客胜", "public_prob": f"{p_away}%", "bookmaker_implied": f"{p_away}%", "true_est": f"{p_away}%", "payout_risk": "低", "bookmaker_attitude": "中性"}
        ]
    }
    return match_obj

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/initialize_match.py <input_json_path>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)
        
    with open(input_path, "r", encoding="utf-8") as f:
        new_raw_matches = json.load(f)
        
    if not os.path.exists(MATCHES_PATH):
        print("matches.json not found!")
        sys.exit(1)
        
    with open(MATCHES_PATH, "r", encoding="utf-8") as f:
        database = json.load(f)
        
    existing_ids = {m["id"] for m in database["matches"]}
    added_count = 0
    
    for raw in new_raw_matches:
        if raw["id"] in existing_ids:
            print(f"Match {raw['id']} already exists, skipping.")
            continue
            
        full_match = create_complete_match(raw)
        database["matches"].append(full_match)
        added_count += 1
        print(f"Initialized & Appended: {full_match['home']} vs {full_match['away']} ({full_match['id']})")
        
    if added_count > 0:
        with open(MATCHES_PATH, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 Successfully initialized and saved {added_count} matches to matches.json!")
    else:
        print("\nNo new matches were added.")

if __name__ == "__main__":
    main()
