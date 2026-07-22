import json
import os
import ssl
import time
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
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)

def fetch_official_results(start_date, end_date):
    """Fetch official match results from Sporttery uniform API"""
    results = []
    page_no = 1
    page_size = 100
    while True:
        url = (
            "https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry"
            f"?matchBeginDate={start_date}&matchEndDate={end_date}"
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
                    pages = val.get("pages", 1)
                    if page_no >= pages:
                        break
                    page_no += 1
                    time.sleep(0.1)
                else:
                    break
        except Exception as e:
            print(f"Error fetching official results ({start_date} ~ {end_date}, p.{page_no}): {e}")
            break
    return results

def fetch_fixed_bonus_history(sporttery_match_id):
    """Fetch complete fixed bonus update trajectory for a matchId"""
    url = f"https://webapi.sporttery.cn/gateway/uniform/football/getFixedBonusV1.qry?clientCode=3001&matchId={sporttery_match_id}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("success"):
                return data.get("value", {})
    except Exception as e:
        pass
    return {}

def process_and_structure_matches(raw_matches):
    structured = []
    print(f"Processing and structuring {len(raw_matches)} raw match records...")
    
    for idx, om in enumerate(raw_matches):
        match_id = str(om.get("matchId", ""))
        home = om.get("homeTeam", "") or om.get("homeTeamAllName", "")
        away = om.get("awayTeam", "") or om.get("awayTeamAllName", "")
        league = om.get("leagueAllName", "") or om.get("leagueName", "")
        mdate = om.get("matchDate", "") or om.get("businessDate", "")
        mtime = om.get("matchTime", "")
        ft_score = om.get("sectionsNo999", "")
        ht_score = om.get("sectionsNo1", "")
        
        if not ft_score or ":" not in ft_score:
            continue
            
        # Parse scores
        try:
            h_g, a_g = map(int, ft_score.split(":"))
            h_gh, a_gh = map(int, ht_score.split(":")) if (ht_score and ":" in ht_score) else (0, 0)
        except Exception:
            continue

        # Fetch detailed bonus trajectories if matchId exists
        bonus_data = {}
        if match_id:
            bonus_data = fetch_fixed_bonus_history(match_id)
            
        # Category 1: Match Preview (赛事前瞻)
        preview = {
            "feature_analysis": {
                "league": league,
                "is_cup_or_qualifier": any(x in league for x in ["杯", "资格赛", "欧冠", "欧联", "世界杯"]),
                "home_advantage_tier": "强" if any(x in home for x in ["弗拉门戈", "首尔", "马尔默", "蔚山", "博德"]) else "中"
            },
            "history_head_to_head": {
                "description": f"近 5 次交手 (开赛时间越旧衰减权重越大)",
                "time_decay_alpha": 0.85,
                "notes": "最近交手权重 1.0, 逐场按 0.85 指数衰减"
            },
            "league_standings_evolution": {
                "description": "随着联赛发展的变动积分榜与排名战意",
                "home_standing_snapshot": om.get("homeRank", "中游"),
                "away_standing_snapshot": om.get("awayRank", "中游")
            },
            "recent_form": {
                "description": "近 6 场比赛战绩 (时间越旧衰减权重越大)",
                "time_decay_alpha": 0.90
            },
            "scorer_stats": {
                "home_scorers": f"{home}主力攻击群",
                "away_scorers": f"{away}主力攻击群"
            }
        }
        
        # Category 2: Fixed Bonus Trajectory (固定奖金)
        odds_history = {
            "had": bonus_data.get("oddsHistory", {}).get("hadList", []),
            "hhad": bonus_data.get("oddsHistory", {}).get("hhadList", []),
            "crs": bonus_data.get("oddsHistory", {}).get("crsList", []),
            "ttg": bonus_data.get("oddsHistory", {}).get("ttgList", []),
            "hafu": bonus_data.get("oddsHistory", {}).get("hafuList", [])
        }
        
        item = {
            "matchId": match_id,
            "matchNumStr": om.get("matchNumStr", ""),
            "league": league,
            "home": home,
            "away": away,
            "matchDate": mdate,
            "matchTime": mtime,
            "fullTimeScore": ft_score,
            "halfTimeScore": ht_score,
            "ft_outcome": "H" if h_g > a_g else "D" if h_g == a_g else "A",
            "ht_outcome": "H" if h_gh > a_gh else "D" if h_gh == a_gh else "A",
            "total_goals": h_g + a_g,
            "is_over_2_5": (h_g + a_g) >= 2.5,
            "preview": preview,
            "odds_trajectory": odds_history
        }
        structured.append(item)
        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{len(raw_matches)} matches...")
            
    return structured

def main():
    print("🚀 Fetching historical Sporttery datasets...")
    
    # 1. Fetch December 2025 Validation Set (2025-12-01 to 2025-12-31)
    print("\n--- Phase 1: Fetching December 2025 Backtest Dataset ---")
    val_raw = fetch_official_results("2025-12-01", "2025-12-31")
    print(f"Fetched {len(val_raw)} raw matches for Dec 2025.")
    val_structured = process_and_structure_matches(val_raw)
    
    val_path = os.path.join(data_dir, "historical_val_202512.json")
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_structured, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(val_structured)} Dec 2025 structured matches to {val_path}")
    
    # 2. Fetch 2026 Training Set (2026-01-01 to 2026-07-22)
    print("\n--- Phase 2: Fetching 2026 Training Dataset (2026-01-01 to 2026-07-22) ---")
    chunks = [
        ("2026-01-01", "2026-02-28"),
        ("2026-03-01", "2026-04-30"),
        ("2026-05-01", "2026-06-30"),
        ("2026-07-01", "2026-07-22")
    ]
    train_raw_all = []
    for s_date, e_date in chunks:
        print(f" Fetching range: {s_date} ~ {e_date}...")
        raw_chunk = fetch_official_results(s_date, e_date)
        print(f"   -> Fetched {len(raw_chunk)} matches.")
        train_raw_all.extend(raw_chunk)
        
    print(f"Total raw training matches fetched: {len(train_raw_all)}")
    train_structured = process_and_structure_matches(train_raw_all)
    
    train_path = os.path.join(data_dir, "historical_train_2026.json")
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_structured, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(train_structured)} 2026 structured matches to {train_path}")

if __name__ == "__main__":
    main()
