# -*- coding: utf-8 -*-
import urllib.request
import json
import random
import re
import time
import os

PUSHPLUS_TOKEN = "960491d71cdb4ce8b10b5a7de29ac5e6"

LUCK_QUOTES = [
    "好运只偏爱有准备的头脑，祝今天旗开得胜！🎲✨",
    "筹码在手，天下我有，祝今日红单连连！💰🔥",
    "借东风，迎财神，愿今天好运常伴你左右！🍀🏮",
    "冷静博弈，理智前行，好运自然水到渠成！🎯💼",
    "搏一搏，单车变摩托；祝今日大红大紫，福星高照！🏍️🚀",
    "财富的密码已经开启，愿你的选择今天能得到运气的拥抱！🔑💎",
    "量化数据为底，财神眷顾在旁，祝今天一红到底！📊📈",
    "智者不入爱河，博者手握乾坤，祝今日逢赌必胜！🎲👑",
    "富贵险中求，红单信手抓，愿命运女神今天向你微笑！🍀🎰",
    "乾坤未定，你我皆是黑马，祝今日盘盘开花！🐎🏆"
]

COMMON_CSS = """<style>
.m-card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:10px;margin-bottom:8px;}
.m-header{display:flex;justify-space-between;align-items:center;border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:5px;margin-bottom:6px;}
.m-teams{font-size:14px;font-weight:bold;color:#ffffff;}
.m-rec{font-size:13px;font-weight:bold;color:#38bdf8;}
.m-box{background:rgba(0,0,0,0.25);border-radius:6px;padding:6px 8px;font-size:11.5px;color:#cbd5e1;display:flex;flex-direction:column;gap:4px;}
.m-script{font-size:11px;color:#94a3b8;background:rgba(56,189,248,0.04);border-left:2px solid #38bdf8;padding:5px 7px;margin-top:5px;border-radius:0 4px 4px 0;line-height:1.4;}
.br{background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3);padding:1px 4px;border-radius:3px;font-size:9.5px;}
.b{color:#38bdf8;font-weight:bold;margin-left:1px;}
.g{color:#fbbf24;font-weight:bold;margin-left:1px;}
</style>"""

def send_push(title, content):
    title = str(title).replace("竞彩首选", "竞彩")
    content = str(content).replace("竞彩首选", "竞彩")
    url = f"http://www.pushplus.plus/send?token={PUSHPLUS_TOKEN}"
    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_text = response.read().decode("utf-8")
            return json.loads(res_text)
    except Exception as e:
        print(f"Push error: {e}")
        return {"code": 500, "msg": str(e)}

def sort_matches_by_date_and_code(matches_list):
    def sort_key(m):
        rank = 0 if (m.get("status") == "waiting_result" or m.get("status_label") == "等待赛果") else 1
        dt_code = m.get("issue_date") or m.get("business_date") or ""
        if not dt_code:
            dt_code = (m.get("kickoff") or m.get("kickoff_time") or "").split("T")[0].split(" ")[0]
        num_code = m.get("match_code")
        if num_code is None:
            num_str = m.get("match_no") or m.get("id") or ""
            num_match = re.search(r'\d+$', num_str)
            num_code = int(num_match.group(0)) if num_match else 999
        return (rank, dt_code, num_code)
    return sorted(matches_list, key=sort_key)

