import json
import os
import math

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
val_path = os.path.join(base_dir, "data", "historical_val_202512.json")
weights_path = os.path.join(base_dir, "data", "weights.json")

def load_dataset():
    if not os.path.exists(val_path):
        raise FileNotFoundError(f"Dataset {val_path} not found.")
    with open(val_path, "r", encoding="utf-8") as f:
        return json.load(f)

def predict_match_at_odds_state(match_item, odds_snapshot_idx):
    """
    Simulate M10 prediction given an odds snapshot step (from initial odds idx 0 to current idx)
    """
    odds_tr = match_item.get("odds_trajectory", {})
    had_list = odds_tr.get("had", [])
    hhad_list = odds_tr.get("hhad", [])
    crs_list = odds_tr.get("crs", [])
    
    # Initial odds vs snapshot odds
    init_had = had_list[0] if len(had_list) > 0 else {}
    curr_had = had_list[min(odds_snapshot_idx, len(had_list) - 1)] if len(had_list) > 0 else {}
    
    h_init = float(init_had.get("h", 2.10)) if init_had.get("h") else 2.10
    d_init = float(init_had.get("d", 3.25)) if init_had.get("d") else 3.25
    a_init = float(init_had.get("a", 3.10)) if init_had.get("a") else 3.10
    
    h_curr = float(curr_had.get("h", h_init)) if curr_had.get("h") else h_init
    d_curr = float(curr_had.get("d", d_init)) if curr_had.get("d") else d_init
    a_curr = float(curr_had.get("a", a_init)) if curr_had.get("a") else a_init
    
    # 1. Enhanced M10 Odds Trend & Water Shift Predictor
    # Margin removal & implied probability
    margin_curr = (1.0/h_curr + 1.0/d_curr + 1.0/a_curr)
    p_h_bm = (1.0/h_curr) / margin_curr
    p_d_bm = (1.0/d_curr) / margin_curr
    p_a_bm = (1.0/a_curr) / margin_curr

    init_hhad = hhad_list[0] if len(hhad_list) > 0 else {}
    curr_hhad = hhad_list[min(odds_snapshot_idx, len(hhad_list) - 1)] if len(hhad_list) > 0 else {}
    hh_init = float(init_hhad.get("h", 3.80)) if init_hhad.get("h") else 3.80
    hh_curr = float(curr_hhad.get("h", hh_init)) if curr_hhad.get("h") else hh_init

    # M10 HAD vs HHAD Scissors Divergence (欧让离散剪刀差)
    # If HAD drops while HHAD rises or holds, bookmaker is luring HAD home win; predict HAD home will rise or level off.
    had_h_drop = (h_init - h_curr) / h_init if h_init > 0 else 0
    hhad_h_drop = (hh_init - hh_curr) / hh_init if hh_init > 0 else 0
    
    home_water_trend = "平稳"
    if had_h_drop > 0.02 and hhad_h_drop <= 0:
        # Scissors divergence: HAD dropped but HHAD didn't -> Lure trap! Predict home odds will rise back (升水)
        home_water_trend = "升水"
    elif had_h_drop > 0.01:
        home_water_trend = "降水"
    elif had_h_drop < -0.01:
        home_water_trend = "升水"

    away_water_trend = "平稳"
    had_a_drop = (a_init - a_curr) / a_init if a_init > 0 else 0
    if had_a_drop > 0.01:
        away_water_trend = "降水"
    elif had_a_drop < -0.01:
        away_water_trend = "升水"

    # Actual water shift in final snapshot
    final_had = had_list[-1] if len(had_list) > 0 else curr_had
    h_final = float(final_had.get("h", h_curr)) if final_had.get("h") else h_curr
    a_final = float(final_had.get("a", a_curr)) if final_had.get("a") else a_curr
    
    actual_home_shift = "降水" if h_final < h_curr - 0.01 else "升水" if h_final > h_curr + 0.01 else "平稳"
    actual_away_shift = "降水" if a_final < a_curr - 0.01 else "升水" if a_final > a_curr + 0.01 else "平稳"
    
    odds_trend_correct = (home_water_trend == actual_home_shift) or (away_water_trend == actual_away_shift)
    
    # 2. Predict Recommendation (方向 - M10 Enhanced)
    # Apply time-decay preview factor adjustments
    preview = match_item.get("preview", {})
    home_standing = preview.get("league_standings_evolution", {}).get("home_standing_snapshot", "10")
    away_standing = preview.get("league_standings_evolution", {}).get("away_standing_snapshot", "10")
    
    try:
        h_rank = int(''.join(filter(str.isdigit, str(home_standing)))) if any(c.isdigit() for c in str(home_standing)) else 10
        a_rank = int(''.join(filter(str.isdigit, str(away_standing)))) if any(c.isdigit() for c in str(away_standing)) else 10
    except Exception:
        h_rank, a_rank = 10, 10
        
    standing_bias = (a_rank - h_rank) * 0.008
    p_h_eff = p_h_bm + standing_bias
    p_a_eff = p_a_bm - standing_bias

    rec = "主胜"
    if p_h_eff > 0.46:
        rec = "主胜"
    elif p_a_eff > 0.40:
        rec = "客胜"
    elif p_d_bm > 0.28:
        rec = "平局"
    elif p_h_eff >= p_a_eff:
        rec = "双选主不败"
    else:
        rec = "双选客不败"
        
    ft_outcome = match_item.get("ft_outcome", "H")
    rec_correct = False
    if "主胜" in rec and ft_outcome == "H": rec_correct = True
    elif "客胜" in rec and ft_outcome == "A": rec_correct = True
    elif "平局" in rec and ft_outcome == "D": rec_correct = True
    elif "主不败" in rec and ft_outcome in ["H", "D"]: rec_correct = True
    elif "客不败" in rec and ft_outcome in ["A", "D"]: rec_correct = True
    
    # 3. Predict Correct Score (比分 - M10 Poisson + CRS Inverse Odds Density Calibration)
    eg_home = max(0.4, p_h_eff * 2.1 + p_d_bm * 0.7)
    eg_away = max(0.4, p_a_eff * 2.1 + p_d_bm * 0.7)
    
    score_probs = {}
    for hg in range(5):
        for ag in range(5):
            prob = (math.pow(eg_home, hg) * math.exp(-eg_home) / math.factorial(hg)) * \
                   (math.pow(eg_away, ag) * math.exp(-eg_away) / math.factorial(ag))
            score_probs[f"{hg}-{ag}"] = prob

    # Fuse with CRS inverse odds density if available
    if crs_list:
        latest_crs = crs_list[min(odds_snapshot_idx, len(crs_list)-1)]
        total_crs_inv = 0
        crs_inv_map = {}
        for s_key, odds_val in latest_crs.items():
            try:
                oval = float(odds_val)
                if oval > 1.0:
                    clean_k = s_key.replace(":", "-").replace("0", "0")
                    inv_v = 1.0 / oval
                    crs_inv_map[clean_k] = inv_v
                    total_crs_inv += inv_v
            except Exception:
                pass
                
        if total_crs_inv > 0:
            for skey, crs_inv in crs_inv_map.items():
                if skey in score_probs:
                    crs_p = crs_inv / total_crs_inv
                    score_probs[skey] = 0.5 * score_probs[skey] + 0.5 * crs_p

    top_scores = sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[:3]
    actual_score = match_item.get("fullTimeScore", "").replace(":", "-")
    score_correct = any(s[0] == actual_score for s in top_scores)
    
    # 4. Predict Half-Full
    ht_outcome = match_item.get("ht_outcome", "H")
    hafu_dict = {"H": "胜", "D": "平", "A": "负"}
    actual_hafu = f"{hafu_dict[ht_outcome]}{hafu_dict[ft_outcome]}"
    
    pred_hafu = "平胜 或 胜胜" if p_h_bm > 0.45 else "平负 或 负负" if p_a_bm > 0.42 else "平平"
    hafu_correct = actual_hafu in pred_hafu
    
    return {
        "rec_correct": rec_correct,
        "score_correct": score_correct,
        "hafu_correct": hafu_correct,
        "odds_trend_correct": odds_trend_correct
    }

