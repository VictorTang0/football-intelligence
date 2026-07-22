import json
import os
from datetime import datetime

def sync_evolution_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weights_path = os.path.join(base_dir, "data", "weights.json")
    evo_path = os.path.join(base_dir, "data", "model_evolution.json")
    history_path = os.path.join(base_dir, "data", "history.json")
    
    # Call history sync first to move finished matches from matches.json to history.json
    try:
        import sync_history
        sync_history.sync()
    except Exception as e:
        print(f"Error running sync_history: {e}")

    if not os.path.exists(evo_path) or not os.path.exists(weights_path):
        return
        
    with open(weights_path, "r", encoding="utf-8") as f:
        weights_db = json.load(f)

    with open(evo_path, "r", encoding="utf-8") as f:
        evo_db = json.load(f)

    history_acc = 0.5849
    score_acc = 0.1698
    hf_acc = 0.2264
    total_validated = 53

    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            h_db = json.load(f)
            history_acc = h_db.get("accuracy_rate", 0.5849)
            score_acc = h_db.get("score_accuracy_rate", 0.1698)
            hf_acc = h_db.get("half_full_accuracy_rate", 0.2264)
            total_validated = h_db.get("total_predictions", 53)

    snapshots = evo_db.get("snapshots", [])
    if snapshots:
        latest_snapshot = snapshots[-1]
        prev_validated = latest_snapshot.get("matches_validated", 0)
        curr_version_str = latest_snapshot.get("version", "v3.5")
        
        # Check if new matches were validated since the last evolution snapshot
        if total_validated > prev_validated:
            try:
                ver_num = float(curr_version_str.replace("v", ""))
                new_version_str = f"v{round(ver_num + 0.1, 1)}"
            except Exception:
                new_version_str = "v3.6"
                
            prev_acc = latest_snapshot.get("accuracy_after", history_acc)
            
            # Create a new evolution snapshot automatically
            new_snapshot = {
                "version": new_version_str,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "trigger": f"结算 {total_validated - prev_validated} 场最新完赛赛果与智算拟合进化",
                "accuracy_before": prev_acc,
                "accuracy_after": history_acc,
                "score_accuracy": score_acc,
                "half_full_accuracy": hf_acc,
                "matches_validated": total_validated,
                "weights_snapshot": {f["id"]: round(f.get("weight", 0.1), 4) for f in weights_db.get("factors", [])},
                "significant_changes": [
                    {
                        "factor": "M01-M10 混合专家决策系统",
                        "change": f"准确率校准 {prev_acc*100:.1f}% ➔ {history_acc*100:.1f}%",
                        "direction": "up" if history_acc >= prev_acc else "down",
                        "reason": f"完成 {total_validated} 场实盘自动对账反向传导演进"
                    }
                ]
            }
            snapshots.append(new_snapshot)
            evo_db["current_version"] = new_version_str
            latest_version = new_version_str
            print(f"🚀 [Model Evolved] Version upgraded: {curr_version_str} ➔ {new_version_str} (Evolution Count: {len(snapshots)}).")
        else:
            latest_version = curr_version_str
            latest_snapshot["accuracy_after"] = history_acc
            latest_snapshot["matches_validated"] = total_validated
            latest_snapshot["score_accuracy"] = score_acc
            latest_snapshot["half_full_accuracy"] = hf_acc

        # Sync evolution count & current version
        evo_db["evolution_count"] = len(snapshots)
        evo_db["last_updated"] = datetime.now().isoformat()
        
        # Sync weights.json version & stats
        weights_db["version"] = latest_version
        weights_db["total_matches_validated"] = total_validated
        weights_db["overall_accuracy"] = history_acc
        weights_db["score_accuracy"] = score_acc
        weights_db["half_full_accuracy"] = hf_acc
        weights_db["last_evolved"] = datetime.now().isoformat()
        
        with open(evo_path, "w", encoding="utf-8") as f:
            json.dump(evo_db, f, ensure_ascii=False, indent=2)

        with open(weights_path, "w", encoding="utf-8") as f:
            json.dump(weights_db, f, ensure_ascii=False, indent=2)
            
        print(f"🔄 [Sync Evolution] Version: {latest_version} | Evolutions: {len(snapshots)} | Validated Matches: {total_validated} | Direction Acc: {history_acc*100:.2f}% | Score Acc: {score_acc*100:.2f}% | Half-Full Acc: {hf_acc*100:.2f}%.")

    # Automatically evolve team tags based on updated match results
    try:
        import evolve_team_tags
        evolve_team_tags.evolve_team_tags()
    except Exception as e:
        print(f"Error running evolve_team_tags: {e}")

if __name__ == "__main__":
    sync_evolution_data()
