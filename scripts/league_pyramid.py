# -*- coding: utf-8 -*-
"""
Match IQ v6.0 - League Pyramid Routing & LRI (League Rating Index) Module
Handles Tier 1/2/3 classification, LRI adjustments, and Proxy xG estimation.
"""

# League Quality Ratings (Base = 1.00 for UEFA Champions League / Premier League)
LEAGUE_LRI_MAP = {
    "欧冠": 1.00,
    "欧洲冠军": 1.00,
    "英超": 1.00,
    "德甲": 0.95,
    "西甲": 0.95,
    "意甲": 0.92,
    "法甲": 0.90,
    "欧联": 0.88,
    "葡超": 0.82,
    "荷甲": 0.82,
    "巴甲": 0.80,
    "美职": 0.75,
    "美职联": 0.75,
    "瑞超": 0.70,
    "挪超": 0.70,
    "芬超": 0.65,
    "韩职": 0.72,
    "日职": 0.74,
    "巴西杯": 0.78,
}

def get_league_tier_and_lri(league_name):
    """
    Returns (Tier, LRI Rating)
    Tier 1: High-precision top leagues (xG/xA ML)
    Tier 2: Mainstream mid leagues (Dynamic Elo + Bivariate Poisson)
    Tier 3: Niche / Low-tier (Market Anomaly & Slope)
    """
    if not league_name:
        return "Tier 3", 0.60
    
    lri = 0.65  # Default baseline
    for k, v in LEAGUE_LRI_MAP.items():
        if k in league_name:
            lri = v
            break
            
    if lri >= 0.90:
        return "Tier 1", lri
    elif lri >= 0.70:
        return "Tier 2", lri
    else:
        return "Tier 3", lri

def calculate_proxy_xg(shots_on_target, shots_inside_box=0, total_shots=0):
    """
    Proxy xG Engine: Calculates estimated xG from shot parameters when event-level xG is missing
    Formula: Proxy_xG = ShotsOnTarget * 0.32 + InsideBoxShots * 0.15 + (TotalShots - ShotsOnTarget) * 0.03
    """
    sot = max(0, shots_on_target or 0)
    sib = max(0, shots_inside_box or 0)
    tot = max(sot, total_shots or 0)
    outside_shots = max(0, tot - sot)
    
    proxy_xg = round(sot * 0.32 + sib * 0.15 + outside_shots * 0.03, 2)
    return max(0.05, proxy_xg)

def adjust_rating_for_promotion(team_rating, is_promoted=False, lri_diff=0.0):
    """
    Prevents concept drift for promoted teams by applying LRI discount factor
    """
    if is_promoted:
        return round(team_rating * 0.88, 2)
    if lri_diff != 0.0:
        return round(team_rating * (1.0 + lri_diff * 0.15), 2)
    return team_rating
