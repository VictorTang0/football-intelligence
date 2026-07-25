# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess
from datetime import datetime
import pytz

def load_state(state_path):
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state_path, state):
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save scheduler_state.json: {e}")

def main():
    bj_tz = pytz.timezone("Asia/Shanghai")
    now_bj = datetime.now(bj_tz)
    
    hour = now_bj.hour
    minute = now_bj.minute
    weekday = now_bj.weekday() # 0 = Monday, ..., 6 = Sunday
    is_weekend = (weekday in [5, 6])
    today_str = now_bj.strftime("%Y-%m-%d")
    
    print(f"⏰ MATCH IQ Orchestrator triggered at Beijing Time: {now_bj.strftime('%Y-%m-%d %H:%M:%S')} (Weekday: {weekday})")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(base_dir, "scripts")
    state_path = os.path.join(base_dir, "data", "scheduler_state.json")

    state = load_state(state_path)

    # 0. Manual/Forced Push Trigger
    if "--force-push" in sys.argv:
        print("📢 [Manual Trigger] Running live update and pushing current predictions summary table to phone...")
        try:
            subprocess.run(["python", os.path.join(scripts_dir, "update_odds_and_news.py")], check=True)
            with open(os.path.join(base_dir, "data", "matches.json"), "r", encoding="utf-8") as f:
                matches_db = json.load(f)
            today_matches = [m for m in matches_db.get("matches", []) if m.get("status") == "pending"]
            import push_service
            push_service.push_initial_predictions(today_matches)
            print("✅ Manual summary table push completed successfully!")
        except Exception as e:
            print(f"❌ Error during manual push: {e}")
        return
    # 1. Daily initial prediction check (Runs once per day after 11:00 AM)
    if hour >= 11 and state.get("last_initial_prediction_date") != today_str:
        print(f"☀️ [State-Lock Run] Triggering Daily Results Settlement & Initial Predictions for {today_str}...")
        try:
            subprocess.run(["python", os.path.join(scripts_dir, "daily_results_and_evolve.py")], check=True)
            subprocess.run(["python", os.path.join(scripts_dir, "predict_today_matches.py")], check=True)
            state["last_initial_prediction_date"] = today_str
            save_state(state_path, state)
        except Exception as e:
            print(f"❌ Error during 11:00 daily run: {e}")

    # 2. ALWAYS execute live odds update & push notification
    print(f"🔍 Running live odds check & PushPlus notification trigger for slot {hour}:{minute:02d}...")
    try:
        subprocess.run(["python", os.path.join(scripts_dir, "update_odds_and_news.py")], check=True)
    except Exception as e:
        print(f"❌ Error during update_odds_and_news: {e}")

if __name__ == "__main__":
    main()
