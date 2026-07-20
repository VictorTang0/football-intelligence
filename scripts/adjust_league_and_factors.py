import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
profiles_path = os.path.join(base_dir, "data", "league_profiles.json")

# Load existing profiles
with open(profiles_path, "r", encoding="utf-8") as f:
    profiles = json.load(f)

# Adjust profiles based on the user's reference criteria:
# 1. Home Advantage: 巴甲 (1.28) > 挪超 (1.18) > 美职联 (0.85)
# 2. Draw Rate: 美职联 (M01=0.82, M05=0.82) > 巴甲 (M01=0.92) > 挪超 (M01=1.12)
# 3. Upset Rate: 美职联 (M05=0.82, M08=1.25) > 挪超 (M08=1.15) > 巴甲 (M08=1.05)

# Update 巴甲
profiles["巴甲"] = {
    "name": "Brasileirão",
    "characteristics": "极强主场优势 · 平局率中等 · 爆冷率较小 · 对抗火爆",
    "modifiers": {
        "M01": 0.92, # Moderate draw rate
        "M03": 1.20,
        "M05": 1.15, # Low upset rate (momentum is stable)
        "M07": 1.28, # Highest home advantage
        "M08": 1.05
    }
}

# Update 挪超
profiles["挪超"] = {
    "name": "Eliteserien",
    "characteristics": "中等主场优势 · 平局率较低 · 爆冷率中等 · 大球倾向",
    "modifiers": {
        "M01": 1.12, # Lowest draw rate (high variance/clear wins)
        "M05": 1.10,
        "M07": 1.18, # Moderate home advantage
        "M08": 1.15  # Moderate upset rate
    }
}

# Update 美职联 / 美职 (Apply to both keys for consistency)
for key in ["美职", "美职联"]:
    profiles[key] = {
        "name": "MLS",
        "characteristics": "主场优势微弱 · 平局率偏高 · 爆冷率偏高 · 大球天堂",
        "modifiers": {
            "M01": 0.82, # Highest draw rate (strength parity)
            "M02": 0.80,
            "M03": 0.85,
            "M04": 1.25,
            "M05": 0.82, # High upset rate (form shifts quickly)
            "M07": 0.85, # Lowest home advantage
            "M08": 1.25
        }
    }

with open(profiles_path, "w", encoding="utf-8") as f:
    json.dump(profiles, f, ensure_ascii=False, indent=2)

print("Successfully adjusted league profiles according to user's criteria.")