def get_handicap_info_html(m):
    c = m.get("conclusions", {})
    uc = m.get("ultimate_conclusion", {})
    oa = m.get("odds_analysis", {})
    
    lh = oa.get("lottery_handicap", {})
    hc_raw = lh.get("handicap", "")
    hc_num = 0
    if "主让" in str(hc_raw) or "-1" in str(hc_raw):
        hc_num = -1
    elif "客让" in str(hc_raw) or "+1" in str(hc_raw):
        hc_num = 1
    elif c.get("hhad_hc"):
        try:
            hc_num = int(c.get("hhad_hc"))
        except:
            hc_num = -1

    if hc_num == 0:
        hc_num = -1

    hc_label = f"+{hc_num}" if hc_num > 0 else f"{hc_num}"

    hhad_rec = c.get("hhad_recommendation") or uc.get("secondary_bet") or ""
    if not hhad_rec or hhad_rec == "--":
        rec = uc.get("recommendation", "")
        if "主胜" in rec:
            hhad_rec = "让主胜"
        elif "客胜" in rec:
            hhad_rec = "让客胜"
        elif "主不败" in rec:
            hhad_rec = "让平 或 让胜" if hc_num == -1 else "让主胜"
        elif "客不败" in rec:
            hhad_rec = "让平 或 让客胜" if hc_num == -1 else "让客胜"
        else:
            hhad_rec = "让平"

    if "(竞彩" not in hhad_rec and "让" in hhad_rec:
        hhad_rec += " (竞彩)"

    hhad_rec = hhad_rec.replace("竞彩", "竞彩")
    sp_val = c.get("hhad_sp", "") or lh.get("current", {}).get("draw", "")
    sp_str = f' <span style="color:#64748b;font-size:10.5px;">[SP:{sp_val}]</span>' if sp_val else ''

    return f"让球({hc_label}): <span style='color:#38bdf8;font-weight:bold;'>{hhad_rec}</span>{sp_str}"

def format_goals_formatted_html(m):
    c = m.get("conclusions", {})
    uc = m.get("ultimate_conclusion", {})
    score_str = c.get("most_likely_score") or uc.get("predicted_score", "")
    
    p_goals = []
    matches_p = re.findall(r'\d+[:\-]\d+', score_str)
    if matches_p:
        for s in matches_p:
            parts = re.split(r'[:\-]', s)
            p_goals.append(int(parts[0]) + int(parts[1]))
        p_goals = sorted(list(set(p_goals)))[:2]
        
    m_goals = []
    m10_scores = c.get("sporttery_hot_scores", [])
    snapshot_count = c.get("m10_snapshot_count", 1)
    if snapshot_count >= 2 and m10_scores:
        limit = 1 if c.get("had_hhad_divergence") else 2
        target_scores = m10_scores[:limit]
        matches_m = re.findall(r'\d+[:\-]\d+', " ".join(target_scores))
        if matches_m:
            for s in matches_m:
                parts = re.split(r'[:\-]', s)
                m_goals.append(int(parts[0]) + int(parts[1]))
            m_goals = sorted(list(set(m_goals)))
            
    combined = sorted(list(set(p_goals + m_goals)))
    if not combined:
        goals_raw = str(c.get("over_under", "--")).replace("球", "").strip()
        return f'<span style="color:#38bdf8;font-weight:bold;">({goals_raw})</span>'

    items_html = []
    for g in combined:
        in_m = (g in m_goals)
        if in_m:
            items_html.append(f'<span style="color:#fbbf24;font-weight:bold;font-size:12px;">{g}</span>')
        else:
            items_html.append(f'<span style="color:#38bdf8;font-weight:bold;font-size:12px;">{g}</span>')

    return "(" + "、".join(items_html) + ")"

def get_arrow_html(m, subitem_key):
    arrows = m.get("subitem_arrows", {}).get(subitem_key, {})
    p_arrow = arrows.get("primary", "none")
    m_arrow = arrows.get("m10", "none")

    res = ""
    if p_arrow == "up":
        res += '<span class="b">↑</span>'
    elif p_arrow == "down":
        res += '<span class="b">↓</span>'

    if m_arrow == "up":
        res += '<span class="g">↑</span>'
    elif m_arrow == "down":
        res += '<span class="g">↓</span>'

    return res

