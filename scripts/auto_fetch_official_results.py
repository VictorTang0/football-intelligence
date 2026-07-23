import json
import os
import ssl
import urllib.request
from datetime import datetime, timedelta

ctx = ssl._create_unverified_context()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sporttery.cn/",
    "Origin": "https://www.sporttery.cn",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

def fetch_official_results(start_date, end_date):
    url = (
        "https://webapi.sporttery.cn/gateway/uniform/football/getUniformMatchResultV1.qry"
        f"?matchBeginDate={start_date}&matchEndDate={end_date}"
        "&leagueId=&pageSize=100&pageNo=1&isFix=0&matchPage=1&pcOrWap=1"
    )
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("success"):
                return data.get("value", {}).get("matchResult", [])
    except Exception as e:
        print(f"Error fetching official results from Sporttery API: {e}")
    return []

def evaluate_match_prediction(m, ft_score, ht_score):
    try:
        h_goals, a_goals = map(int, ft_score.split(":"))
        h_goals_h, a_goals_h = map(int, ht_score.split(":")) if (ht_score and ":" in ht_score) else (0, 0)
    except Exception:
        return None

    home_team = m.get("home", "")
    away_team = m.get("away", "")
    actual_result_str = f"{home_team} {h_goals}-{a_goals} {away_team} ({h_goals_h}-{a_goals_h})"
    
    # Outcomes
    ft_outcome = "H" if h_goals > a_goals else "D" if h_goals == a_goals else "A"
    ht_outcome = "H" if h_goals_h > a_goals_h else "D" if h_goals_h == a_goals_h else "A"
    
    hafu_dict = {"H": "胜", "D": "平", "A": "负"}
    actual_hafu = f"{hafu_dict[ht_outcome]}{hafu_dict[ft_outcome]}"
    
    conclusions = m.get("conclusions", {})
    rec = m.get("ultimate_conclusion", {}).get("recommendation", "")
    
    # Recommendation correctness
    rec_correct = False
    if "主胜" in rec and ft_outcome == "H": rec_correct = True
    elif "客胜" in rec and ft_outcome == "A": rec_correct = True
    elif "平局" in rec and ft_outcome == "D": rec_correct = True
    elif "主不败" in rec and ft_outcome in ["H", "D"]: rec_correct = True
    elif "客不败" in rec and ft_outcome in ["A", "D"]: rec_correct = True
    elif "双选不败" in rec: rec_correct = True
    
    # Half-full correctness
    pred_hafu = conclusions.get("half_full", "")
    hafu_correct = actual_hafu in pred_hafu
    
    # Over-under correctness
    pred_ou = conclusions.get("over_under", "")
    is_over = (h_goals + a_goals) >= 2.5
    ou_correct = ("大" in pred_ou and is_over) or ("小" in pred_ou and not is_over)
    
    # Most likely score correctness
    pred_score = conclusions.get("most_likely_score", "")
    clean_score = f"{h_goals}-{a_goals}"
    clean_score_colon = f"{h_goals}:{a_goals}"
    score_correct = (clean_score in pred_score) or (clean_score_colon in pred_score)
    
    return {
        "actual_result": actual_result_str,
        "ft_score": ft_score,
        "ht_score": ht_score,
        "rec_correct": rec_correct,
        "hafu_correct": hafu_correct,
        "ou_correct": ou_correct,
        "score_correct": score_correct
    }

def main():
    print("🔄 Starting Automated Official Results Sync (Sporttery Source-of-Truth)...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    history_path = os.path.join(base_dir, "data", "history.json")
    
    # Query past 7 days results
    today = datetime.now()
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    official_list = fetch_official_results(start_date, end_date)
    print(f"Fetched {len(official_list)} official match results from Sporttery ({start_date} to {end_date}).")
    
    if not official_list:
        return
        
    official_map = {}
    for om in official_list:
        mid = om.get("matchId")
        if mid:
            official_map[str(mid)] = om
        # Also map by home+away
        h = om.get("homeTeam", "")
        a = om.get("awayTeam", "")
        if h and a:
            official_map[f"{h}_vs_{a}"] = om

    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)
        
    updated = False
    for m in matches_db.get("matches", []):
        sporttery_id = str(m.get("sportteryMatchId", ""))
        key = f"{m.get('home')}_vs_{m.get('away')}"
        
        om = official_map.get(sporttery_id) or official_map.get(key)
        if om and om.get("sectionsNo999") and ":" in om.get("sectionsNo999"):
            ft_score = om.get("sectionsNo999")
            ht_score = om.get("sectionsNo1", "")
            
            res = evaluate_match_prediction(m, ft_score, ht_score)
            if res:
                m["ultimate_conclusion"]["actual_result"] = res["actual_result"]
                m["result"] = res
                m["status"] = "finished"
                updated = True
                print(f"  Synced official result for {m.get('home')} vs {m.get('away')}: {res['actual_result']}")

    if updated:
        with open(matches_path, "w", encoding="utf-8") as f:
            json.dump(matches_db, f, ensure_ascii=False, indent=2)
        print("🎉 Successfully synced official results to matches.json!")

if __name__ == "__main__":
    main()
