import json
import os
import re

def swap_score_str(score_str):
    match = re.match(r'(\d+)\s*[:|-]\s*(\d+)', score_str)
    if match:
        g1, g2 = match.groups()
        return f"{g2}-{g1}"
    return score_str

def repair_records(records):
    repaired_count = 0
    for m in records:
        outcome = m.get("outcome", "D")
        score = m.get("score", "")
        half_score = m.get("half_score", "")
        
        score_match = re.match(r'(\d+)\s*[:|-]\s*(\d+)', score)
        if not score_match:
            continue
            
        g_home, g_away = map(int, score_match.groups())
        
        # Scenario 1: Outcome is 'A' (Away Win) but home score is higher than away score
        if outcome == "A" and g_home > g_away:
            m["score"] = swap_score_str(score)
            if half_score:
                m["half_score"] = swap_score_str(half_score)
            repaired_count += 1
            print(f"  [Repaired A] {m.get('date')} {m.get('home')} vs {m.get('away')}: {score} ({half_score}) -> {m['score']} ({m.get('half_score')})")
            
        # Scenario 2: Outcome is 'H' (Home Win) but away score is higher than home score
        elif outcome == "H" and g_home < g_away:
            m["score"] = swap_score_str(score)
            if half_score:
                m["half_score"] = swap_score_str(half_score)
            repaired_count += 1
            print(f"  [Repaired H] {m.get('date')} {m.get('home')} vs {m.get('away')}: {score} ({half_score}) -> {m['score']} ({m.get('half_score')})")
            
    return repaired_count

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    
    if not os.path.exists(matches_path):
        print("matches.json not found!")
        return
        
    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)
        
    total_repaired = 0
    for m in matches_db["matches"]:
        # Fix both 'h2h' and 'head_to_head'
        for key in ["h2h", "head_to_head"]:
            if key in m and "last_5" in m[key]:
                total_repaired += repair_records(m[key]["last_5"])
                
    if total_repaired > 0:
        with open(matches_path, "w", encoding="utf-8") as f:
            json.dump(matches_db, f, ensure_ascii=False, indent=2)
        print(f"🎉 Successfully repaired {total_repaired} H2H score records in matches.json!")
    else:
        print("✨ All H2H scores are already consistent with their outcomes!")

if __name__ == "__main__":
    main()
