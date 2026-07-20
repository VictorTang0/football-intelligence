import json
import os
import re

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
weights_path = os.path.join(base_dir, "data", "weights.json")
script_path = os.path.join(base_dir, "scripts", "update_odds_and_news.py")

# 1. Update weights.json
with open(weights_path, "r", encoding="utf-8") as f:
    weights_db = json.load(f)

# Check if M09 already exists
if not any(f["id"] == "M09" for f in weights_db["factors"]):
    new_factor = {
        "id": "M09",
        "name": "历史交锋与心理克制",
        "weight": 0.08,
        "initial": 0.08,
        "category": "战术心理",
        "delta": 0.0,
        "type": "base"
    }
    
    # Scale existing factor weights to make room for M09
    total_w = sum(f["weight"] for f in weights_db["factors"])
    if total_w > 0:
        for f in weights_db["factors"]:
            f["weight"] = round(f["weight"] * 0.92, 4)
            
    weights_db["factors"].append(new_factor)
    
    # Add M09 to narrative expert dimensions
    if "narrative" in weights_db["experts"]:
        dims = weights_db["experts"]["narrative"]["dimensions"]
        if "M09" not in dims:
            dims.append("M09")
            
    # Normalize weights to exactly 1.0
    final_sum = sum(f["weight"] for f in weights_db["factors"])
    diff = round(1.0 - final_sum, 4)
    if diff != 0.0:
        weights_db["factors"][0]["weight"] = round(weights_db["factors"][0]["weight"] + diff, 4)
        
    with open(weights_path, "w", encoding="utf-8") as f:
        json.dump(weights_db, f, ensure_ascii=False, indent=2)
    print("✅ Successfully added M09 factor and expert dimensions to weights.json.")
else:
    print("ℹ️ M09 factor already exists in weights.json.")


# 2. Update update_odds_and_news.py to compute M09 factor score
with open(script_path, "r", encoding="utf-8") as f:
    script_content = f.read()

# Define the M09 calculation code to insert before factor_scores dictionary is defined
m09_calc_code = """    # 9. Historical H2H & Psychological Dominance (M09)
    h2h_matches = m.get("h2h", {}).get("last_5", [])
    if not h2h_matches:
        h2h_matches = m.get("head_to_head", {}).get("last_5", [])
        
    m09_home = 5.0
    m09_away = 5.0
    if h2h_matches:
        home_points = 0
        away_points = 0
        valid_matches = 0
        for game in h2h_matches:
            g_home = game.get("home", "")
            g_away = game.get("away", "")
            g_outcome = game.get("outcome", "D")
            
            # Check if the past home is current home
            past_home_is_curr_home = (g_home == home) or (home in g_home)
            past_home_is_curr_away = (g_home == away) or (away in g_home)
            past_away_is_curr_home = (g_away == home) or (home in g_away)
            past_away_is_curr_away = (g_away == away) or (away in g_away)
            
            if (past_home_is_curr_home and past_away_is_curr_away) or (past_home_is_curr_away and past_away_is_curr_home):
                valid_matches += 1
                if g_outcome == "H":
                    if past_home_is_curr_home:
                        home_points += 3
                    else:
                        away_points += 3
                elif g_outcome == "A":
                    if past_away_is_curr_home:
                        home_points += 3
                    else:
                        away_points += 3
                else:
                    home_points += 1
                    away_points += 1
                    
        if valid_matches > 0:
            max_pts = 3.0 * valid_matches
            diff_pts = home_points - away_points
            scale = 3.0 * (diff_pts / max_pts)
            m09_home = round(5.0 + scale, 1)
            m09_away = round(5.0 - scale, 1)

    m["factor_scores"] = {"""

# Replace definition of factor_scores in update_odds_and_news.py
old_factor_scores_start = '    m["factor_scores"] = {'
if old_factor_scores_start in script_content and m09_calc_code not in script_content:
    script_content = script_content.replace(old_factor_scores_start, m09_calc_code)
    
    # Also add M09 mapping inside the factor_scores dict definition
    old_m08_definition = """        "M08_战意与抢分压力": {
            "home_score": m08_home,
            "away_score": m08_away,
            "weight": 0.13,
            "signal": f"{home if m08_home > m08_away else away}抢分战意更浓" if m08_home != m08_away else "均有抢分期望"
        }
    }"""
    
    new_m08_and_m09_definition = """        "M08_战意与抢分压力": {
            "home_score": m08_home,
            "away_score": m08_away,
            "weight": 0.13,
            "signal": f"{home if m08_home > m08_away else away}抢分战意更浓" if m08_home != m08_away else "均有抢分期望"
        },
        "M09_历史交锋与心理克制": {
            "home_score": m09_home,
            "away_score": m09_away,
            "weight": 0.08,
            "signal": f"{home if m09_home > m09_away else away}交锋占优" if m09_home != m09_away else "交锋势均力敌"
        }
    }"""
    
    script_content = script_content.replace(old_m08_definition, new_m08_and_m09_definition)
    
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    print("✅ Successfully injected M09 calculation logic and dictionary into update_odds_and_news.py.")
else:
    print("ℹ️ M09 logic is already injected or old pattern not found in update_odds_and_news.py.")
