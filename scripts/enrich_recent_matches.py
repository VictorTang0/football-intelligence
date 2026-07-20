import json
import os
import random
from datetime import datetime, timedelta

def get_league_teams(league):
    # Standard team pools for realistic opponent generation
    pools = {
        "瑞超": ["马尔默", "佐加顿斯", "赫根", "埃夫斯堡", "哈马比", "天狼星", "盖斯", "索尔纳", "米亚尔比", "哥德堡", "布鲁马波", "卡尔马", "韦斯特罗斯", "哈尔姆斯", "代格福什"],
        "挪超": ["博德闪耀", "腓特烈", "莫尔德", "布兰", "维京", "特罗姆瑟", "萨普斯堡", "利勒斯特", "罗森博格", "奥斯陆", "桑德菲杰", "斯特罗姆", "哈姆卡", "克里斯蒂安"],
        "芬超": ["赫尔辛基", "瓦萨", "库普斯", "国际图尔库", "塞纳约基", "哈卡", "玛丽港", "拉赫蒂", "奥卢", "埃克纳斯", "格尼斯坦"],
        "巴甲": ["弗拉门戈", "帕尔梅拉斯", "博塔弗戈", "巴伊亚", "圣保罗", "米内罗竞技", "克鲁塞罗", "福塔雷萨", "巴拉纳竞技", "瓦斯科达伽马", "科林蒂安", "格雷米奥", "弗鲁米嫩", "布拉干RB", "维多利亚", "尤文图德"],
        "美职联": ["洛杉矶FC", "洛城银河", "迈阿密国际", "哥伦布机员", "皇家盐湖城", "辛辛那提", "纽约城", "夏洛特", "科罗拉多", "温哥华白帽", "波特兰战马", "西雅图海湾人", "明尼苏达联", "纳什维尔", "亚特联"]
    }
    return pools.get(league, ["赫尔辛基", "莫尔德", "马尔默", "哥德堡", "布兰", "瓦萨", "库普斯"])

def generate_recent_matches_for_team(team_name, form_list, league, kickoff_str):
    try:
        kickoff_dt = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
    except Exception:
        kickoff_dt = datetime.now()
        
    teams_pool = [t for t in get_league_teams(league) if t != team_name]
    if not teams_pool:
        teams_pool = ["对手A", "对手B", "对手C", "对手D"]
        
    recent_list = []
    
    # Deterministic generation seed based on team name
    seed_val = sum(ord(c) for c in team_name)
    random.seed(seed_val)
    
    # Sort dates backwards from kickoff
    days_back = 4
    for idx, outcome in enumerate(form_list):
        days_back += random.randint(4, 7)
        match_date = (kickoff_dt - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        opponent = random.choice(teams_pool)
        is_home = (idx % 2 == 0)
        
        # Determine scores based on outcome (W, D, L) for team_name
        if outcome == "W":
            our_g = random.choices([1, 2, 3, 4], weights=[0.4, 0.35, 0.2, 0.05])[0]
            opp_g = random.choice(list(range(our_g)))
        elif outcome == "L":
            opp_g = random.choices([1, 2, 3, 4], weights=[0.4, 0.35, 0.2, 0.05])[0]
            our_g = random.choice(list(range(opp_g)))
        else: # Draw
            our_g = random.choices([0, 1, 2, 3], weights=[0.2, 0.5, 0.2, 0.1])[0]
            opp_g = our_g
            
        our_ht = random.randint(0, our_g)
        opp_ht = random.randint(0, opp_g)
        
        home_team = team_name if is_home else opponent
        away_team = opponent if is_home else team_name
        
        home_score = our_g if is_home else opp_g
        away_score = opp_g if is_home else our_g
        
        home_ht = our_ht if is_home else opp_ht
        away_ht = opp_ht if is_home else our_ht
        
        score_str = f"{home_score}-{away_score}"
        half_score_str = f"{home_ht}-{away_ht}"
        
        recent_list.append({
            "date": match_date,
            "home": home_team,
            "away": away_team,
            "score": score_str,
            "half_score": half_score_str,
            "outcome": outcome # relative to team_name: W, D, L
        })
        
    return recent_list

def main():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "matches.json")
    if not os.path.exists(path):
        print("matches.json not found!")
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for m in data["matches"]:
        league = m.get("league", "瑞超")
        kickoff = m.get("kickoff", "2026-07-21T01:00:00+08:00")
        
        # Home team recent matches
        home_name = m["team_stats"]["home"]["name"]
        home_form = m["team_stats"]["home"].get("form", ["W", "D", "L", "W", "D"])
        m["team_stats"]["home"]["recent_matches"] = generate_recent_matches_for_team(home_name, home_form, league, kickoff)
        
        # Away team recent matches
        away_name = m["team_stats"]["away"]["name"]
        away_form = m["team_stats"]["away"].get("form", ["D", "L", "W", "D", "L"])
        m["team_stats"]["away"]["recent_matches"] = generate_recent_matches_for_team(away_name, away_form, league, kickoff)
        
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("🎉 Successfully generated detailed recent matches for all teams in matches.json!")

if __name__ == "__main__":
    main()
