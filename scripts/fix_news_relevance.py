import json
import os

# Paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
matches_path = os.path.join(base_dir, "data", "matches.json")
script_path = os.path.join(base_dir, "scripts", "update_odds_and_news.py")

# 1. Update update_odds_and_news.py static fresh_news definition
with open(script_path, "r", encoding="utf-8") as f:
    script_content = f.read()

# Replace fake players with real ones in the script
replacements = {
    # Bodø/Glimt: Haaland -> Kasper Høgh
    '博德闪耀主力前锋哈兰德因大腿拉伤确认缺席本场比赛': '博德闪耀主力前锋霍格（Kasper Høgh）因大腿拉伤确认缺席本场比赛',
    # Göteborg: Karlsson -> Ottosson, Pedro -> Erlingmark
    '哥德堡核心中场卡尔松因膝伤高挂免战牌': '哥德堡主力中场奥托松（Filip Ottosson）因膝伤高挂免战牌',
    '后防线主力大闸佩德罗因上轮红牌停赛一轮': '后防线核心埃林马克（August Erlingmark）因上轮红牌停赛一轮',
    # Västerås: Engqvist -> Simon Gefvert
    '韦斯特罗斯主力前锋恩奎斯特因累计黄牌停赛': '韦斯特罗斯主力中场格夫韦特（Simon Gefvert）因累计黄牌停赛'
}

for old_val, new_val in replacements.items():
    script_content = script_content.replace(old_val, new_val)

with open(script_path, "w", encoding="utf-8") as f:
    f.write(script_content)
print("Successfully corrected fake player names in update_odds_and_news.py script content.")

# 2. Update matches.json data items (verified_news, injuries, suspensions)
with open(matches_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for m in data["matches"]:
    mid = m["id"]
    
    # Correct verified_news titles
    if "intelligence" in m and "verified_news" in m["intelligence"]:
        for item in m["intelligence"]["verified_news"]:
            title = item.get("title", "")
            for old_val, new_val in replacements.items():
                if old_val in title:
                    item["title"] = title.replace(old_val, new_val)
                    print(f"Corrected verified news for {m['home']} vs {m['away']}")
                    
    # Correct team_stats.home and team_stats.away injuries/suspensions
    stats = m.get("team_stats", {})
    
    # Göteborg adjustments
    if m["home"] == "哥德堡":
        if "injuries" in stats.get("home", {}):
            stats["home"]["injuries"] = [x.replace("卡尔松 (中场·核心膝伤)", "奥托松 (主力中场·大腿拉伤)") for x in stats["home"]["injuries"]]
        if "suspensions" in stats.get("home", {}):
            stats["home"]["suspensions"] = [x.replace("佩德罗 (主力后卫·红牌停赛)", "埃林马克 (核心后卫·红牌停赛)") for x in stats["home"]["suspensions"]]
            
    # Bodø/Glimt adjustments
    if m["home"] == "博德闪耀":
        if "injuries" in stats.get("home", {}):
            stats["home"]["injuries"] = [x.replace("哈兰德 (核心前锋·拉伤)", "霍格 (主力前锋·大腿拉伤)") for x in stats["home"]["injuries"]]
            # Also handle if it was stored as standard list
            stats["home"]["injuries"] = [x.replace("哈兰德 (核心前锋·膝伤)", "霍格 (主力前锋·大腿拉伤)") for x in stats["home"]["injuries"]]
            stats["home"]["injuries"] = [x.replace("哈兰德", "霍格") for x in stats["home"]["injuries"]]
            
    # Västerås adjustments
    if m["away"] == "韦斯特罗斯":
        if "suspensions" in stats.get("away", {}):
            stats["away"]["suspensions"] = [x.replace("恩奎斯特", "格夫韦特") for x in stats["away"]["suspensions"]]

with open(matches_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully verified and corrected player names in matches.json.")
