import json
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
input_path = os.path.join(base_dir, "data", "new_matches_input.json")

if not os.path.exists(matches_path):
    print("matches.json missing for cleanup.")
    sys.exit(1)

with open(matches_path, "r", encoding="utf-8") as f:
    database = json.load(f)

new_input_ids = set()
if os.path.exists(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            new_input = json.load(f)
            for item in new_input:
                new_input_ids.add(item.get("id"))
                sp_id = item.get("sportteryMatchId")
                if sp_id: new_input_ids.add(str(sp_id))
        except Exception:
            pass

cleaned_matches = []
unresolved_pending = []

for m in database.get("matches", []):
    # 1. 完场赛事绝对保留
    if m.get("status") == "finished":
        cleaned_matches.append(m)
    else:
        mid = m.get("id")
        sp_id = str(m.get("sportteryMatchId", ""))
        # 2. 如果在新输入的在售列表中，保留
        if mid in new_input_ids or sp_id in new_input_ids:
            cleaned_matches.append(m)
        else:
            # 3. 既未完场又不在最新在售列表中的赛事：保留并标记警报，等待用户确认处理
            unresolved_pending.append(m)
            cleaned_matches.append(m) # 安全保存在 matches.json 中，防止盲目抹除

database["matches"] = cleaned_matches

with open(matches_path, "w", encoding="utf-8") as f:
    json.dump(database, f, ensure_ascii=False, indent=2)

if unresolved_pending:
    print(f"\n⚠️ [安全防护警报] 发现 {len(unresolved_pending)} 场未查到赛果且不在当前在售列表中的赛事：")
    for m in unresolved_pending:
        print(f"  - {m.get('home')} vs {m.get('away')} ({m.get('id')}) | 状态: {m.get('status')}")
    print("已触发防误删保护：这些赛事已被安全保留在数据库中，请向用户询问是保留等待赛果还是彻底删除。")
else:
    print("✅ Cleanup completed! All matches verified safely.")
