import json
import os
import ssl
import time
import re
import urllib.request
from datetime import datetime, timedelta

ctx = ssl._create_unverified_context()

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sporttery.cn/",
    "Origin": "https://www.sporttery.cn",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bonus_path = os.path.join(base_dir, "data", "sporttery_bonus.json")

def fetch_official_results_batch(target_count=300):
    results = []
    page_size = 100
    
    # Query in 14-day windows backward from today
    curr_end = datetime.now()
    
    print(f"🌐 Fetching official match results from Sporttery API in 14-day sliding windows. Target: {target_count} matches...")

    while len(results) < target_count and curr_end > (datetime.now() - timedelta(days=120)):
        curr_start = curr_end - timedelta(days=14)
        s_str = curr_start.strftime("%Y-%m-%d")
        e_str = curr_end.strftime("%Y-%m-%d")
        
        page_no = 1
        while len(results) < target_count:
            url = (
                "https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry"
                f"?matchBeginDate={s_str}&matchEndDate={e_str}"
                f"&leagueId=&pageSize={page_size}&pageNo={page_no}&isFix=0&matchPage=1&pcOrWap=1"
            )
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    if data.get("success"):
                        val = data.get("value", {})
                        match_list = val.get("matchResult", [])
                        if not match_list:
                            break
                        results.extend(match_list)
                        print(f"  > Window {s_str} ~ {e_str} (p.{page_no}): +{len(match_list)} matches (Total: {len(results)})")
                        pages = val.get("pages", 1)
                        if page_no >= pages or len(results) >= target_count:
                            break
                        page_no += 1
                        time.sleep(0.1)
                    else:
                        break
            except Exception as e:
                print(f"❌ Error fetching window {s_str} ~ {e_str}: {e}")
                break
        
        curr_end = curr_start - timedelta(days=1)

    return results[:target_count]

def fetch_fixed_bonus_history(sporttery_match_id):
    url = f"https://webapi.sporttery.cn/gateway/uniform/football/getFixedBonusV1.qry?clientCode=3001&matchId={sporttery_match_id}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("success"):
                return data.get("value", {})
    except Exception:
        pass
    return {}

def run_300_fetch_and_merge():
    raw_bonus_db = {}
    if os.path.exists(bonus_path):
        try:
            with open(bonus_path, "r", encoding="utf-8") as f:
                raw_bonus_db = json.load(f)
        except Exception:
            raw_bonus_db = {}

    matches = fetch_official_results_batch(300)
    print(f"🎉 Successfully fetched {len(matches)} official finished matches!")

    added_count = 0
    updated_count = 0

    for idx, m in enumerate(matches):
        sp_id = str(m.get("matchId") or m.get("id"))
        if not sp_id or sp_id == "None":
            continue

        match_key = f"match_sp_{sp_id}"
        
        score_str = m.get("sectionsNo1") or ""
        match_full = re.search(r'(\d+)[:\-]\d+', score_str)
        
        had_res, hhad_res, crs_res, ttg_res, hafu_res = "", "", "", "", ""
        hc_line = -1
        try:
            hc_raw = m.get("hhad", {}).get("goalLine") or m.get("goalLine") or "-1"
            hc_line = int(hc_raw)
        except Exception: pass

        if match_full:
            parts = score_str.replace(":", "-").split()
            score_part = parts[0]
            hg, ag = map(int, score_part.split("-"))
            total_g = hg + ag
            had_res = "主胜" if hg > ag else "客胜" if ag > hg else "平局"
            crs_res = f"{hg}:{ag}"
            ttg_res = str(total_g)
            
            diff = hg - ag + hc_line
            hhad_res = "让胜" if diff > 0 else "让负" if diff < 0 else "让平"

            # Parse half score if present e.g. "1-1 (0-1)"
            if len(parts) > 1 and "(" in parts[1]:
                half_part = parts[1].replace("(", "").replace(")", "")
                if "-" in half_part:
                    hh, ha = map(int, half_part.split("-"))
                    ht_res = "胜" if hh > ha else "负" if ha > hh else "平"
                    ft_res = "胜" if hg > ag else "负" if ag > hg else "平"
                    hafu_res = f"{ht_res}{ft_res}"

        home_name = m.get("homeTeamAllName") or m.get("homeTeamAbbName") or ""
        away_name = m.get("awayTeamAllName") or m.get("awayTeamAbbName") or ""

        # Fetch Fixed Bonus Trajectory
        bonus_data = fetch_fixed_bonus_history(sp_id)
        time.sleep(0.05)

        entry = {
            "matchId": sp_id,
            "home": home_name,
            "away": away_name,
            "league": m.get("leagueAllName") or m.get("leagueAbbName") or "",
            "matchDate": m.get("matchDate") or m.get("date") or "",
            "handicap_line": f"{hc_line:+d}" if hc_line != 0 else "0",
            "official_outcomes": {
                "had": had_res,
                "hhad": hhad_res,
                "crs": crs_res,
                "ttg": ttg_res,
                "hafu": hafu_res,
                "score": score_str
            },
            "oddsHistory": bonus_data.get("oddsHistory", bonus_data)
        }

        if match_key not in raw_bonus_db:
            raw_bonus_db[match_key] = entry
            added_count += 1
        else:
            raw_bonus_db[match_key].update(entry)
            updated_count += 1

        if (idx + 1) % 50 == 0 or (idx + 1) == len(matches):
            print(f"  📈 Processed {idx + 1}/{len(matches)} matches fixed bonus trajectories & ground truths...")

    with open(bonus_path, "w", encoding="utf-8") as f:
        json.dump(raw_bonus_db, f, ensure_ascii=False, indent=2)

    print(f"✅ Finished! Dataset fully synchronized. Total dataset size: {len(raw_bonus_db)} matches.")

if __name__ == "__main__":
    run_300_fetch_and_merge()
