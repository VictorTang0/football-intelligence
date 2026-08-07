# -*- coding: utf-8 -*-
import json
import math
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_market_values():
    path = os.path.join(BASE_DIR, "data", "team_market_values.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("teams", {})
        except Exception:
            pass
    return {}

def calculate_market_value_factors(home_team, away_team, lineup_home_ratio=1.0, lineup_away_ratio=1.0):
    mv_db = load_market_values()
    
    home_mv = mv_db.get(home_team, {}).get("market_value", 25.0)
    away_mv = mv_db.get(away_team, {}).get("market_value", 25.0)
    
    # Avoid division by zero or log of <= 0
    home_mv = max(1.0, float(home_mv))
    away_mv = max(1.0, float(away_mv))
    
    # Log-scale market value ratio for M01 adjustment
    # ratio > 1 means Home higher market value; ratio < 1 means Away higher market value
    mv_ratio = home_mv / away_mv
    log_ratio = math.log10(mv_ratio)
    
    # M01 Multiplier: Range [0.85, 1.15]
    m01_multiplier = max(0.85, min(1.15, 1.0 + 0.15 * log_ratio))
    
    # M02 Lineup Coverage Ratio adjustment
    m02_home_health = max(0.60, min(1.0, float(lineup_home_ratio)))
    m02_away_health = max(0.60, min(1.0, float(lineup_away_ratio)))
    
    return {
        "home_market_value": home_mv,
        "away_market_value": away_mv,
        "mv_ratio": round(mv_ratio, 2),
        "log_ratio": round(log_ratio, 3),
        "m01_multiplier": round(m01_multiplier, 3),
        "m02_home_health": round(m02_home_health, 2),
        "m02_away_health": round(m02_away_health, 2),
        "summary_str": f"身价对比: 主 €{home_mv}M vs 客 €{away_mv}M (比值 {mv_ratio:.1f}x)"
    }
