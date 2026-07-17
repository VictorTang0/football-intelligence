import json
import os
import math
import copy
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
weights_path = os.path.join(base_dir, "data", "weights.json")

def calculate_moe_score(factor_scores, factor_weights, experts):
    # Calculate dimension scores
    dim_scores = {}
    for key, val in factor_scores.items():
        fid = key.split("_")[0]
        home_score = val.get("home_score", 5.0)
        away_score = val.get("away_score", 5.0)
        diff = home_score - away_score
        dim_scores[fid] = diff * factor_weights.get(fid, 0)
        
    # Aggregate into Experts
    expert_votes = {}
    for exp_id, exp_data in experts.items():
        score = 0
        dims = exp_data.get("dimensions", [])
        if dims:
            score = sum(dim_scores.get(d, 0) for d in dims)
        expert_votes[exp_id] = score * exp_data.get("weight", 0)
        
    # Final combined score delta
    return sum(expert_votes.values())

def get_actual_outcome(actual_str, home_team, away_team):
    if not actual_str or "-" not in actual_str: return None
    try:
        score_part = [p for p in actual_str.split() if "-" in p][0]
        hg, ag = map(int, score_part.split("-"))
        if hg > ag: return "home"
        if hg < ag: return "away"
        return "draw"
    except Exception:
        return None

def compute_mse(finished_matches, factor_weights, experts):
    total_mse = 0
    valid_count = 0
    for m in finished_matches:
        actual_str = m.get("ultimate_conclusion", {}).get("actual_result", "")
        outcome = get_actual_outcome(actual_str, m["home"], m["away"])
        if not outcome: continue
        
        # Target mapping: home win=1.0, draw=0.0, away win=-1.0
        target = 1.0 if outcome == "home" else (-1.0 if outcome == "away" else 0.0)
        
        # Predict
        pred_score = calculate_moe_score(m.get("factor_scores", {}), factor_weights, experts)
        # Normalize pred_score to roughly [-1.0, 1.0] domain
        pred_normalized = max(-1.0, min(1.0, pred_score / 2.0))
        
        error = (target - pred_normalized) ** 2
        total_mse += error
        valid_count += 1
        
    return total_mse / valid_count if valid_count > 0 else 0

def run_backprop_sandbox():
    with open(weights_path, "r", encoding="utf-8") as f:
        weights_db = json.load(f)
    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)
        
    finished_matches = [m for m in matches_db["matches"] if m.get("status") == "finished"]
    print(f"Starting Error Backpropagation Sandbox with {len(finished_matches)} matches...")
    if not finished_matches:
        return
        
    base_factors = {f["id"]: f["weight"] for f in weights_db["factors"]}
    base_experts = copy.deepcopy(weights_db.get("experts", {}))
    if not base_experts:
        print("MoE experts not found in weights.json. Exiting.")
        return
    
    current_mse = compute_mse(finished_matches, base_factors, base_experts)
    print(f"Current Baseline MSE: {current_mse:.4f}")
    
    # 1. Grid Perturbation for Factor Weights (M01-M08)
    best_factors = copy.deepcopy(base_factors)
    best_mse = current_mse
    learning_rate = 0.05
    
    print("Testing factor perturbations...")
    for fid in base_factors:
        for direction in [1, -1]:
            test_factors = copy.deepcopy(best_factors)
            test_factors[fid] += direction * learning_rate
            # Normalize
            total = sum(test_factors.values())
            test_factors = {k: v/total for k, v in test_factors.items()}
            
            mse = compute_mse(finished_matches, test_factors, base_experts)
            if mse < best_mse:
                best_mse = mse
                best_factors = copy.deepcopy(test_factors)
                print(f"  > Improved MSE to {best_mse:.4f} by adjusting {fid}")
                
    # 2. Grid Perturbation for MoE Experts
    best_experts = copy.deepcopy(base_experts)
    print("Testing MoE Expert perturbations...")
    for exp_id in base_experts:
        for direction in [1, -1]:
            test_exp = copy.deepcopy(best_experts)
            test_exp[exp_id]["weight"] += direction * learning_rate
            # Normalize
            total = sum(e["weight"] for e in test_exp.values())
            if total > 0:
                for k in test_exp:
                    test_exp[k]["weight"] = round(test_exp[k]["weight"] / total, 4)
                
            mse = compute_mse(finished_matches, best_factors, test_exp)
            if mse < best_mse:
                best_mse = mse
                best_experts = copy.deepcopy(test_exp)
                print(f"  > Improved MSE to {best_mse:.4f} by adjusting Expert: {exp_id}")
                
    # Write back if improved
    if best_mse < current_mse:
        print(f"Applying new optimized weights. Final MSE: {best_mse:.4f}")
        for f in weights_db["factors"]:
            f["weight"] = round(best_factors[f["id"]], 4)
        weights_db["experts"] = best_experts
        weights_db["last_evolved"] = datetime.now().isoformat()
        
        with open(weights_path, "w", encoding="utf-8") as f:
            json.dump(weights_db, f, ensure_ascii=False, indent=2)
    else:
        print("No improvement found in this sandbox iteration. Weights remain unchanged.")

if __name__ == "__main__":
    run_backprop_sandbox()
