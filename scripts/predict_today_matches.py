# -*- coding: utf-8 -*-
import json
import os
import sys
from datetime import datetime

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(base_dir, "scripts"))

matches_path = os.path.join(base_dir, "data", "matches.json")

def main():
    try:
        import fetch_sporttery_matches
        fetch_sporttery_matches.main()
    except Exception as e:
        print(f"❌ Error running fetch_sporttery_matches: {e}")

    try:
        import initialize_match
        input_path = os.path.join(base_dir, "data", "new_matches_input.json")
        sys.argv = [sys.argv[0], input_path]
        initialize_match.main()
    except Exception as e:
        print(f"❌ Error running initialize_match: {e}")

    try:
        import update_odds_and_news
        sys.argv = [sys.argv[0], "--no-fetch"]
        update_odds_and_news.main()
    except Exception as e:
        print(f"❌ Error running update_odds_and_news: {e}")

    if not os.path.exists(matches_path):
        return

    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_matches = []
    locked_count = 0

    for m in matches_db.get("matches", []):
        st = m.get("status", "").lower()
        if st in ["pending", "waiting_result"]:
            kickoff_str = m.get("kickoff", "").split("T")[0].split(" ")[0]
            if kickoff_str >= today_str or st == "waiting_result":
                today_matches.append(m)
                if not m.get("baseline_recommendation"):
                    uc = m.get("ultimate_conclusion", {})
                    conc = m.get("conclusions", {})
                    m["baseline_recommendation"] = uc.get("recommendation", "--")
                    m["baseline_score"] = uc.get("predicted_score", "--")
                    m["baseline_goals"] = conc.get("over_under", "--")
                    m["prediction_trajectory"] = [{
                        "time": datetime.now().strftime("%H:%M"),
                        "val": uc.get("recommendation", "--").split("(")[0].strip()
                    }]
                    locked_count += 1

    if locked_count > 0:
        with open(matches_path, "w", encoding="utf-8") as f:
            json.dump(matches_db, f, ensure_ascii=False, indent=2)

    if today_matches:
        try:
            import push_service
            push_service.push_initial_predictions(today_matches)
        except Exception as e:
            print("❌ Error pushing initial predictions notification:", e)

    try:
        import subprocess
        subprocess.run(["git", "config", "user.name", "MATCH IQ Autopilot"], check=True)
        subprocess.run(["git", "config", "user.email", "autopilot@matchiq.com"], check=True)
        subprocess.run(["git", "add", "data/matches.json", "data/new_matches_input.json", "data/sporttery_odds.json", "data/sporttery_bonus.json"], check=True)
        subprocess.run(["git", "commit", "-m", "update: today matches predictions baseline lock"], check=True)
        subprocess.run(["git", "-c", "http.sslVerify=false", "pull", "origin", "main"], check=True)
        subprocess.run(["git", "-c", "http.sslVerify=false", "push", "origin", "main"], check=True)
    except Exception as e:
        print("❌ Error pushing baseline lock updates to GitHub:", e)

if __name__ == "__main__":
    main()