def render_match_card_html(m):
    match_no = m.get("match_num_str") or m.get("match_no") or m.get("id", "").split("_")[-1]
    home = m.get("home", "")
    away = m.get("away", "")
    league = m.get("league", "")
    kickoff = m.get("kickoff_time") or m.get("kickoff", "")
    if "T" in kickoff:
        kickoff = kickoff.split("T")[1][:5]
    elif " " in kickoff:
        parts = kickoff.split(" ")
        if len(parts) > 1:
            kickoff = parts[1][:5]

    uc = m.get("ultimate_conclusion", {})
    c = m.get("conclusions", {})
    diff = m.get("diff_markers", {})

    had_changed = diff.get("had") or (m.get("baseline_recommendation") and m.get("baseline_recommendation") != m.get("current_recommendation") and m.get("baseline_recommendation") != "--")
    water_changed = m.get("odds_water_changed", False)
    score_changed = diff.get("score", False)
    goals_changed = diff.get("goals", False)
    hf_changed = diff.get("hf", False)

    has_match_changed = m.get("has_conclusion_changed", False) or had_changed or score_changed or goals_changed or hf_changed

    time_dot = '<span style="font-size:10px;margin-left:3px;">🟡</span>' if has_match_changed else ''
    dot_had = "🟡 " if had_changed else ""
    dot_water = "🟡 " if water_changed else ""
    dot_score = "🟡 " if score_changed else ""
    dot_goals = "🟡 " if goals_changed else ""
    dot_hf = "🟡 " if hf_changed else ""

    arrow_had = get_arrow_html(m, "had")
    arrow_score = get_arrow_html(m, "score")
    arrow_goals = get_arrow_html(m, "goals")
    arrow_hf = get_arrow_html(m, "hf")

    baseline_rec = m.get("baseline_recommendation", "--")
    current_rec = (m.get("current_recommendation") or uc.get("recommendation", "--"))
    conf = uc.get("confidence", 60)
    risk_level = uc.get("risk_level", "中")
    
    if conf < 60:
        current_rec = current_rec.replace("(竞彩)", "").replace("竞彩", "").strip()
    elif "(竞彩" not in current_rec and "竞彩" in str(uc.get("primary_bet", "")):
        current_rec += " (竞彩)"
    current_rec = current_rec.replace("竞彩首选", "竞彩")
    handicap_html = get_handicap_info_html(m)
    conf_color = "#10b981" if conf >= 75 else "#fbbf24"
    
    risk_color = "#10b981" if risk_level == "低" else "#f59e0b" if risk_level == "中" else "#f43f5e"
    risk_bg = "rgba(16,185,129,0.15)" if risk_level == "低" else "rgba(245,158,11,0.15)" if risk_level == "中" else "rgba(244,63,94,0.15)"

    is_radar = m.get("radar_triggered") or c.get("had_hhad_divergence", False)
    radar_badge = ' <span class="br">雷达预警</span>' if is_radar else ''

    has_rec_changed = (baseline_rec != current_rec and baseline_rec != "--")
    if has_rec_changed:
        rec_display = f'{dot_had}<span style="text-decoration:line-through;color:#64748b;font-size:11px;">{baseline_rec}</span>➔<span style="color:#f43f5e;font-weight:bold;text-decoration:underline;font-size:13px;">{current_rec}</span>{arrow_had}'
    else:
        rec_display = f'{dot_had}<span style="color:#38bdf8;font-weight:bold;font-size:13px;">{current_rec}</span>{arrow_had}'

    scores = m.get("current_scores") or uc.get("predicted_score") or c.get("most_likely_score", "--")
    goals_html = format_goals_formatted_html(m)
    hf = c.get("half_full", "--")

    # M10 System Hub Object (Strictly 100% Aligned with Web UI render.js L1203-L1218)
    oa = m.get("odds_analysis", {}) or {}
    hub = m.get("m10_hub_analysis") or c.get("m10_hub_analysis") or {}

    # Bold Score (大胆比分 / M10 动态大胆预测) - Directly reads hub.m10_bold_score or c.m10_bold_score
    raw_bold = hub.get("m10_bold_score") or c.get("m10_bold_score") or ""
    if not raw_bold or raw_bold == "None" or raw_bold == "--":
        bold_score_val = "无"
    else:
        bold_score_val = str(raw_bold).replace("💥", "").strip()

    odds_mov = m.get("odds_movement_str", "")
    water_row_html = ""
    if odds_mov:
        water_row_html = f'<div style="font-size:11px;color:#94a3b8;margin-bottom:5px;">💧 {dot_water}<strong>水位异动</strong>: <span style="color:#fbbf24;font-weight:bold;">{odds_mov}</span></div>'

    # M10 System Conclusion formatting (Strictly Aligned with Web UI render.js L1202-L1250)
    snap_cnt = c.get("m10_snapshot_count") or hub.get("snapshot_count") or (oa.get("water_trajectory", []) and len(oa.get("water_trajectory"))) or 1
    
    clean_rec = lambda txt: str(txt).replace("(竞彩)", "").replace("（竞彩）", "").replace("竞彩", "").replace("None", "").strip() if txt and txt != "--" and txt != "None" else ""
    had_val = clean_rec(hub.get("had_recommendation") or hub.get("m10_had") or hub.get("had_analysis", {}).get("primary"))
    hhad_val = clean_rec(hub.get("hhad_recommendation") or hub.get("m10_hhad") or hub.get("hhad_analysis", {}).get("primary"))
    eu_an = hub.get("asian_eu_status", {}) if isinstance(hub, dict) else {}

    if snap_cnt < 2:
        m10_text = '<span style="color:#94a3b8;">变盘次数不足</span>'
    else:
        parts = []
        if had_val and had_val != "无推荐":
            parts.append(f"胜平负:{had_val}")
        if hhad_val and hhad_val != "无推荐":
            parts.append(f"让球:{hhad_val}")
        if eu_an.get("has_divergence"):
            parts.append("欧让剪刀差")
        
        range_pref = oa.get("m10_hhad_range_preference")
        if range_pref and range_pref not in parts:
            parts.append(range_pref)
            
        m10_text = " | ".join(parts) if parts else "水温拉锯平稳"

    # Monte Carlo 5000 Sandbox Simulation & Wild Outliers (大球比分) matching Web UI render.js L1263-L1315
    wild_html = ""
    try:
        from generate_pure_m10_conclusions import run_python_simulation_1000
        sim = run_python_simulation_1000(m)
        win_rate = sim.get("winRate", {})
        h_pct = win_rate.get("homePct", "0")
        d_pct = win_rate.get("drawPct", "0")
        a_pct = win_rate.get("awayPct", "0")
        style_name = sim.get("styleTag", {}).get("name", "沙盘推演")
        top_s = sim.get("topScores", [{}])[0]
        top_score_str = f"{top_s.get('score', '--')} ({top_s.get('pct', '')})" if top_s else "--"
        
        sandtable_html = f'{style_name}: 主胜{h_pct}%/平{d_pct}%/客胜{a_pct}% (最频 {top_score_str})'

        wild = sim.get("wildOutliers", [])
        if wild and len(wild) > 0 and wild[0].get("score"):
            wild_score_str = f"{wild[0].get('score')} ({wild[0].get('pct')})"
            wild_html = f'<div>💥 <strong>狂野大球比分</strong>: <span style="color:#ef4444;font-weight:bold;">{wild_score_str}</span></div>'
    except Exception:
        sandtable_html = '<span style="color:#64748b;">推演计算中...</span>'

    # Bookmaker intent / script summary
    script = oa.get("bookmaker_backed_script", "")
    script_html = ""
    if script:
        clean_script = script.replace("【庄家看好剧本】", "").strip()
        script_html = f'<div class="m-script">🎬 <strong>看好剧本</strong>: {clean_script}</div>'

    return f'''<div class="m-card"><div class="m-header"><span style="font-size:11px;color:#94a3b8;font-weight:bold;">{match_no} • {kickoff} ({league}) {time_dot}</span><span style="font-size:10px;padding:1.5px 6px;border-radius:4px;background:{risk_bg};color:{risk_color};font-weight:bold;">{risk_level}风控</span></div><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;"><div class="m-teams">{home} <span style="color:#64748b;font-size:11px;font-weight:normal;">VS</span> {away}</div><div class="m-rec">{rec_display} <span style="font-size:11px;color:{conf_color};">[{conf}%]</span>{radar_badge}</div></div>{water_row_html}<div class="m-box"><div>🎯 <strong>竞彩玩法</strong>: {handicap_html}</div><div>⚽ <strong>最可能比分</strong>: {dot_score}<span style="color:#10b981;font-weight:bold;">{scores}</span>{arrow_score} | 💥 <strong>大胆比分</strong>: <span style="color:#fbbf24;font-weight:bold;">{bold_score_val}</span></div><div>⚽ <strong>具体进球</strong>: {dot_goals}{goals_html}{arrow_goals} | ⏱️ <strong>半全场</strong>: {dot_hf}<span style="color:#a855f7;font-weight:bold;">{hf}</span>{arrow_hf}</div><div>🟡 <strong>M10中枢结论</strong>: <span style="color:#fbbf24;font-weight:bold;">{m10_text}</span></div><div>🎮 <strong>沙盘推演(5000次)</strong>: <span style="color:#38bdf8;font-weight:bold;">{sandtable_html}</span></div>{wild_html}</div>{script_html}</div>'''

