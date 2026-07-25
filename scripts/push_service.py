# -*- coding: utf-8 -*-
import urllib.request
import json
import random
import re

PUSHPLUS_TOKEN = "960491d71cdb4ce8b10b5a7de29ac5e6"

LUCK_QUOTES = [
    "好运只偏爱有准备的头脑，祝今天旗开得胜！🎲✨",
    "筹码在手，天下我有，祝今日红单连连！💰🔥",
    "借东风，迎财神，愿今天好运常伴你左右！🍀🏮",
    "冷静博弈，理智前行，好运自然水到渠成！🎯💼",
    "搏一搏，单车变摩托；祝今日大红大紫，福星高照！🏍️🚀",
    "财富的密码已经开启，愿你的选择今天能得到运气的拥抱！🔑💎",
    "量化数据为底，财神眷顾在旁，祝今天一红到底！📊📈"
]

def send_push(title, content):
    url = "http://www.pushplus.plus/send"
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
        kickoff_date = (m.get("kickoff") or m.get("kickoff_time") or "").split("T")[0].split(" ")[0]
        num_str = m.get("match_no") or m.get("id") or ""
        num_match = re.search(r'\d+$', num_str)
        code = int(num_match.group(0)) if num_match else 999
        return (kickoff_date, code)
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

    sp_val = c.get("hhad_sp", "") or lh.get("current", {}).get("draw", "")
    sp_str = f' <span style="color: #64748b; font-size: 10.5px;">[SP: {sp_val}]</span>' if sp_val else ''

    return f"让球({hc_label}): <span style='color: #38bdf8; font-weight: bold;'>{hhad_rec}</span>{sp_str}"

def format_goals_formatted_html(m):
    c = m.get("conclusions", {})
    uc = m.get("ultimate_conclusion", {})
    score_str = c.get("most_likely_score") or uc.get("predicted_score", "")
    
    # 1. 主系统具体进球数 p_goals (最多 2 个)
    p_goals = []
    matches_p = re.findall(r'\d+[:\-]\d+', score_str)
    if matches_p:
        for s in matches_p:
            parts = re.split(r'[:\-]', s)
            p_goals.append(int(parts[0]) + int(parts[1]))
        p_goals = sorted(list(set(p_goals)))[:2]
        
    # 2. M10 系统具体进球数 m_goals (不限限制，变盘热度推演)
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
        return f'<span style="color: #38bdf8; font-weight: bold;">({goals_raw})</span>'

    # 对齐 render.js 逻辑：仅主系统 -> 天蓝 #38bdf8；M10/双核重合 -> 金黄 #fbbf24
    items_html = []
    for g in combined:
        in_m = (g in m_goals)
        if in_m:
            items_html.append(f'<span style="color: #fbbf24; font-weight: bold; font-size: 13px;">{g}</span>')
        else:
            items_html.append(f'<span style="color: #38bdf8; font-weight: bold; font-size: 13px;">{g}</span>')

    return "(" + "、".join(items_html) + ")"

