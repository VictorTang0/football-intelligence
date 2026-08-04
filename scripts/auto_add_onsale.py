import json
import os
import sys
import fetch_sporttery_matches as fsm
import initialize_match as init_m

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")

def auto_add_all_onsale():
    if not os.path.exists(matches_path):
        print("matches.json not found!")
        return

    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)

    existing_matches = matches_db.get("matches", [])
    existing_sporttery_ids = {str(m.get("sportteryMatchId")) for m in existing_matches if m.get("sportteryMatchId")}
    
    api_data = fsm.fetch_sporttery_data()
    if not api_data:
        print("Failed to fetch official Sporttery matches.")
        return

    onsale_list, _ = fsm.process_matches(api_data)
    print(f"Fetched {len(onsale_list)} currently on-sale matches from Sporttery API.")
    
    added_count = 0
    for om in onsale_list:
        sm_id = str(om.get("sportteryMatchId"))
        if sm_id in existing_sporttery_ids:
            continue
            
        home = om.get("home", "")
        away = om.get("away", "")
        league = om.get("league", "")
        match_no = om.get("match_no", "")
        issue_date = om.get("issue_date", "")
        match_id = om.get("id", "")
        kickoff = om.get("kickoff", "")
        
        print(f"➕ Adding new on-sale match: {match_no} {home} vs {away} (Issue: {issue_date})...")
        raw_obj = {
            "id": match_id,
            "match_no": match_no,
            "issue_date": issue_date,
            "home": home,
            "away": away,
            "league": league,
            "kickoff": kickoff,
            "venue": f"{home}主场",
            "city": "体育场",
            "context": f"{league}官方对决。{home}坐镇主场迎接{away}的挑战。",
            "matchNumStr": match_no,
            "sportteryMatchId": sm_id,
            "handicap_line": om.get("handicap_line", "")
        }
        new_m = init_m.create_complete_match(raw_obj)
        existing_matches.append(new_m)
        existing_sporttery_ids.add(sm_id)
        added_count += 1

    if added_count > 0:
        matches_db["matches"] = existing_matches
        with open(matches_path, "w", encoding="utf-8") as f:
            json.dump(matches_db, f, ensure_ascii=False, indent=2)
        print(f"🎉 Successfully added {added_count} new on-sale matches to matches.json!")
    else:
        print("✅ All on-sale matches are already in matches.json.")

if __name__ == "__main__":
    auto_add_all_onsale()
