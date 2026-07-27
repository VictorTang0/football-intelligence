import json
import os
import math
import copy
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bonus_path = os.path.join(base_dir, "data", "sporttery_bonus.json")
m10_weights_path = os.path.join(base_dir, "data", "m10_weights.json")

def evaluate_m10_on_dataset(dataset, weights, thresholds):
    """
    Evaluates M10 5-dimensional predictions on 415 finished matches using Fixed Bonus trajectories & Official Outcomes
    """
    had_hits, had_total = 0, 0
    hhad_hits, hhad_total = 0, 0
    crs_hits, crs_total = 0, 0
    goals_hits, goals_total = 0, 0
    hafu_hits, hafu_total = 0, 0

    for key, item in dataset.items():
        outcomes = item.get("official_outcomes", {})
        oh = item.get("oddsHistory", {})
        if not outcomes or not oh:
            continue

        actual_had = outcomes.get("had", "")
        actual_hhad = outcomes.get("hhad", "")
        actual_crs = outcomes.get("crs", "")
        actual_ttg = str(outcomes.get("ttg", ""))
        actual_hafu = outcomes.get("hafu", "")

        had_list = oh.get("hadList", [])
        hhad_list = oh.get("hhadList", [])
        crs_list = oh.get("crsList", [])
        ttg_list = oh.get("ttgList", [])
        hafu_list = oh.get("hafuList", [])

        # 1. Evaluate HAD
        if len(had_list) >= 2:
            init_h, curr_h = float(had_list[0].get("h", 0)), float(had_list[-1].get("h", 0))
            init_a, curr_a = float(had_list[0].get("a", 0)), float(had_list[-1].get("a", 0))
            diff_h = init_h - curr_h
            diff_a = init_a - curr_a
            
            if abs(diff_h - diff_a) >= thresholds["had_min_diff"]:
                had_total += 1
                pred_had = "主胜" if diff_h > diff_a else "客胜"
                if pred_had == actual_had:
                    had_hits += 1

        # 2. Evaluate HHAD (Handicap)
        if len(had_list) >= 2 and len(hhad_list) >= 2:
            init_h, curr_h = float(had_list[0].get("h", 0)), float(had_list[-1].get("h", 0))
            init_hhad, curr_hhad = float(hhad_list[0].get("h", 0)), float(hhad_list[-1].get("h", 0))
            scissors_diff = (init_hhad - curr_hhad) - (init_h - curr_h)
            if abs(scissors_diff) >= thresholds["hhad_min_scissors"]:
                hhad_total += 1
                pred_hhad = "让胜" if scissors_diff > 0 else "让负"
                if pred_hhad == actual_hhad:
                    hhad_hits += 1

        # 3. Evaluate CRS (Score)
        if len(crs_list) >= 2:
            init_crs, curr_crs = crs_list[0], crs_list[-1]
            best_drop = 0
            best_score_key = ""
            for skey in init_crs:
                if skey.startswith("s") and not skey.endswith("f") and skey not in ["s-1sh", "s-1sd", "s-1sa"]:
                    try:
                        v_init = float(init_crs.get(skey, 0))
                        v_curr = float(curr_crs.get(skey, 0))
                        if v_init > 0 and v_curr > 0:
                            drop = v_init - v_curr
                            if drop > best_drop:
                                best_drop = drop
                                best_score_key = skey
                    except Exception: pass
            
            if best_drop >= thresholds["crs_min_drop"] and best_score_key:
                crs_total += 1
                formatted = best_score_key.replace("s", "").split("s")
                if len(formatted) == 2:
                    score_str = f"{int(formatted[0])}:{int(formatted[1])}"
                    if score_str == actual_crs:
                        crs_hits += 1

        # 4. Evaluate GOALS (TTG)
        if len(ttg_list) >= 2:
            init_ttg, curr_ttg = ttg_list[0], ttg_list[-1]
            best_g_drop = 0
            best_g = ""
            for gkey in ["s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7"]:
                try:
                    v_init = float(init_ttg.get(gkey, 0))
                    v_curr = float(curr_ttg.get(gkey, 0))
                    if v_init > 0 and v_curr > 0:
                        drop = v_init - v_curr
                        if drop > best_g_drop:
                            best_g_drop = drop
                            best_g = gkey.replace("s", "")
                except Exception: pass

            if best_g_drop >= 0.10 and best_g:
                goals_total += 1
                if best_g == actual_ttg or actual_ttg == f"{best_g}球":
                    goals_hits += 1

        # 5. Evaluate HAFU
        if len(hafu_list) >= 2:
            init_hafu, curr_hafu = hafu_list[0], hafu_list[-1]
            best_hf_drop = 0
            best_hf = ""
            for hfkey in ["hh", "hd", "ha", "dh", "dd", "da", "ah", "ad", "aa"]:
                try:
                    v_init = float(init_hafu.get(hfkey, 0))
                    v_curr = float(curr_hafu.get(hfkey, 0))
                    if v_init > 0 and v_curr > 0:
                        drop = v_init - v_curr
                        if drop > best_hf_drop:
                            best_hf_drop = drop
                            best_hf = hfkey
                except Exception: pass
            
            if best_hf_drop >= thresholds["hafu_min_drop"] and best_hf:
                hafu_total += 1
                hf_map = {"hh":"胜胜", "hd":"胜平", "ha":"胜负", "dh":"平胜", "dd":"平平", "da":"平负", "ah":"负胜", "ad":"负平", "aa":"负负"}
                pred_hafu_text = hf_map.get(best_hf, "")
                if pred_hafu_text and pred_hafu_text == actual_hafu:
                    hafu_hits += 1

    had_acc = had_hits / had_total if had_total > 0 else 0.0
    hhad_acc = hhad_hits / hhad_total if hhad_total > 0 else 0.0
    crs_acc = crs_hits / crs_total if crs_total > 0 else 0.0
    goals_acc = goals_hits / goals_total if goals_total > 0 else 0.0
    hafu_acc = hafu_hits / hafu_total if hafu_total > 0 else 0.0

    weighted_score = (had_acc * weights["w_had"] +
                      hhad_acc * weights["w_hhad"] +
                      crs_acc * weights["w_crs"] +
                      goals_acc * weights["w_goals"] +
                      hafu_acc * weights["w_hafu"])

    return {
        "score": weighted_score,
        "stats": {
            "had": {"hits": had_hits, "total": had_total, "acc": round(had_acc, 4)},
            "hhad": {"hits": hhad_hits, "total": hhad_total, "acc": round(hhad_acc, 4)},
            "crs": {"hits": crs_hits, "total": crs_total, "acc": round(crs_acc, 4)},
            "goals": {"hits": goals_hits, "total": goals_total, "acc": round(goals_acc, 4)},
            "hafu": {"hits": hafu_hits, "total": hafu_total, "acc": round(hafu_acc, 4)}
        }
    }

