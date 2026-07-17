import json
import os

# Set up working directory and paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
config_path = os.path.join(base_dir, "data", "config.json")

def calibrate():
    # 1. Load matches database
    if not os.path.exists(matches_path):
        print(f"Error: matches.json not found at {matches_path}")
        return
        
    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)
        
    finished_matches = [m for m in matches_db["matches"] if m.get("status") == "finished"]
    print(f"Loaded {len(finished_matches)} finished matches with odds/sentiment data.")
    
    if not finished_matches:
        print("No finished matches found to calibrate. Exiting.")
        return
        
    # Grid search parameters
    trap_candidates = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    protect_candidates = [-0.01, -0.02, -0.03, -0.04, -0.05, -0.06, -0.07, -0.08, -0.09, -0.10]
    
    best_accuracy = 0.0
    best_trap = 0.04
    best_protect = -0.02
    
    # Store results for grid search
    grid_results = []
    
    for trap_t in trap_candidates:
        for protect_t in protect_candidates:
            correct_count = 0
            evaluated_count = 0
            
            for m in finished_matches:
                # Get pinnacle odds
                odds_analysis = m.get("odds_analysis", {})
                pinnacle = odds_analysis.get("pinnacle", {})
                current_odds = pinnacle.get("current")
                initial_odds = pinnacle.get("initial")
                
                if not current_odds or not initial_odds:
                    continue
                    
                oh, od, oa = current_odds.get("home"), current_odds.get("draw"), current_odds.get("away")
                ih, id_, ia = initial_odds.get("home"), initial_odds.get("draw"), initial_odds.get("away")
                
                if not all([oh, od, oa, ih, id_, ia]):
                    continue
                    
                # Get retail sentiment
                sentiment = odds_analysis.get("retail_sentiment", {})
                if "home_pct" in sentiment:
                    sh = sentiment["home_pct"] / 100.0
                    sd = sentiment["draw_pct"] / 100.0
                    sa = sentiment["away_pct"] / 100.0
                else:
                    sh = sentiment.get("home_support", 0.33)
                    sd = sentiment.get("draw_support", 0.33)
                    sa = sentiment.get("away_support", 0.33)
                    
                # Calculate Kelly values
                kelly_h = oh * sh
                kelly_d = od * sd
                kelly_a = oa * sa
                
                diff_h = oh - ih
                diff_d = od - id_
                diff_a = oa - ia
                
                # Determine actual result
                actual_str = m.get("ultimate_conclusion", {}).get("actual_result", "")
                if not actual_str or "-" not in actual_str:
                    continue
                    
                try:
                    score_part = [p for p in actual_str.split() if "-" in p][0]
                    home_g, away_g = map(int, score_part.split("-"))
                except Exception:
                    continue
                    
                actual_outcome = "draw"
                if home_g > away_g:
                    actual_outcome = "home"
                elif home_g < away_g:
                    actual_outcome = "away"
                    
                # Calculate prediction
                kellys = [("home", kelly_h, diff_h), ("draw", kelly_d, diff_d), ("away", kelly_a, diff_a)]
                kellys.sort(key=lambda x: x[1])
                
                best_protected = kellys[0][0] # Lowest Kelly value
                worst_risk = kellys[-1][0]    # Highest Kelly value
                worst_diff = kellys[-1][2]    # Odds difference for worst risk
                
                worst_move = "stable"
                if worst_diff <= protect_t:
                    worst_move = "protect"
                elif worst_diff >= trap_t:
                    worst_move = "trap"
                    
                predicted_outcome = ""
                if worst_move == "protect":
                    predicted_outcome = worst_risk
                elif worst_move == "trap":
                    # Opposite of worst risk
                    if worst_risk == "home":
                        # If actual is draw or away, prediction is correct
                        predicted_outcome = "not_home"
                    elif worst_risk == "away":
                        predicted_outcome = "not_away"
                    else:
                        predicted_outcome = "not_draw"
                else:
                    predicted_outcome = best_protected
                    
                # Check correctness
                is_correct = False
                if predicted_outcome == "not_home":
                    is_correct = actual_outcome in ["draw", "away"]
                elif predicted_outcome == "not_away":
                    is_correct = actual_outcome in ["home", "draw"]
                elif predicted_outcome == "not_draw":
                    is_correct = actual_outcome in ["home", "away"]
                else:
                    is_correct = predicted_outcome == actual_outcome
                    
                if is_correct:
                    correct_count += 1
                evaluated_count += 1
                
            if evaluated_count > 0:
                accuracy = correct_count / evaluated_count
                grid_results.append((trap_t, protect_t, accuracy, correct_count, evaluated_count))
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_trap = trap_t
                    best_protect = protect_t
                    
    print(f"Calibration Grid Search completed.")
    print(f"Best Accuracy: {best_accuracy*100:.2f}% (Trap: {best_trap:+.2f}, Protect: {best_protect:+.2f})")
    
    # 2. Update config.json with calibrated thresholds
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_db = json.load(f)
            
        config_db["odds_trap_threshold"] = best_trap
        config_db["odds_protect_threshold"] = best_protect
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_db, f, ensure_ascii=False, indent=2)
            
        print("Updated data/config.json with calibrated thresholds.")
    else:
        print("Warning: config.json not found to save thresholds.")

if __name__ == "__main__":
    calibrate()