def push_scheduled_update(matches, has_any_change=False):
    # 防骚扰硬性冷却过滤: 间隔 < 30 分钟且没有重大变盘变化时静默跳过
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_file = os.path.join(base_dir, "data", "scheduler_state.json")
        now_ts = int(time.time())
        if os.path.exists(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                st = json.load(f)
            last_push_ts = st.get("last_push_timestamp", 0)
            if not has_any_change and (now_ts - last_push_ts < 1800): # 30 mins
                print(f"🔕 [Push Cooldown] 上次推送时间在 30 分钟内 ({now_ts - last_push_ts}s 之前)，且无重大方向变化，跳过 Push 消息。")
                return {"code": 200, "msg": "cooldown_skipped"}
            st["last_push_timestamp"] = now_ts
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(st, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning during cooldown check: {e}")

    sorted_matches = sort_matches_by_date_and_code(matches)
    cards_html = "".join([render_match_card_html(m) for m in sorted_matches])
    
    title_prefix = "情况有变" if has_any_change else "牌没问题"
    title = f"{title_prefix} - MATCH IQ 临场简报 ({len(matches)}场)"
    
    header_color = "#f43f5e" if has_any_change else "#10b981"
    sub_text = "极简临场变盘与双系统总结卡片 (变盘项已标 🟡)：" if has_any_change else "临场水温平稳，双系统总结卡片："

    selected_quote = random.choice(LUCK_QUOTES)
    quote_html = f'<div style="background-color:rgba(56,189,248,0.04);padding:6px 8px;border-radius:6px;border:1px solid rgba(56,189,248,0.15);font-size:11px;text-align:center;font-weight:bold;color:#38bdf8;margin-top:8px;">{selected_quote}</div>'

    content = f"""{COMMON_CSS}<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background-color:#0f172a;color:#f1f5f9;padding:10px;border-radius:8px;border:1px solid rgba(0,212,255,0.2);"><h4 style="color:{header_color};margin-top:0;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:5px;font-size:15px;">{title_prefix} • 临场总结 (共{len(matches)}场)</h4><p style="font-size:11px;color:#94a3b8;margin-top:4px;margin-bottom:8px;">{sub_text}</p>{cards_html}{quote_html}<p style="font-size:10.5px;color:#64748b;text-align:center;margin-top:10px;margin-bottom:0;">💬 极简总结推送 • <a href="https://victortang0.github.io/football-intelligence/" style="color:#00d4ff;text-decoration:none;">打开 MATCH IQ 看板 ➔</a></p></div>"""
    return send_push(title, content)

def push_daily_results(records_settled, model_evolution):
    version = model_evolution.get("version", "v1.0")
    direction_acc = model_evolution.get("direction_accuracy", 0.0)
    score_acc = model_evolution.get("score_accuracy", 0.0)
    total_validated = model_evolution.get("total_validated_matches", 0)

    rows_html = ""
    for r in records_settled:
        match_no = r.get("match_no", "")
        home = r.get("home", "")
        away = r.get("away", "")
        rec = r.get("recommendation", "").replace("竞彩", "竞彩")
        score = r.get("score", "")
        is_correct = r.get("is_correct", False)
        actual = r.get("actual_result", "")

        status_html = '<span style="color:#10b981;font-weight:bold;">红 📈</span>' if is_correct else '<span style="color:#94a3b8;">黑 📉</span>'
        rows_html += f"""<tr style="border-bottom:1px solid rgba(255,255,255,0.05);"><td style="padding:6px;font-weight:bold;color:#94a3b8;">{match_no}</td><td style="padding:6px;">{home} vs {away}</td><td style="padding:6px;color:#38bdf8;">{rec} <span style="font-size:10px;color:#64748b;">({score})</span></td><td style="padding:6px;font-family:monospace;">{actual}</td><td style="padding:6px;">{status_html}</td></tr>"""

    content = f"""{COMMON_CSS}<div style="font-family:Arial,sans-serif;background-color:#0f172a;color:#f1f5f9;padding:12px;border-radius:8px;border:1px solid rgba(0,212,255,0.2);"><h3 style="color:#10b981;margin-top:0;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:6px;">💰 MATCH IQ 昨日红黑清算单</h3><p style="font-size:12px;color:#94a3b8;">昨日已完赛赛事预测结算列表：</p><table style="width:100%;border-collapse:collapse;margin:12px 0;font-size:11px;color:#e2e8f0;text-align:left;"><thead><tr style="background-color:rgba(255,255,255,0.03);border-bottom:1px solid rgba(255,255,255,0.1);"><th style="padding:6px;">编号</th><th style="padding:6px;">赛事对阵</th><th style="padding:6px;">预测推荐</th><th style="padding:6px;">赛果</th><th style="padding:6px;">结果</th></tr></thead><tbody>{rows_html}</tbody></table><div style="background-color:rgba(56,189,248,0.05);padding:10px;border-radius:6px;border:1px solid rgba(56,189,248,0.2);font-size:12px;margin-top:12px;line-height:1.5;">🚀 <strong>模型自动进化报告 ({version})</strong><br/>• 历史总验证场次: <span style="color:#f1f5f9;font-weight:bold;">{total_validated} 场</span><br/>• 胜平负/方向命中率: <span style="color:#10b981;font-weight:bold;">{direction_acc * 100:.2f}%</span><br/>• 最可能比分命中率: <span style="color:#fbbf24;font-weight:bold;">{score_acc * 100:.2f}%</span></div><p style="font-size:11px;color:#64748b;text-align:center;margin-top:12px;margin-bottom:0;">💬 自动结算已部署 • <a href="https://victortang0.github.io/football-intelligence/" style="color:#00d4ff;text-decoration:none;">打开 MATCH IQ 看板 ➔</a></p></div>"""
    return send_push(f"💰 MATCH IQ 战绩结算及模型进化 ({version})", content)

def ensure_fresh_odds_update():
    """
    Guarantees that live odds from Sporttery API are fetched and predictions/Kelly EV are recalculated
    right before push notifications are generated and delivered.
    """
    try:
        import sys, subprocess
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        update_script = os.path.join(scripts_dir, "update_odds_and_news.py")
        if os.path.exists(update_script):
            print("🔄 [Push Pre-Flight Check] Running update_odds_and_news.py to ensure live odds & predictions are updated before push...")
            subprocess.run([sys.executable, update_script], check=True)
            return True
    except Exception as e:
        print(f"⚠️ Warning: Pre-push odds update failed: {e}")
    return False

def push_initial_predictions(matches):
    has_any = any(m.get("has_changed_in_push") or m.get("odds_water_changed") for m in matches)
    return push_scheduled_update(matches, has_any_change=has_any)

def push_live_change_alert(changed_matches):
    return push_scheduled_update(changed_matches, has_any_change=True)

def push_closing_summary(matches, is_pre_final=False):
    has_any = any(m.get("has_changed_in_push") or m.get("odds_water_changed") for m in matches)
    return push_scheduled_update(matches, has_any_change=has_any)

if __name__ == "__main__":
    import subprocess
    print("📲 Executing standalone push service pipeline (fetching live odds & pushing)...")
    ensure_fresh_odds_update()