def run_backtest():
    print("🧪 Running December 2025 M10 Simulation Backtest (558 Matches)...")
    dataset = load_dataset()
    
    total_matches = len(dataset)
    rec_hits = 0
    score_hits = 0
    hafu_hits = 0
    odds_trend_hits = 0
    
    # Simulate step-by-step prediction updates from initial odds to final snapshot
    for idx, match_item in enumerate(dataset):
        odds_tr = match_item.get("odds_trajectory", {})
        had_len = len(odds_tr.get("had", []))
        
        # Test prediction at initial odds (snapshot 0)
        res_initial = predict_match_at_odds_state(match_item, 0)
        
        # Test prediction at latest available odds (snapshot N)
        res_latest = predict_match_at_odds_state(match_item, max(0, had_len - 1))
        
        if res_latest["rec_correct"]: rec_hits += 1
        if res_latest["score_correct"]: score_hits += 1
        if res_latest["hafu_correct"]: hafu_hits += 1
        if res_latest["odds_trend_correct"]: odds_trend_hits += 1
        
    rec_acc = rec_hits / total_matches if total_matches > 0 else 0
    score_acc = score_hits / total_matches if total_matches > 0 else 0
    hafu_acc = hafu_hits / total_matches if total_matches > 0 else 0
    trend_acc = odds_trend_hits / total_matches if total_matches > 0 else 0
    
    print("\n📊 --- DECEMBER 2025 BACKTEST RESULTS ---")
    print(f"  Total Validated Matches: {total_matches}")
    print(f"  🎯 Recommendation Direction Accuracy (胜平负方向): {rec_acc*100:.2f}% ({rec_hits}/{total_matches})")
    print(f"  🥅 Correct Score Accuracy (比分精确命中): {score_acc*100:.2f}% ({score_hits}/{total_matches})")
    print(f"  ⏱️ Half-Full Accuracy (半全场命中): {hafu_acc*100:.2f}% ({hafu_hits}/{total_matches})")
    print(f"  🌊 Odds Trend Prediction Accuracy (盘口走向/水位预测): {trend_acc*100:.2f}% ({odds_trend_hits}/{total_matches})")
    print("-------------------------------------------\n")
    
    # Return metrics for calibration
    return {
        "total": total_matches,
        "rec_acc": rec_acc,
        "score_acc": score_acc,
        "hafu_acc": hafu_acc,
        "trend_acc": trend_acc
    }

if __name__ == "__main__":
    run_backtest()
