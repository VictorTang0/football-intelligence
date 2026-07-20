import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
profiles_path = os.path.join(base_dir, "data", "league_profiles.json")

new_profiles = {
  "韩职": {
    "name": "K-League",
    "characteristics": "平局偏多 · 锋线转化率低 · 强队易爆冷",
    "modifiers": {
      "M02": 1.15,
      "M07": 1.10,
      "M08": 1.25
    }
  },
  "美职": {
    "name": "MLS",
    "characteristics": "大球天堂 · 重攻轻守 · 开放大开大合",
    "modifiers": {
      "M02": 0.80,
      "M03": 0.85,
      "M04": 1.25,
      "M07": 0.90
    }
  },
  "美职联": {
    "name": "MLS",
    "characteristics": "大球天堂 · 重攻轻守 · 开放大开大合",
    "modifiers": {
      "M02": 0.80,
      "M03": 0.85,
      "M04": 1.25,
      "M07": 0.90
    }
  },
  "瑞超": {
    "name": "Allsvenskan",
    "characteristics": "魔鬼主场 · 人工草皮差异 · 跨地区旅行疲劳",
    "modifiers": {
      "M06": 1.15,
      "M07": 1.30
    }
  },
  "巴甲": {
    "name": "Brasileirão",
    "characteristics": "对抗火爆 · 红黄牌率偏高 · 强力主场哨",
    "modifiers": {
      "M03": 1.20,
      "M07": 1.25,
      "M08": 1.10
    }
  },
  "世界杯": {
    "name": "World Cup",
    "characteristics": "杯赛极致战意 · 淘汰赛防平 · 心理压力巨大",
    "modifiers": {
      "M03": 1.25,
      "M07": 0.60,
      "M08": 1.25
    }
  },
  "世界杯半决赛": {
    "name": "World Cup",
    "characteristics": "杯赛极致战意 · 淘汰赛防平 · 心理压力巨大",
    "modifiers": {
      "M03": 1.25,
      "M07": 0.60,
      "M08": 1.25
    }
  },
  "西甲": {
    "name": "La Liga",
    "characteristics": "战术出球抗压 · 裁判VAR介入高 · 中场控盘",
    "modifiers": {
      "M01": 1.10,
      "M03": 1.15,
      "M04": 1.15
    }
  },
  "英超": {
    "name": "Premier League",
    "characteristics": "攻防节奏极快 · 身体对抗激烈 · 赛程压力重",
    "modifiers": {
      "M01": 1.15,
      "M05": 1.15,
      "M06": 1.10
    }
  },
  "日职": {
    "name": "J-League",
    "characteristics": "传控技术流 · 点球率偏低 · 主场优势较弱",
    "modifiers": {
      "M03": 1.15,
      "M04": 1.10,
      "M07": 0.85
    }
  },
  "挪超": {
    "name": "Eliteserien",
    "characteristics": "大球倾向明显 · 主场进球率高 · 攻强守弱",
    "modifiers": {
      "M05": 1.15,
      "M07": 1.20,
      "M08": 1.10
    }
  },
  "芬超": {
    "name": "Veikkausliiga",
    "characteristics": "球风保守 · 低比分偏多 · 客战难度大",
    "modifiers": {
      "M03": 1.15,
      "M04": 0.85,
      "M07": 1.20
    }
  },
  "欧冠资格赛第一轮（次回合）": {
    "name": "CL Qualifiers",
    "characteristics": "淘汰赛强弱悬殊 · 首尾分化极强 · 防冷门爆发",
    "modifiers": {
      "M01": 1.20,
      "M05": 0.80,
      "M08": 1.30
    }
  },
  "欧联资格赛": {
    "name": "EL Qualifiers",
    "characteristics": "淘汰赛强弱悬殊 · 首尾分化极强 · 防冷门爆发",
    "modifiers": {
      "M01": 1.20,
      "M05": 0.80,
      "M08": 1.30
    }
  }
}

with open(profiles_path, "w", encoding="utf-8") as f:
    json.dump(new_profiles, f, ensure_ascii=False, indent=2)

print("Successfully rebuilt league_profiles.json with M01-M08 mappings and new leagues.")