def render_match_card_html(m):
    match_no = m.get("match_no") or m.get("id", "").split("_")[-1]
    home = m.get("home", "")
    away = m.get("away", "")
    kickoff = m.get("kickoff_time") or m.get("kickoff", "")
    if "T" in kickoff:
        kickoff = kickoff.split("T")[1][:5]
    elif " " in kickoff:
        parts = kickoff.split(" ")
        if len(parts) > 1:
            kickoff = parts[1][:5]

    uc = m.get("ultimate_conclusion", {})
    c = m.get("conclusions", {})

    baseline_rec = m.get("baseline_recommendation", "--")
    current_rec = m.get("current_recommendation") or uc.get("recommendation", "--")
    
    # 格式化胜平负推荐结论（带 (竞彩) 标识）
    if "(竞彩" not in current_rec and "竞彩" in uc.get("primary_bet", ""):
        current_rec += " (竞彩)"
    if "(竞彩" not in current_rec and "不败" in current_rec:
        current_rec += " (竞彩)"

    # 让球加减球与结论 HTML
    handicap_html = get_handicap_info_html(m)

    # 信心级别与风险标签
    conf = uc.get("confidence", 60)
    conf_class = "color: #10b981; font-weight: bold;" if conf >= 75 else "color: #fbbf24; font-weight: bold;"
    cold_tag = "反基本面冷门" if "反基本面冷门" in current_rec else "主力资金指向"

    # 雷达 Badge
    is_radar = m.get("radar_triggered") or c.get("had_hhad_divergence", False)
    radar_badge = ' <span style="background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); padding: 1px 4px; border-radius: 3px; font-size: 9.5px;">雷达干预</span>' if is_radar else ''

    # 变盘展示
    has_rec_changed = (baseline_rec != current_rec and baseline_rec != "--")
    if has_rec_changed:
        rec_display = f'<span style="text-decoration: line-through; color: #64748b; font-size: 11px;">{baseline_rec}</span> ➔ <span style="color: #f43f5e; font-weight: bold; text-decoration: underline; font-size: 13.5px;">{current_rec}</span>'
    else:
        rec_display = f'<span style="color: #38bdf8; font-weight: bold; font-size: 13.5px;">{current_rec}</span>'

    # 比分、双色进球数（主系统天蓝 / M10与双核金黄）与半全场
    scores = m.get("current_scores") or uc.get("predicted_score") or c.get("most_likely_score", "--")
    goals_html = format_goals_formatted_html(m)
    hf = c.get("half_full", "--")

    # 水位变动通栏
    odds_mov = m.get("odds_movement_str", "")
    water_row_html = ""
    if odds_mov:
        water_row_html = f'''
        <div style="background-color: rgba(56, 189, 248, 0.03); padding: 8px 10px; font-size: 11.5px; color: #94a3b8; border-bottom: 1px solid rgba(255, 255, 255, 0.05); font-family: monospace;">
          💧 <strong>水位异动</strong>: <span style="color: #fbbf24; font-weight: bold;">{odds_mov}</span>
        </div>
        '''

    return f'''
    <div style="background-color: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; margin-bottom: 14px; overflow: hidden;">
      <div style="display: flex; border-bottom: 1px solid rgba(255, 255, 255, 0.06);">
        <div style="width: 38%; background-color: rgba(255, 255, 255, 0.03); padding: 12px 8px; display: flex; flex-direction: column; justify-content: center; border-right: 1px solid rgba(255, 255, 255, 0.06);">
          <div style="font-size: 11px; color: #94a3b8; font-weight: bold; margin-bottom: 4px;">{match_no} • {kickoff}</div>
          <div style="font-size: 14.5px; font-weight: bold; color: #ffffff; line-height: 1.3;">{home}</div>
          <div style="font-size: 10px; color: #64748b; margin: 2px 0;">VS</div>
          <div style="font-size: 14.5px; font-weight: bold; color: #ffffff; line-height: 1.3;">{away}</div>
        </div>
        <div style="width: 62%; padding: 10px 12px; font-size: 12.5px; display: flex; flex-direction: column; gap: 5px;">
          <div>{rec_display}{radar_badge}</div>
          <div style="color: #cbd5e1; font-size: 12px;">{handicap_html}</div>
          <div style="font-size: 11px; color: #94a3b8;">信心: <span style="{conf_class}">{conf}%</span> | {cold_tag}</div>
        </div>
      </div>
      {water_row_html}
      <div style="padding: 10px 12px; font-size: 12px; background-color: rgba(0, 0, 0, 0.15); display: flex; flex-direction: column; gap: 5px;">
        <div style="color: #f1f5f9; font-size: 12.5px;">🎯 <strong>最可能比分</strong>: <span style="color: #10b981; font-weight: bold; font-size: 13px;">{scores}</span></div>
        <div style="color: #94a3b8; font-size: 12px;">⚽ <strong>具体进球数</strong>: {goals_html} | <strong>半全场</strong>: <span style="color: #a855f7; font-weight: bold; font-size: 12.5px;">{hf}</span></div>
      </div>
    </div>
    '''

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
        rec = r.get("recommendation", "")
        score = r.get("score", "")
        is_correct = r.get("is_correct", False)
        actual = r.get("actual_result", "")

        status_html = '<span style="color: #10b981; font-weight: bold;">红 📈</span>' if is_correct else '<span style="color: #94a3b8;">黑 📉</span>'
        rows_html += f"""
        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <td style="padding: 6px; font-weight: bold; color: #94a3b8;">{match_no}</td>
          <td style="padding: 6px;">{home} vs {away}</td>
          <td style="padding: 6px; color: #38bdf8;">{rec} <span style="font-size: 10px; color: #64748b;">({score})</span></td>
          <td style="padding: 6px; font-family: monospace;">{actual}</td>
          <td style="padding: 6px;">{status_html}</td>
        </tr>
        """

    content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
      <h3 style="color: #10b981; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">💰 MATCH IQ 昨日红黑清算单</h3>
      <p style="font-size: 12px; color: #94a3b8;">昨日已完赛赛事预测结算列表：</p>
      
      <table style="width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11px; color: #e2e8f0; text-align: left;">
        <thead>
          <tr style="background-color: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
            <th style="padding: 6px;">编号</th>
            <th style="padding: 6px;">赛事对阵</th>
            <th style="padding: 6px;">预测推荐</th>
            <th style="padding: 6px;">赛果</th>
            <th style="padding: 6px;">结果</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>

      <div style="background-color: rgba(56, 189, 248, 0.05); padding: 12px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.2); font-size: 12px; margin-top: 15px; line-height: 1.5;">
        🚀 <strong>模型自动进化报告 ({version})</strong><br/>
        • 历史总验证场次: <span style="color: #f1f5f9; font-weight: bold;">{total_validated} 场</span><br/>
        • 胜平负/方向命中率: <span style="color: #10b981; font-weight: bold;">{direction_acc * 100:.2f}%</span><br/>
        • 最可能比分命中率: <span style="color: #fbbf24; font-weight: bold;">{score_acc * 100:.2f}%</span>
      </div>
      
      <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 15px; margin-bottom: 0;">
        💬 自动结算已部署 • <a href="https://victortang0.github.io/football-intelligence/" style="color: #00d4ff; text-decoration: none;">打开 MATCH IQ 看板 ➔</a>
      </p>
    </div>
    """
    return send_push(f"💰 MATCH IQ 战绩结算及模型进化 ({version})", content)

def push_initial_predictions(matches):
    sorted_matches = sort_matches_by_date_and_code(matches)
    cards_html = "".join([render_match_card_html(m) for m in sorted_matches])
    selected_quote = random.choice(LUCK_QUOTES)

    content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
      <h3 style="color: #38bdf8; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">🔮 今日初盘大盘汇总</h3>
      <p style="font-size: 12px; color: #94a3b8;">今日初盘多维结论已锁定，大盘概览如下：</p>
      
      {cards_html}

      <div style="background-color: rgba(56, 189, 248, 0.05); padding: 10px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.2); font-size: 13px; text-align: center; font-weight: bold; color: #38bdf8; margin-top: 15px;">
        {selected_quote}
      </div>

      <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 15px; margin-bottom: 0;">
        💬 今日数据监控中 • <a href="https://victortang0.github.io/football-intelligence/" style="color: #00d4ff; text-decoration: none;">打开 MATCH IQ 看板 ➔</a>
      </p>
    </div>
    """
    return send_push("🔮 MATCH IQ 今日初盘锁定大表", content)

