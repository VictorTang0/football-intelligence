import json
import os

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    matches_path = os.path.join(base_dir, "data", "matches.json")
    history_path = os.path.join(base_dir, "data", "history.json")
    
    half_time_results = {
        "match_260715_102": "阿根廷 2-1 英格兰 (1-1)",
        "match_260715_201": "比森 1-2 克拉克斯 (0-0)",
        "match_260715_202": "苏德斯卡 0-2 阿拉木图 (0-0)",
        "match_260716_201": "瓦勒伦加 6-1 奥勒松 (3-0)",
        "match_260716_202": "德里城 1-2 索陆军 (0-1)",
        "match_260716_203": "费伦茨 3-0 伏伊伏丁 (1-0)",
        "match_260716_204": "日利纳 2-1 斯海杜克 (1-0)",
        "match_260716_205": "博塔弗戈 2-1 桑托斯 (1-1)",
        "match_260716_206": "维多利亚 1-0 达伽马 (0-0)",
        "match_260716_207": "蒙特利尔 0-0 多伦多 (0-0)",
        "match_260716_209": "圣路易城 3-2 堪萨斯城 (2-0)",
        "match_260716_210": "西雅图 1-5 波特兰 (0-2)",
        "match_260717_201": "哥德堡 2-1 布鲁马波 (1-0)",
        "match_260717_202": "米亚尔比 0-0 韦斯特罗斯 (0-0)",
        "match_260717_203": "博德闪耀 1-0 腓特烈 (0-0)",
        "match_260717_204": "巴伊亚 2-0 沙佩科 (1-0)",
        "match_260717_205": "弗鲁米嫩 1-1 布拉干RB (1-0)",
        "match_260717_206": "米拉索尔 2-1 格雷米奥 (1-1)",
        "match_260717_207": "纳什维尔 1-0 亚特联 (1-0)",
        "match_260717_208": "洛城银河 0-3 洛杉矶FC (0-0)",
        "match_260718_201": "大田市民 2-2 蔚山现代 (1-1)",
        "match_260718_202": "江原FC 2-0 金泉尚武 (1-0)",
        "match_260718_203": "济州SK 2-1 浦项制铁 (0-1)",
        "match_260718_204": "仁川联 1-0 全北现代 (0-0)",
        "match_260718_205": "汉坎 1-4 特罗姆瑟 (0-2)",
        "match_260718_206": "赫尔辛基 2-1 瓦萨 (1-0)",
        "match_260718_207": "索尔纳 2-0 盖斯 (0-0)",
        "match_260718_208": "利勒斯特 1-1 奥斯KFUM (0-1)",
        "match_260718_209": "斯达 0-3 罗森博格 (0-1)",
        "match_260718_210": "克里斯蒂 0-0 萨普斯堡 (0-0)",
        "match_260718_211": "AC奥卢 0-2 赫尔火花 (0-1)",
        "match_260718_212": "塞伊奈 0-2 库奥皮奥 (0-2)",
        "match_260719_103": "法国 4-6 英格兰 (1-2)",
        "match_260719_201": "富川FC 1-3 首尔FC (0-1)",
        "match_260719_202": "安养FC 1-1 光州FC (1-0)",
        "match_260719_203": "埃夫斯堡 1-3 天狼星 (0-0)",
        "match_260719_204": "哈尔姆斯 0-2 赫根 (0-1)",
        "match_260719_205": "哈马比 4-0 代格福什 (2-0)",
        "match_260719_206": "雅罗 0-0 国际图尔 (0-0)",
        "match_260719_213": "莫尔德 1-2 布兰 (0-1)",
        "match_260719_214": "维京 2-1 桑纳菲 (1-1)",
        "match_260720_104": "西班牙 0-0 阿根廷 (0-0)"
    }
    
    # 1. Update matches.json
    if os.path.exists(matches_path):
        with open(matches_path, "r", encoding="utf-8") as f:
            matches_db = json.load(f)
            
        updated_m = 0
        for m in matches_db["matches"]:
            mid = m["id"]
            if mid in half_time_results:
                m["ultimate_conclusion"]["actual_result"] = half_time_results[mid]
                updated_m += 1
                
        with open(matches_path, "w", encoding="utf-8") as f:
            json.dump(matches_db, f, ensure_ascii=False, indent=2)
        print(f"🎉 Updated {updated_m} match results in matches.json!")
        
    # 2. Update history.json
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            history_db = json.load(f)
            
        updated_h = 0
        for r in history_db["records"]:
            mid = r["match_id"]
            if mid in half_time_results:
                r["actual_result"] = half_time_results[mid]
                updated_h += 1
                
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history_db, f, ensure_ascii=False, indent=2)
        print(f"🎉 Updated {updated_h} history records in history.json!")

if __name__ == "__main__":
    main()
