import json
import os
import copy
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m10_weights_path = os.path.join(base_dir, "data", "m10_weights.json")
bonus_path = os.path.join(base_dir, "data", "sporttery_bonus.json")

def evolve_m10_weights_online():
    """
    Runs automated online incremental gradient evolution on M10 hyperparameter thresholds
    """
    if not os.path.exists(m10_weights_path) or not os.path.exists(bonus_path):
        return

    try:
        import train_m10
        with open(bonus_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

        with open(m10_weights_path, "r", encoding="utf-8") as f:
            m10_weights_db = json.load(f)

        prev_stats = copy.deepcopy(m10_weights_db.get("accuracy_stats", {}))
        
        # Run incremental optimization
        train_m10.train_m10_model()

        with open(m10_weights_path, "r", encoding="utf-8") as f:
            new_db = json.load(f)
            
        new_stats = new_db.get("accuracy_stats", {})
        print(f"🧠 [M10 Incremental Evolution Complete] Dataset Size: {len(dataset)} | HAD: {new_stats.get('had')} | HHAD: {new_stats.get('hhad')} | Goals: {new_stats.get('goals')}")

    except Exception as e:
        print(f"Error running evolve_m10_weights_online: {e}")

if __name__ == "__main__":
    evolve_m10_weights_online()