def push_live_change_alert(changed_matches):
    sorted_matches = sort_matches_by_date_and_code(changed_matches)
    cards_html = "".join([render_match_card_html(m) for m in sorted_matches])

    content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
      <h3 style="color: #f43f5e; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">💧 盘口水位异动与最新结论警报</h3>
      <p style="font-size: 12px; color: #94a3b8;">检测到竞彩/欧赔水位或结论异动，已为您同步以下变盘赛事：</p>
      
      {cards_html}

      <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 15px; margin-bottom: 0;">
        💬 水位与结论异动实时跟踪中 • <a href="https://victortang0.github.io/football-intelligence/" style="color: #00d4ff; text-decoration: none;">打开 MATCH IQ 看板 ➔</a>
      </p>
    </div>
    """
    return send_push("💧 MATCH IQ 水位变动与最新结论警报", content)

def push_closing_summary(matches, is_pre_final=False):
    sorted_matches = sort_matches_by_date_and_code(matches)
    cards_html = "".join([render_match_card_html(m) for m in sorted_matches])

    if is_pre_final:
        footer_text = "离今日结束还有一小时，祝顺利。⏳⚽💪"
        footer_bg = "rgba(251, 191, 36, 0.05)"
        footer_border = "rgba(251, 191, 36, 0.2)"
        footer_color = "#fbbf24"
        title_tag = "⏳ 临场最终倒计时监控"
        email_title = "⏳ MATCH IQ 终盘前半小时总结"
    else:
        footer_text = "今日盘口跟踪已结束，祝红。🍀🎯🔥"
        footer_bg = "rgba(16, 185, 129, 0.05)"
        footer_border = "rgba(16, 185, 129, 0.2)"
        footer_color = "#10b981"
        title_tag = "🏁 今日终盘汇总锁定"
        email_title = "🏁 MATCH IQ 今日终盘总结"

    content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
      <h3 style="color: {footer_color}; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">{title_tag}</h3>
      <p style="font-size: 12px; color: #94a3b8;">今日全部预测赛事的终盘汇总大盘如下：</p>
      
      {cards_html}

      <div style="background-color: {footer_bg}; padding: 10px; border-radius: 6px; border: 1px solid {footer_border}; font-size: 13px; text-align: center; font-weight: bold; color: {footer_color}; margin-top: 15px;">
        {footer_text}
      </div>

      <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 15px; margin-bottom: 0;">
        💬 终盘结论已推送锁定 • <a href="https://victortang0.github.io/football-intelligence/" style="color: #00d4ff; text-decoration: none;">打开 MATCH IQ ➔</a>
      </p>
    </div>
    """
    return send_push(email_title, content)
