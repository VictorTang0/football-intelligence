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
    # If time is past 11:00 AM and initial predictions for today have not been sent yet -> RUN IMMEDIATELY!
    if hour >= 11 and state.get("last_initial_prediction_date") != today_str:
        print(f"☀️ [State-Lock Run] Triggering Daily Results Settlement & Initial Predictions for {today_str}...")
        try:
            subprocess.run(["python", os.path.join(scripts_dir, "daily_results_and_evolve.py")], check=True)
            subprocess.run(["python", os.path.join(scripts_dir, "predict_today_matches.py")], check=True)
            state["last_initial_prediction_date"] = today_str
            save_state(state_path, state)
        except Exception as e:
            print(f"❌ Error during 11:00 daily run: {e}")
        return

    # Determine monitoring boundaries
    end_hour = 22 if is_weekend else 21
    end_min = 30

    # Outside active monitoring window
    if hour < 11 or hour > end_hour or (hour == end_hour and minute > end_min + 15):
        print("💤 Outside active monitoring window. Sleeping.")
        return

    # 2. Check Pre-Final countdown slot (Workday 21:00 / Weekend 22:00)
    pre_final_target_hour = end_hour - 1
    if hour >= pre_final_target_hour and state.get("last_pre_final_date") != today_str:
        print(f"⏳ [State-Lock Run] Triggering Pre-Final countdown summary push for {today_str}...")
        try:
            subprocess.run(["python", os.path.join(scripts_dir, "update_odds_and_news.py"), "--pre-final"], check=True)
            state["last_pre_final_date"] = today_str
            save_state(state_path, state)
        except Exception as e:
            print(f"❌ Error during Pre-Final run: {e}")
        return

    # 3. Check Final closing slot (Workday 21:30 / Weekend 22:30)
    if (hour > end_hour or (hour == end_hour and minute >= 25)) and state.get("last_final_date") != today_str:
        print(f"🏁 [State-Lock Run] Triggering Final closing summary push for {today_str}...")
        try:
            subprocess.run(["python", os.path.join(scripts_dir, "update_odds_and_news.py"), "--final"], check=True)
            state["last_final_date"] = today_str
            save_state(state_path, state)
        except Exception as e:
            print(f"❌ Error during Final run: {e}")
        return

    # 4. Hourly & High-frequency live odds check
    print(f"🔍 Running live odds and news check for slot {hour}:{minute:02d}...")
    try:
        subprocess.run(["python", os.path.join(scripts_dir, "update_odds_and_news.py")], check=True)
    except Exception as e:
        print(f"❌ Error during update_odds_and_news: {e}")

if __name__ == "__main__":
    main()
