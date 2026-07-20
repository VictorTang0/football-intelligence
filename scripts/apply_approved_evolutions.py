import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
profiles_path = os.path.join(base_dir, "data", "league_profiles.json")
script_path = os.path.join(base_dir, "scripts", "update_odds_and_news.py")

# 1. Update league_profiles.json for韩职 and芬超
with open(profiles_path, "r", encoding="utf-8") as f:
    profiles = json.load(f)

# 韩职: M01 = 0.88, M05 = 0.90
profiles["韩职"]["modifiers"]["M01"] = 0.88
profiles["韩职"]["modifiers"]["M05"] = 0.90

# 芬超: M04 = 0.80, M03 = 1.20
profiles["芬超"]["modifiers"]["M04"] = 0.80
profiles["芬超"]["modifiers"]["M03"] = 1.20

with open(profiles_path, "w", encoding="utf-8") as f:
    json.dump(profiles, f, ensure_ascii=False, indent=2)
print("✅ Updated league_profiles.json for K-League and Veikkausliiga modifiers.")

# 2. Update update_odds_and_news.py H2H points calculation
with open(script_path, "r", encoding="utf-8") as f:
    script_content = f.read()

# Define the old calculation block
old_calc_block = """            if (past_home_is_curr_home and past_away_is_curr_away) or (past_home_is_curr_away and past_away_is_curr_home):
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
                    away_points += 1"""

# Define the new calculation block with venue weighting (1.5x for same venue)
new_calc_block = """            if (past_home_is_curr_home and past_away_is_curr_away) or (past_home_is_curr_away and past_away_is_curr_home):
                is_same_venue = past_home_is_curr_home and past_away_is_curr_away
                game_weight = 1.5 if is_same_venue else 1.0
                valid_matches += game_weight
                if g_outcome == "H":
                    if past_home_is_curr_home:
                        home_points += 3.0 * game_weight
                    else:
                        away_points += 3.0 * game_weight
                elif g_outcome == "A":
                    if past_away_is_curr_home:
                        home_points += 3.0 * game_weight
                    else:
                        away_points += 3.0 * game_weight
                else:
                    home_points += 1.0 * game_weight
                    away_points += 1.0 * game_weight"""

if old_calc_block in script_content:
    script_content = script_content.replace(old_calc_block, new_calc_block)
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    print("✅ Successfully injected Home/Away venue weighting into M09 calculation in update_odds_and_news.py.")
else:
    print("❌ Old H2H points calculation block not found in update_odds_and_news.py.")
