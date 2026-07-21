import json
import urllib.request
import ssl
import time
import os
from datetime import datetime

ctx = ssl._create_unverified_context()

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sporttery.cn/jc/zqszsc/",
    "Origin": "https://www.sporttery.cn",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

def fetch_on_sale_matches():
    """Fetch currently on-sale matches from Sporttery (https://www.sporttery.cn/jc/zqszsc/)"""
    url = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001"
    req = urllib.request.Request(url, headers=headers)
    on_sale_matches = []
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get("success"):
                match_info_list = data.get("value", {}).get("matchInfoList", [])
                for item in match_info_list:
                    sub_list = item.get("subMatchList", [])
                    for m in sub_list:
                        sell_status = str(m.get("sellStatus", ""))
                        pool_list = m.get("poolList", [])
                        if sell_status != "1" or len(pool_list) <= 1:
                            continue
                            
                        bdate = m.get("businessDate", "")
                        mtime = m.get("matchTime", "")
                        kickoff = f"{bdate} {mtime}" if bdate and mtime else mtime
                        
                        on_sale_matches.append({
                            "matchId": str(m.get("matchId")),
                            "home": m.get("homeTeamAllName") or m.get("homeTeamAbbName"),
                            "away": m.get("awayTeamAllName") or m.get("awayTeamAbbName"),
                            "matchNumStr": m.get("matchNumStr"),
                            "league": m.get("leagueAllName") or m.get("leagueAbbName"),
                            "kickoff": kickoff
                        })
    except Exception as e:
        print(f"Error fetching on-sale matches from https://www.sporttery.cn/jc/zqszsc/: {e}")
    return on_sale_matches

def get_bonus_history(sporttery_match_id):
    """Fetch fixed bonus history for a given Sporttery matchId"""
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

def compare_and_detect_odds_updates(old_history, new_history):
    """
    Compare new oddsHistory against old stored oddsHistory.
    Detects any newly added entries or water changes in hadList/hhadList.
    Returns: (has_updates, list_of_detected_changes)
    """
    changes = []
    if not old_history:
        return True, ["初始盘口数据加载"]

    # 1. Compare HAD (胜平负) history
    old_had = old_history.get("hadList", [])
    new_had = new_history.get("hadList", [])
    
    old_had_keys = {f"{item.get('updateDate')} {item.get('updateTime')}" for item in old_had}
    for item in new_had:
        key = f"{item.get('updateDate')} {item.get('updateTime')}"
        if key not in old_had_keys:
            h = item.get("h", "-")
            d = item.get("d", "-")
            a = item.get("a", "-")
            changes.append(f"【胜平负变盘】[{key}] 主胜:{h} 平局:{d} 客胜:{a}")

    # 2. Compare HHAD (让球胜平负) history
    old_hhad = old_history.get("hhadList", [])
    new_hhad = new_history.get("hhadList", [])
    
    old_hhad_keys = {f"{item.get('updateDate')} {item.get('updateTime')}" for item in old_hhad}
    for item in new_hhad:
        key = f"{item.get('updateDate')} {item.get('updateTime')}"
        if key not in old_hhad_keys:
            line = item.get("goalLine", "")
            h = item.get("h", "-")
            d = item.get("d", "-")
            a = item.get("a", "-")
            changes.append(f"【让球变盘({line})】[{key}] 让胜:{h} 让平:{d} 让负:{a}")

    return (len(changes) > 0), changes

def main():
    print("🔄 Starting Sporttery Real-time Odds & Water Monitor (Source: https://www.sporttery.cn/jc/zqszsc/)...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    bonus_path = os.path.join(base_dir, "data", "sporttery_bonus.json")
    odds_path = os.path.join(base_dir, "data", "sporttery_odds.json")

    # 1. Fetch currently on-sale matches from www.sporttery.cn/jc/zqszsc/
    on_sale_list = fetch_on_sale_matches()
    print(f"✅ Fetched {len(on_sale_list)} currently on-sale matches from Sporttery official portal.")

    # Load existing bonus map
    bonus_map = {}
    if os.path.exists(bonus_path):
        try:
            with open(bonus_path, "r", encoding="utf-8") as f:
                bonus_map = json.load(f)
        except Exception as e:
            print("Error loading existing sporttery_bonus.json:", e)

    # Load existing matches database
    database = {"matches": []}
    if os.path.exists(matches_path):
        with open(matches_path, "r", encoding="utf-8") as f:
            database = json.load(f)

    match_by_sporttery_id = {}
    for m in database.get("matches", []):
        sid = str(m.get("sportteryMatchId", ""))
        if sid:
            match_by_sporttery_id[sid] = m

    total_detected_changes = 0
    updated_matches_count = 0

    # 2. Iterate through each on-sale match, fetch fixed bonus, compare with previous history
    for sale_m in on_sale_list:
        sid = sale_m["matchId"]
        home = sale_m["home"]
        away = sale_m["away"]

        # Find local match ID if exists
        local_m = match_by_sporttery_id.get(sid)
        local_id = local_m["id"] if local_m else f"match_sporttery_{sid}"

        old_entry = bonus_map.get(local_id, {})
        old_odds_history = old_entry.get("oddsHistory", {})

        bonus_data = get_bonus_history(sid)
        if not bonus_data:
            continue

        new_odds_history = bonus_data.get("oddsHistory", {})
        has_new_changes, change_logs = compare_and_detect_odds_updates(old_odds_history, new_odds_history)

        if has_new_changes:
            total_detected_changes += len(change_logs)
            updated_matches_count += 1
            print(f"\n⚡ [盘口水温更新识别] {home} vs {away} (Sporttery ID: {sid}):")
            for log in change_logs[:5]:
                print(f"   -> {log}")

        # Update bonus map entry
        bonus_map[local_id] = {
            "matchId": sid,
            "home": home,
            "away": away,
            "oddsHistory": new_odds_history,
            "last_update": datetime.now().isoformat(),
            "has_new_updates": has_new_changes,
            "recent_change_logs": change_logs
        }
        time.sleep(0.3)

    # 3. Save updated bonus history to sporttery_bonus.json
    with open(bonus_path, "w", encoding="utf-8") as f:
        json.dump(bonus_map, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 Completed Sporttery Odds Traversal! Detected {total_detected_changes} new odds changes across {updated_matches_count} matches.")
    print(f"💾 Saved detailed bonus history to {bonus_path}")

if __name__ == "__main__":
    main()
