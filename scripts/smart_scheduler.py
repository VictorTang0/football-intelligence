# -*- coding: utf-8 -*-
"""
Match IQ v6.0 - Smart Time-Window Scheduler (UTC+8 Beijing Time)
Enforces China time-window collection rules:
  - Workdays (Mon-Fri): Active window 11:00 - 22:00 (UTC+8)
  - Weekends (Sat-Sun): Active window 11:00 - 23:00 (UTC+8)
  - Off-hours: Low-power idle mode (no live API polling)
"""

from datetime import datetime, time

def get_window_status(now_dt=None):
    """
    Returns dict with window status:
    {
      "is_active_window": bool,
      "window_label": str,
      "mode": str ("Peak Monitoring" vs "Off-Hour Low Power"),
      "next_action": str
    }
    """
    if now_dt is None:
        now_dt = datetime.now()

    current_time = now_dt.time()
    is_weekend = now_dt.weekday() in [5, 6]  # 5: Sat, 6: Sun

    start_t = time(11, 0, 0)
    end_t = time(23, 0, 0) if is_weekend else time(22, 0, 0)

    is_active = (start_t <= current_time <= end_t)
    window_label = "周末 11:00-23:00" if is_weekend else "工作日 11:00-22:00"

    return {
        "is_active_window": is_active,
        "window_label": window_label,
        "mode": "高峰临场水温监控 (Peak Monitoring)" if is_active else "夜间/清晨低能耗休眠 (Off-Hour Idle)",
        "rate_limit_budget": "API-Football 100/天配额保护中",
        "current_time": now_dt.strftime("%H:%M")
    }

def should_execute_live_update(now_dt=None):
    """
    Returns True if live odds/news update is permitted under user's window rule
    """
    status = get_window_status(now_dt)
    return status["is_active_window"]

if __name__ == "__main__":
    status = get_window_status()
    print("Smart Window Status:", status)
