# -*- coding: utf-8 -*-
import os
import sys
import json
import subprocess
from datetime import datetime, timezone, timedelta

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

def get_beijing_time():
    bj_tz = timezone(timedelta(hours=8))
    return datetime.now(bj_tz)

def is_market_open(now_bj):
    """
    竞彩官方硬性停售与开售交易时间守卫:
    - 周一至周五 (Weekday 0~4): 11:00 开售 ~ 22:00 停售
    - 周六至周日 (Weekday 5~6): 11:00 开售 ~ 23:00 停售
    在停售时间段 (周一~五 22:00~11:00 / 周六日 23:00~11:00) 引擎切断盘口更新与所有消息推送!
    """
    weekday = now_bj.weekday() # 0 = Monday, ..., 6 = Sunday
    hour = now_bj.hour
    minute = now_bj.minute
    
    is_weekend = (weekday in [5, 6])
    cutoff_hour = 23 if is_weekend else 22
    
    # 早上 11:00 之前未开售
    if hour < 11:
        return False, f"未到开售时间 (每日 11:00 开售)"
    
    # 达到或超越停售时间
    if hour >= cutoff_hour:
        day_str = "周六日" if is_weekend else "周一至五"
        return False, f"竞彩官方已停售 (中国时间 {day_str} 固定 {cutoff_hour}:00 封盘停售)"
        
    return True, "竞彩交易期内"

def main():
    now_bj = get_beijing_time()
    
    hour = now_bj.hour
    weekday = now_bj.weekday()
    today_str = now_bj.strftime("%Y-%m-%d")
    
    print(f"⏰ MATCH IQ Autopilot Orchestrator triggered at Beijing Time: {now_bj.strftime('%Y-%m-%d %H:%M:%S')} (Weekday: {weekday})")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(base_dir, "scripts")
    state_path = os.path.join(base_dir, "data", "scheduler_state.json")
    state = load_state(state_path)

    # 0. Check Market Open Guard
    open_status, reason = is_market_open(now_bj)
    if not open_status and "--force" not in sys.argv:
        print(f"🔒 [Market Shutdown] {reason}。巡航系统自动进入【终盘深度休眠】，暂停盘口抓取与消息推送。")
        return

    # 1. Check for Active Pending Matches
    matches_file = os.path.join(base_dir, "data", "matches.json")
    if os.path.exists(matches_file):
        try:
            with open(matches_file, "r", encoding="utf-8") as f:
                matches_db = json.load(f)
            pending_count = len([m for m in matches_db.get("matches", []) if m.get("status") == "pending" and not m.get("is_finished")])
            if pending_count == 0 and "--force" not in sys.argv:
                print(f"🔒 [No Pending Matches] 当前无可分析的在售比赛。巡航休眠断流。")
                return
        except Exception as e:
            print(f"Warning checking pending matches: {e}")

    # 2. Daily initial prediction check (Runs once per day after 11:00 AM)
    if hour >= 11 and state.get("last_initial_prediction_date") != today_str:
        print(f"☀️ [State-Lock Run] Triggering Daily Results Settlement & Initial Predictions for {today_str}...")
        try:
            subprocess.run([sys.executable, os.path.join(scripts_dir, "daily_results_and_evolve.py")], check=True)
            subprocess.run([sys.executable, os.path.join(scripts_dir, "predict_today_matches.py")], check=True)
            state["last_initial_prediction_date"] = today_str
            save_state(state_path, state)
        except Exception as e:
            print(f"❌ Error during daily initial run: {e}")

    # 3. REAL odds update & M10 pure deduction
    print(f"🔍 Running real-time live odds update & pure M10 deduction...")
    try:
        subprocess.run([sys.executable, os.path.join(scripts_dir, "update_odds_and_news.py")], check=True)
        subprocess.run([sys.executable, os.path.join(scripts_dir, "generate_pure_m10_conclusions.py")], check=True)
        subprocess.run([sys.executable, os.path.join(scripts_dir, "sync_history.py")], check=True)
    except Exception as e:
        print(f"❌ Error during odds update pipeline: {e}")

    # 4. ALWAYS execute self-healing Git Sync to GitHub Pages
    print(f"🚀 Triggering self-healing Auto Git Sync to GitHub Pages...")
    try:
        subprocess.run([sys.executable, os.path.join(scripts_dir, "auto_git_sync.py")], check=True)
    except Exception as e:
        print(f"❌ Error during auto_git_sync: {e}")

if __name__ == "__main__":
    main()
