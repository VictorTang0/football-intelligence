import json
import os

# 全量官方球场与草皮数据库 (Stadium & Turf Database)
stadium_turf_db = {
    # ─── 瑞典超 (Allsvenskan) ───
    "赫根": {"stadium": "Bravida Arena", "turf": "artificial", "accustomed": "artificial", "notes": "典型快速人造草，主场反弹陡"},
    "BK赫根": {"stadium": "Bravida Arena", "turf": "artificial", "accustomed": "artificial", "notes": "典型快速人造草，主场反弹陡"},
    "索尔纳": {"stadium": "Strawberry Arena (Friends Arena)", "turf": "natural", "accustomed": "natural", "notes": "伸缩顶棚天然草"},
    "AIK索尔纳": {"stadium": "Strawberry Arena (Friends Arena)", "turf": "natural", "accustomed": "natural", "notes": "伸缩顶棚天然草"},
    "马尔默": {"stadium": "Eleda Stadion", "turf": "natural", "accustomed": "natural", "notes": "优质标准天然草"},
    "哈马比": {"stadium": "Tele2 Arena", "turf": "artificial", "accustomed": "artificial", "notes": "人工合成草皮"},
    "佐加顿斯": {"stadium": "Tele2 Arena", "turf": "artificial", "accustomed": "artificial", "notes": "人工合成草皮"},
    "埃尔夫斯堡": {"stadium": "Borås Arena", "turf": "artificial", "accustomed": "artificial", "notes": "快速人造草"},
    "天狼星": {"stadium": "Studenternas IP", "turf": "artificial", "accustomed": "artificial", "notes": "人造草"},
    "瓦斯特拉斯": {"stadium": "Hitachi Energy Arena", "turf": "artificial", "accustomed": "artificial", "notes": "人造草"},
    "哈尔姆斯塔德": {"stadium": "Örjans Vall", "turf": "natural", "accustomed": "natural", "notes": "天然草"},

    # ─── 挪超 (Eliteserien) ───
    "罗森博格": {"stadium": "Lerkendal Stadion", "turf": "natural", "accustomed": "natural", "notes": "挪超最顶级天然草场"},
    "腓特烈斯塔": {"stadium": "Fredrikstad Stadion", "turf": "artificial", "accustomed": "artificial", "notes": "优质人造草"},
    "腓特烈": {"stadium": "Fredrikstad Stadion", "turf": "artificial", "accustomed": "artificial", "notes": "优质人造草"},
    "博德闪耀": {"stadium": "Aspmyra Stadion", "turf": "artificial", "accustomed": "artificial", "notes": "极地人工草，主场壁垒极强"},
    "维京": {"stadium": "SR-Bank Arena", "turf": "artificial", "accustomed": "artificial", "notes": "人造草"},
    "莫尔德": {"stadium": "Aker Stadion", "turf": "artificial", "accustomed": "artificial", "notes": "人造草"},
    "布兰": {"stadium": "Brann Stadion", "turf": "natural", "accustomed": "natural", "notes": "天然草"},
    "利勒斯特罗姆": {"stadium": "Åråsen Stadion", "turf": "natural", "accustomed": "natural", "notes": "天然草"},
    "汉坎": {"stadium": "Briskeby Arena", "turf": "artificial", "accustomed": "artificial", "notes": "人造草"},
    "斯达": {"stadium": "Sparebanken Sør Arena", "turf": "artificial", "accustomed": "artificial", "notes": "人造草"},

    # ─── 韩职联 (K-League 1) ───
    "首尔FC": {"stadium": "Seoul World Cup Stadium", "turf": "hybrid", "accustomed": "hybrid", "notes": "混合草皮"},
    "蔚山现代": {"stadium": "Ulsan Munsu Football Stadium", "turf": "natural", "accustomed": "natural", "notes": "天然草"},
    "全北现代": {"stadium": "Jeonju World Cup Stadium", "turf": "natural", "accustomed": "natural", "notes": "天然草"},
    "江原FC": {"stadium": "Chuncheon Songam Sports Town", "turf": "natural", "accustomed": "natural", "notes": "天然草"},

    # ─── 巴甲 (Brasileirão) ───
    "弗拉门戈": {"stadium": "Maracanã", "turf": "hybrid", "accustomed": "hybrid", "notes": "马拉卡纳混合草"},
    "博塔弗戈": {"stadium": "Nilton Santos", "turf": "artificial", "accustomed": "artificial", "notes": "巴甲少有人造草场"},
    "巴拉纳竞技": {"stadium": "Ligga Arena", "turf": "artificial", "accustomed": "artificial", "notes": "人造草"}
}

def get_pitch_info(home_name, away_name):
    """
    根据主客队获取球场场地与草皮不适配向量 (Turf Mismatch Vector)
    """
    home_data = None
    for k, v in stadium_turf_db.items():
        if k in home_name or home_name in k:
            home_data = v
            break
            
    away_data = None
    for k, v in stadium_turf_db.items():
        if k in away_name or away_name in k:
            away_data = v
            break

    stadium = home_data.get("stadium", "常规主场") if home_data else "常规主场"
    turf_type = home_data.get("turf", "natural") if home_data else "natural"
    home_acc = home_data.get("accustomed", "natural") if home_data else "natural"
    away_acc = away_data.get("accustomed", "natural") if away_data else "natural"
    notes = home_data.get("notes", "标准草皮场地") if home_data else "标准草皮场地"

    # 判断草皮错位壁垒 (Turf Mismatch)
    # 如: 主场是人造草 (artificial)，而客队习惯天然草 (natural)
    is_mismatch = (turf_type == "artificial" and away_acc == "natural")
    
    label = "天然草场地"
    if turf_type == "artificial":
        label = "人工合成草皮 (快速球速)"
        if is_mismatch:
            label += " ⚡ [客队天然草不适应壁垒]"
    elif turf_type == "hybrid":
        label = "顶级混合草皮"

    return {
        "stadium_name": stadium,
        "turf_type": turf_type,
        "home_accustomed": home_acc,
        "away_accustomed": away_acc,
        "turf_mismatch": is_mismatch,
        "display_label": label,
        "notes": notes
    }

def enrich_pitch_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    
    if not os.path.exists(matches_path):
        print(f"Error: {matches_path} not found.")
        return

    with open(matches_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated_count = 0
    for match in data.get("matches", []):
        if match.get("status") in ["finished", "postponed"]:
            continue
            
        home_name = match.get("home", "")
        away_name = match.get("away", "")
        
        pitch_info = get_pitch_info(home_name, away_name)
        match["pitch_info"] = pitch_info
        updated_count += 1

    with open(matches_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ [场地草皮数据挂载完毕] 成功为 {updated_count} 场比赛注入官方场地草皮元数据!")

if __name__ == "__main__":
    enrich_pitch_data()
