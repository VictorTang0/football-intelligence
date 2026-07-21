import json
import os
from datetime import datetime

def sync_evolution_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weights_path = os.path.join(base_dir, "data", "weights.json")
    evo_path = os.path.join(base_dir, "data", "model_evolution.json")
    history_path = os.path.join(base_dir, "data", "history.json")
    
    if not os.path.exists(evo_path) or not os.path.exists(weights_path):
        return
        
    with open(weights_path, "r", encoding="utf-8") as f:
        weights_db = json.load(f)

    with open(evo_path, "r", encoding="utf-8") as f:
        evo_db = json.load(f)

    history_acc = 0.5652
    total_validated = 46
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            h_db = json.load(f)
            history_acc = h_db.get("accuracy_rate", 0.5652)
            total_validated = h_db.get("total_predictions", 46)

    snapshots = evo_db.get("snapshots", [])
    if snapshots:
        latest_snapshot = snapshots[-1]
        latest_version = latest_snapshot.get("version", "v3.5")
        
        # Ensure snapshot accuracy matches history.json
        latest_snapshot["accuracy_after"] = history_acc
        latest_snapshot["matches_validated"] = total_validated
        
        # Sync weights.json version & stats
        weights_db["version"] = latest_version
        weights_db["total_matches_validated"] = total_validated
        weights_db["last_evolved"] = datetime.now().isoformat()
        
        # Sync evolution count
        evo_db["evolution_count"] = len(snapshots)
        
        with open(evo_path, "w", encoding="utf-8") as f:
            json.dump(evo_db, f, ensure_ascii=False, indent=2)

        with open(weights_path, "w", encoding="utf-8") as f:
            json.dump(weights_db, f, ensure_ascii=False, indent=2)
            
        print(f"🔄 [Sync Evolution] Synchronized version {latest_version} & stats ({total_validated} matches, {history_acc*100:.2f}% acc).")

    # Automatically evolve team tags based on updated match results
    try:
        import evolve_team_tags
        evolve_team_tags.evolve_team_tags()
    except Exception as e:
        print(f"Error running evolve_team_tags: {e}")

if __name__ == "__main__":
    sync_evolution_data()
