import json
import urllib.request
import ssl
import os
from datetime import datetime

def fetch_sporttery_data():
    url = "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry?category=3001&clientType=2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://m.sporttery.cn/",
        "Origin": "https://m.sporttery.cn"
    }
    
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    
    try:
        print("Fetching match data from Sporttery API...")
        with urllib.request.urlopen(req, timeout=15, context=ctx) as response:
            data = json.loads(response.read().decode("utf-8"))
            if not data.get("success", False):
                print(f"API Error: {data.get('errorMessage', 'Unknown error')}")
                return None
            return data
    except Exception as e:
        print(f"HTTP Error: {e}")
        return None

def process_matches(api_data):
    if not api_data or "value" not in api_data:
        return [], {}
        
    match_info_list = api_data["value"].get("matchInfoList", [])
    new_matches_input = []
    sporttery_odds = {}
    
    # Standard league mapping (matching our data/league_profiles.json keys)
    league_mapping = {
        "韩国职业联赛": "韩职",
        "挪威超级联赛": "挪超",
        "瑞典超级联赛": "瑞超",
        "芬兰超级联赛": "芬超",
        "世界杯": "世界杯",
        "美职大联盟": "美职",
        "巴西甲级联赛": "巴甲"
    }
    
    # We want to support all leagues, so if not in mapping, we fallback to leagueAbbName
    for group in match_info_list:
        sub_matches = group.get("subMatchList", [])
        # 竞彩官方开售期号/业务日期 (例如 "2026-07-28" -> "260728")
        bus_date = group.get("businessDate", group.get("businessDateStr", ""))
        bus_yymmdd = bus_date.replace("-", "")[2:] if bus_date else ""

        for m in sub_matches:
            # 1. League
            raw_league = m.get("leagueName", "")
            league_abbr = m.get("leagueAbbName", "")
            league = league_mapping.get(raw_league, league_abbr)
            
            # 2. Teams
            home = m.get("homeTeamAbbName", "")
            away = m.get("awayTeamAbbName", "")
            
            # 3. Kickoff Date & Time
            m_date = m.get("matchDate", "") # e.g. "2026-07-18"
            m_time = m.get("matchTime", "") # e.g. "21:00:00"
            if not m_date or not m_time:
                continue
                
            kickoff_iso = f"{m_date}T{m_time}+08:00"
            
            # 4. Unique ID formation based on official business date (issue_date)
            # e.g. "周二002" in "2026-07-28" issue -> match_260728_002
            yymmdd = bus_yymmdd if bus_yymmdd else m_date.replace("-", "")[2:]
            match_num_str = m.get("matchNumStr", "") # e.g. "周六108"
            num = "".join(filter(str.isdigit, match_num_str))
            if not num:
                continue
            num_padded = f"{int(num):03d}"
            mid = f"match_{yymmdd}_{num_padded}"
            
            # 5. Extract HAD (胜平负) Odds
            had = m.get("had", {})
            h_odds = float(had.get("h", 2.0)) if had.get("h") else 2.0
            d_odds = float(had.get("d", 3.0)) if had.get("d") else 3.0
            a_odds = float(had.get("a", 3.0)) if had.get("a") else 3.0
            
            # 6. Extract HHAD (让球胜平负) Line
            hhad = m.get("hhad", {})
            raw_gl = hhad.get("goalLine") or hhad.get("goalLineValue", "") # e.g. "-1" or "+1" or "-2"
            handicap_line = str(raw_gl).strip() if raw_gl else "-1"
            if handicap_line and not handicap_line.startswith("+") and not handicap_line.startswith("-"):
                try:
                    gl_num = int(handicap_line)
                    handicap_line = f"+{gl_num}" if gl_num > 0 else f"{gl_num}"
                except Exception:
                    pass
            
            # We construct a record for new_matches_input.json
            new_matches_input.append({
                "id": mid,
                "match_no": match_num_str,
                "issue_date": yymmdd,
                "sportteryMatchId": m.get("matchId"),
                "league": league,
                "home": home,
                "away": away,
                "kickoff": kickoff_iso,
                "initial_odds": {
                    "home": h_odds,
                    "draw": d_odds,
                    "away": a_odds
                },
                "handicap_line": handicap_line
            })
            
            # Record odds for sporttery_odds.json
            sporttery_odds[mid] = {
                "sportteryMatchId": m.get("matchId"),
                "home": h_odds,
                "draw": d_odds,
                "away": a_odds
            }
            
    return new_matches_input, sporttery_odds

def main():
    api_data = fetch_sporttery_data()
    if not api_data:
        print("Failed to fetch data from Sporttery.")
        return
        
    new_matches_input, sporttery_odds = process_matches(api_data)
    
    if not new_matches_input:
        print("No active matches parsed.")
        return
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "data", "new_matches_input.json")
    odds_path = os.path.join(base_dir, "data", "sporttery_odds.json")
    
    # Save input
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(new_matches_input, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(new_matches_input)} matches to {input_path}")
    
    # Save odds mapping
    with open(odds_path, "w", encoding="utf-8") as f:
        json.dump(sporttery_odds, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(sporttery_odds)} match odds mapping to {odds_path}")

if __name__ == "__main__":
    main()
