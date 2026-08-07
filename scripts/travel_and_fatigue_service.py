# -*- coding: utf-8 -*-
import json
import math
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_city_coordinates():
    path = os.path.join(BASE_DIR, "data", "city_coordinates.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("teams", {})
        except Exception:
            pass
    return {}

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Radius of Earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def calculate_travel_and_fatigue(home_team, away_team, kickoff_str, prev_kickoff_str=None, next_kickoff_str=None, next_tier=None, current_tier=None):
    coords_db = load_city_coordinates()
    
    home_data = coords_db.get(home_team, {"lat": 50.0, "lon": 10.0, "altitude": 100, "pitch": "natural"})
    away_data = coords_db.get(away_team, {"lat": 50.0, "lon": 10.0, "altitude": 100, "pitch": "natural"})
    
    # 1. Flight Travel Distance Calculation (Haversine)
    one_way_dist = haversine_distance(
        home_data.get("lat", 50.0), home_data.get("lon", 10.0),
        away_data.get("lat", 50.0), away_data.get("lon", 10.0)
    )
    round_trip_dist = one_way_dist * 2.0
    
    # Travel fatigue penalty
    travel_penalty = 0.0
    if round_trip_dist > 4000:
        travel_penalty = 0.15 # Severe long-haul flight fatigue
    elif round_trip_dist > 2000:
        travel_penalty = 0.08
    elif round_trip_dist > 1000:
        travel_penalty = 0.04

    # 2. Altitude Difference Calculation
    home_alt = home_data.get("altitude", 100)
    away_base_alt = away_data.get("altitude", 100)
    alt_diff = home_alt - away_base_alt
    
    altitude_penalty = 0.0
    altitude_warning = ""
    if alt_diff >= 1200:
        altitude_penalty = 0.20 # Extreme high altitude hypoxia penalty
        altitude_warning = f"🏔️ 高海拔严重缺氧 ({home_alt}m, 高于客队{alt_diff}m)"
    elif alt_diff >= 600:
        altitude_penalty = 0.10
        altitude_warning = f"🏔️ 中度高海拔缺氧 ({home_alt}m, 高于客队{alt_diff}m)"

    # 3. Rest Days & Schedule Density (Past 14 days)
    rest_hours = 120 # Default 5 days rest
    if prev_kickoff_str:
        try:
            fmt = "%Y-%m-%d %H:%M:%S" if " " in prev_kickoff_str else "%Y-%m-%dT%H:%M:%S"
            dt_curr = datetime.strptime(kickoff_str.replace("Z", ""), fmt)
            dt_prev = datetime.strptime(prev_kickoff_str.replace("Z", ""), fmt)
            rest_hours = max(24, (dt_curr - dt_prev).total_seconds() / 3600.0)
        except Exception:
            pass

    density_penalty = 0.0
    density_warning = ""
    if rest_hours < 72: # Less than 3 days rest
        density_penalty = 0.18
        density_warning = f"⚡ 急性双赛体能透支 (仅休整{int(rest_hours)}h)"
    elif rest_hours < 96: # Less than 4 days rest
        density_penalty = 0.08
        density_warning = f"⚡ 密集中期休整不足 ({int(rest_hours)}h)"

    # 4. Strategic Fighting Spirit Shift (Future 7 days)
    fighting_spirit_mult = 1.0
    strategic_warning = ""
    if next_kickoff_str and next_tier == "Tier1" and current_tier in ["Tier3", "Tier4"]:
        try:
            fmt = "%Y-%m-%d %H:%M:%S" if " " in next_kickoff_str else "%Y-%m-%dT%H:%M:%S"
            dt_curr = datetime.strptime(kickoff_str.replace("Z", ""), fmt)
            dt_next = datetime.strptime(next_kickoff_str.replace("Z", ""), fmt)
            hours_to_next = (dt_next - dt_curr).total_seconds() / 3600.0
            if hours_to_next <= 120: # Next match in <= 5 days is Tier 1 Champions League/Title Decider
                fighting_spirit_mult = 0.75
                strategic_warning = f"🎯 战略保留 (未来{int(hours_to_next/24)}天内有生死战)"
        except Exception:
            pass

    # Comprehensive CFI Fatigue Factor (Environmental & Schedule Composite Index)
    cfi_index = (1.0 - travel_penalty) * (1.0 - altitude_penalty) * (1.0 - density_penalty) * fighting_spirit_mult

    warnings = [w for w in [density_warning, altitude_warning, strategic_warning] if w]
    summary_str = " | ".join(warnings) if warnings else "休整与环境充沛"

    return {
        "one_way_dist_km": round(one_way_dist, 1),
        "round_trip_dist_km": round(round_trip_dist, 1),
        "home_altitude_m": home_alt,
        "altitude_diff_m": alt_diff,
        "rest_hours": round(rest_hours, 1),
        "cfi_index": round(cfi_index, 3),
        "fighting_spirit_mult": round(fighting_spirit_mult, 2),
        "warnings": warnings,
        "summary_str": summary_str
    }
