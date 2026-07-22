import json
import os
import sys
import fetch_bonus as fb
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
    
    onsale_list = fb.fetch_on_sale_matches()
    print(f"Fetched {len(onsale_list)} currently on-sale matches from Sporttery.")
    
    added_count = 0
    for om in onsale_list:
        sm_id = str(om.get("matchId"))
        if sm_id in existing_sporttery_ids:
            continue
            
        home = om.get("home", "")
        away = om.get("away", "")
        league = om.get("league", "")
        match_num = om.get("matchNumStr", "")
        kickoff = om.get("kickoff", "")
        
        # Build match id string
        clean_date_str = kickoff.split(" ")[0].replace("-", "")[2:] if " " in kickoff else "260722"
        match_id_str = f"match_{clean_date_str}_{match_num}"
        
        print(f"➕ Adding new on-sale match: {match_num} {home} vs {away} (KO: {kickoff})...")
        raw_obj = {
            "id": match_id_str,
            "home": home,
            "away": away,
            "league": league,
            "kickoff": kickoff,
            "venue": f"{home}主场",
            "city": "体育场",
            "context": f"{league}官方对决。{home}坐镇主场迎接{away}的挑战。",
            "matchNumStr": match_num,
            "sportteryMatchId": sm_id
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