def train_m10_model():
    if not os.path.exists(bonus_path):
        print("Error: sporttery_bonus.json not found!")
        return

    with open(bonus_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    with open(m10_weights_path, "r", encoding="utf-8") as f:
        m10_weights_db = json.load(f)

    print(f"🧠 Training M10 Master Model on {len(dataset)} official matches...")

    best_weights = copy.deepcopy(m10_weights_db["weights"])
    best_thresholds = copy.deepcopy(m10_weights_db["thresholds"])
    
    baseline = evaluate_m10_on_dataset(dataset, best_weights, best_thresholds)
    best_score = baseline["score"]
    
    print(f"📊 Baseline Accuracy Score: {best_score:.4f}")
    print("  -> HAD Acc:", baseline["stats"]["had"])
    print("  -> HHAD Acc:", baseline["stats"]["hhad"])
    print("  -> CRS Acc:", baseline["stats"]["crs"])
    print("  -> Goals Acc:", baseline["stats"]["goals"])
    print("  -> Hafu Acc:", baseline["stats"]["hafu"])

    # Grid Perturbation Search for Best Threshold Parameters
    for param_name in best_thresholds:
        for delta in [0.02, -0.02, 0.05, -0.05]:
            test_thresh = copy.deepcopy(best_thresholds)
            test_thresh[param_name] = max(0.01, test_thresh[param_name] + delta)
            res = evaluate_m10_on_dataset(dataset, best_weights, test_thresh)
            if res["score"] > best_score:
                best_score = res["score"]
                best_thresholds = test_thresh
                print(f"  > Improved score to {best_score:.4f} by tuning threshold {param_name} -> {best_thresholds[param_name]:.3f}")

    final_res = evaluate_m10_on_dataset(dataset, best_weights, best_thresholds)
    m10_weights_db["weights"] = best_weights
    m10_weights_db["thresholds"] = best_thresholds
    m10_weights_db["total_training_samples"] = len(dataset)
    m10_weights_db["accuracy_stats"] = {
        "had": final_res["stats"]["had"]["acc"],
        "hhad": final_res["stats"]["hhad"]["acc"],
        "crs": final_res["stats"]["crs"]["acc"],
        "goals": final_res["stats"]["goals"]["acc"],
        "hafu": final_res["stats"]["hafu"]["acc"]
    }
    m10_weights_db["last_trained"] = datetime.now().isoformat()

    with open(m10_weights_path, "w", encoding="utf-8") as f:
        json.dump(m10_weights_db, f, ensure_ascii=False, indent=2)

    print("🎉 M10 Offline Master Training Complete! Hyperparameters saved to data/m10_weights.json.")
    print("🎯 Final 5-Dimensional Accuracy Stats:")
    print(json.dumps(m10_weights_db["accuracy_stats"], indent=2))

if __name__ == "__main__":
    train_m10_model()
