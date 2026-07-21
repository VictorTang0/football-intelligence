import json
import urllib.request
import ssl
import time
import os
from datetime import datetime

ctx = ssl._create_unverified_context()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sporttery.cn/",
    "Origin": "https://www.sporttery.cn",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

def get_bonus(sporttery_match_id):
    url = f"https://webapi.sporttery.cn/gateway/uniform/football/getFixedBonusV1.qry?clientCode=3001&matchId={sporttery_match_id}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("success"):
                return data.get("value", {})
    except Exception as e:
        print(f"Error fetching bonus for match {sporttery_match_id}: {e}")
    return None

def main():
    print("🔄 Starting Sporttery Detailed Fixed Bonus Scraper...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    bonus_path = os.path.join(base_dir, "data", "sporttery_bonus.json")
    
    if not os.path.exists(matches_path):
        print(f"matches.json not found at {matches_path}")
        return
        
    with open(matches_path, "r", encoding="utf-8") as f:
        database = json.load(f)
        
    pending_matches = [m for m in database.get("matches", []) if m.get("status") in ["pending", "postponed"]]
    print(f"Found {len(pending_matches)} active/pending matches in database.")
    
    # Load existing bonus map to merge
    bonus_map = {}
    if os.path.exists(bonus_path):
        try:
            with open(bonus_path, "r", encoding="utf-8") as f:
                bonus_map = json.load(f)
        except Exception as e:
            print("Error loading existing sporttery_bonus.json:", e)
            
    updated_count = 0
    for m in pending_matches:
        mid = m.get("id")
        sporttery_id = m.get("sportteryMatchId")
        
        if not sporttery_id:
            print(f"No sportteryMatchId for {m.get('home')} vs {m.get('away')} ({mid})")
            continue
            
        print(f"Fetching bonus history for {m.get('home')} vs {m.get('away')} (Sporttery ID: {sporttery_id})...")
        bonus_data = get_bonus(sporttery_id)
        if bonus_data:
            bonus_map[mid] = {
                "matchId": sporttery_id,
                "home": m.get("home"),
                "away": m.get("away"),
                "oddsHistory": bonus_data.get("oddsHistory", {}),
                "last_update": datetime.now().isoformat()
            }
            updated_count += 1
            print(f"  Successfully saved detailed odds history for {mid}.")
            time.sleep(0.5)
            
    if updated_count > 0 or not os.path.exists(bonus_path):
        with open(bonus_path, "w", encoding="utf-8") as f:
            json.dump(bonus_map, f, ensure_ascii=False, indent=2)
        print(f"🎉 Saved detailed bonus data for {updated_count} matches to {bonus_path}")
    else:
        print("No bonus data was updated.")

if __name__ == "__main__":
    main()
