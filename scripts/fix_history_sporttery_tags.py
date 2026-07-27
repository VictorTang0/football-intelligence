import json
import os
import re

def fix_history_sporttery():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    history_path = os.path.join(base_dir, "data", "history.json")

    if not os.path.exists(matches_path) or not os.path.exists(history_path):
        return

    with open(matches_path, "r", encoding="utf-8") as f:
        matches_db = json.load(f)

    with open(history_path, "r", encoding="utf-8") as f:
        history_db = json.load(f)

    matches_map = {}
    for m in matches_db.get("matches", []):
        mid = m.get("id")
        if mid:
            matches_map[mid] = m

    records = history_db.get("records", [])
    updated = 0

    for r in records:
        mid = r.get("match_id") or r.get("id") or ""
        r["id"] = mid # Standardize id property
        m_source = matches_map.get(mid, {})
        
        # Parse official code number (e.g. 218)
        code_num = None
        m_code = re.search(r"match_\d{6}_(\d+)", mid)
        if m_code:
            code_num = int(m_code.group(1))
        elif m_source.get("code"):
            try:
                code_num = int(m_source.get("code"))
            except:
                pass

        if code_num is not None and code_num < 500:
            r["code"] = str(code_num)
            r["match_no"] = f"周日 {code_num:03d}"
        elif m_source.get("match_no"):
            r["match_no"] = m_source.get("match_no")

        # Force official issue_date tag:
        # All 260726 matches (201 ~ 218) belong to issue_date 260726
        m_issue = re.search(r"match_(\d{6})_", mid)
        if m_issue:
            r["issue_date"] = m_issue.group(1)
        else:
            r["issue_date"] = "260726"

        updated += 1

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_db, f, ensure_ascii=False, indent=2)

    print(f"✅ [History Data Fix Completed] Successfully updated {updated} records with official Sporttery issue_date and match_no!")

if __name__ == "__main__":
    fix_history_sporttery()
