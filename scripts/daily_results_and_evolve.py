# -*- coding: utf-8 -*-
import json
import os
import sys
from datetime import datetime, timedelta

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "scripts"))

matches_path = os.path.join(base_dir, "data", "matches.json")
history_path = os.path.join(base_dir, "data", "history.json")
weights_path = os.path.join(base_dir, "data", "weights.json")
evo_path = os.path.join(base_dir, "data", "model_evolution.json")

def main():
    print("🔄 Starting daily results update & model evolution workflow...")
    
    if not os.path.exists(matches_path):
        print("❌ Error: matches.json not found!")
        return

    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    pending_yesterday_or_earlier = []
    for m in matches_db.get("matches", []):
        st = m.get("status", "").lower()
        if st in ["pending", "waiting_result"]:
            kickoff_str = m.get("kickoff", "").split("T")[0].split(" ")[0]
            if kickoff_str < today_str:
                pending_yesterday_or_earlier.append(m)

    if not pending_yesterday_or_earlier:
        print("✅ No pending matches from yesterday or earlier. Today's settlement is already complete.")
        return

    print(f"📋 Found {len(pending_yesterday_or_earlier)} pending/waiting_result matches from yesterday or earlier.")

    try:
        import auto_fetch_official_results
        auto_fetch_official_results.main()
    except Exception as e:
        print(f"❌ Error running auto_fetch_official_results: {e}")

    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)

    still_pending = []
    for m in matches_db.get("matches", []):
        st = m.get("status", "").lower()
        if st in ["pending", "waiting_result"]:
            kickoff_str = m.get("kickoff", "").split("T")[0].split(" ")[0]
            if kickoff_str < today_str:
                still_pending.append(m)

    if still_pending:
        print(f"⏳ Still waiting for {len(still_pending)} matches to be officially synced.")
        return

    print("🎉 All yesterday matches have been officially closed! Evolving weights...")
    newly_settled_ids = [m["id"] for m in pending_yesterday_or_earlier]
    
    try:
        import sync_evolution
        sync_evolution.sync_evolution_data()
    except Exception as e:
        print(f"❌ Error running sync_evolution: {e}")

    with open(history_path, "r", encoding="utf-8") as f:
        history_db = json.load(f)
    
    with open(evo_path, "r", encoding="utf-8") as f:
        evo_db = json.load(f)

    settled_records = []
    for r in history_db.get("records", []):
        if r["match_id"] in newly_settled_ids:
            settled_records.append({
                "match_no": r.get("match_id").split("_")[-1],
                "home": r.get("home"),
                "away": r.get("away"),
                "recommendation": r.get("predictions", {}).get("recommendation", {}).get("val", "--"),
                "score": r.get("predictions", {}).get("most_likely_score", {}).get("val", "--"),
                "is_correct": r.get("is_correct", False),
                "actual_result": r.get("actual_result", "")
            })

    evo_stats = {
        "version": evo_db.get("current_version", "v4.0"),
        "direction_accuracy": history_db.get("accuracy_rate", 0.0),
        "score_accuracy": history_db.get("score_accuracy_rate", 0.0),
        "total_validated_matches": history_db.get("total_predictions", 0)
    }

    try:
        import push_service
        push_service.push_daily_results(settled_records, evo_stats)
    except Exception as e:
        print("❌ Error pushing daily results notification:", e)

    try:
        import subprocess
        subprocess.run(["git", "config", "user.name", "MATCH IQ Autopilot"], check=True)
        subprocess.run(["git", "config", "user.email", "autopilot@matchiq.com"], check=True)
        subprocess.run(["git", "add", "data/matches.json", "data/history.json", "data/model_evolution.json", "data/weights.json", "data/team_tags.json"], check=True)
        subprocess.run(["git", "commit", "-m", f"update: daily results sync and model evolution {evo_stats['version']}"], check=True)
        subprocess.run(["git", "-c", "http.sslVerify=false", "pull", "origin", "main"], check=True)
        subprocess.run(["git", "-c", "http.sslVerify=false", "push", "origin", "main"], check=True)
    except Exception as e:
        print("❌ Error pushing daily updates to GitHub:", e)

if __name__ == "__main__":
    main()
