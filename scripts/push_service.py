# -*- coding: utf-8 -*-
import urllib.request
import json
import random

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
def sort_matches_by_date_and_code(matches_list):
    import re
    def sort_key(m):
        kickoff_date = (m.get("kickoff") or m.get("kickoff_time") or "").split("T")[0].split(" ")[0]
        num_str = m.get("match_no") or m.get("id") or ""
        num_match = re.search(r'\d+$', num_str)
        code = int(num_match.group(0)) if num_match else 999
        return (kickoff_date, code)
    return sorted(matches_list, key=sort_key)

def push_initial_predictions(matches):
    sorted_matches = sort_matches_by_date_and_code(matches)
    rows_html = ""
    for m in sorted_matches:
        match_no = m.get("match_no", "")
        league = m.get("league", "")
        home = m.get("home", "")
        away = m.get("away", "")
        uc = m.get("ultimate_conclusion", {})
        rec = uc.get("recommendation", "")
        score = uc.get("predicted_score", "")

        rows_html += f"""
        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <td style="padding: 6px; font-weight: bold; color: #94a3b8;">{match_no}</td>
          <td style="padding: 6px; color: #94a3b8;">{league}</td>
          <td style="padding: 6px; font-weight: bold;">{home} vs {away}</td>
          <td style="padding: 6px; color: #38bdf8;">{rec} <span style="font-size: 10px; color: #64748b;">({score})</span></td>
        </tr>
        """

    selected_quote = random.choice(LUCK_QUOTES)

    content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
      <h3 style="color: #38bdf8; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">🔮 今日初盘大盘汇总</h3>
      <p style="font-size: 12px; color: #94a3b8;">今日初盘多维结论已锁定，大盘概览如下：</p>
      
      <table style="width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11px; color: #e2e8f0; text-align: left;">
        <thead>
          <tr style="background-color: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
            <th style="padding: 6px; width: 12%;">编号</th>
            <th style="padding: 6px; width: 15%;">联赛</th>
            <th style="padding: 6px; width: 38%;">对阵</th>
            <th style="padding: 6px; width: 35%;">初盘预测结论</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>

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
    rows_html = ""
    for m in sorted_matches:
        match_no = m.get("match_no", "")
        home = m.get("home", "")
        away = m.get("away", "")
        kickoff = m.get("kickoff_time") or m.get("kickoff", "")
        if "T" in kickoff:
            kickoff = kickoff.split("T")[1][:5]
        
        baseline_rec = m.get("baseline_recommendation", "--").split("(")[0].strip()
        current_rec = m.get("current_recommendation", m.get("ultimate_conclusion", {}).get("recommendation", "--")).split("(")[0].strip()
        
        is_radar = m.get("radar_triggered", False)
        radar_badge = ' <span style="background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); padding: 1px 3px; border-radius: 3px; font-size: 9px;">雷达干预</span>' if is_radar else ''
        
        scores = m.get("current_scores", m.get("ultimate_conclusion", {}).get("predicted_score", "--"))
        goals = m.get("current_goals", m.get("conclusions", {}).get("over_under", "--"))
        odds_mov = m.get("odds_movement_str", "水位异动监测中")
        has_rec_changed = (baseline_rec != current_rec and baseline_rec != "--")

        rec_display = f'<span style="color: #38bdf8; font-weight: bold;">{current_rec}</span>'
        if has_rec_changed:
            rec_display = f'<span style="text-decoration: line-through; color: #64748b;">{baseline_rec}</span> ➔ <span style="color: #f43f5e; font-weight: bold; text-decoration: underline;">{current_rec}</span>'

        rows_html += f"""
        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <td style="padding: 6px; font-weight: bold; color: #94a3b8;">{match_no}</td>
          <td style="padding: 6px; font-weight: bold;">{home} vs {away}</td>
          <td style="padding: 6px; color: #38bdf8; font-size: 10px;">{kickoff}</td>
          <td style="padding: 6px;">{rec_display}{radar_badge}</td>
        </tr>
        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.02); background-color: rgba(255,255,255,0.01);">
          <td colspan="4" style="padding: 6px 12px; font-size: 11px; color: #94a3b8;">
            💧 <strong>水位异动</strong>: <span style="color: #fbbf24; font-family: monospace;">{odds_mov}</span><br/>
            🎯 <strong>当前结论比分</strong>: <span style="color: #10b981; font-weight: bold;">{scores}</span> | 进球数: <span style="color: #38bdf8;">{goals}</span>
          </td>
        </tr>
        """

    content = f"""
    <div style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid rgba(0, 212, 255, 0.2);">
      <h3 style="color: #f43f5e; margin-top: 0; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">💧 盘口水位异动与最新结论警报</h3>
      <p style="font-size: 12px; color: #94a3b8;">检测到竞彩/欧赔水位或结论异动，已为您同步以下变盘赛事：</p>
      
      <table style="width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11px; color: #e2e8f0; text-align: left;">
        <thead>
          <tr style="background-color: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
            <th style="padding: 6px; width: 12%;">编号</th>
            <th style="padding: 6px; width: 35%;">对阵双方</th>
            <th style="padding: 6px; width: 15%;">开赛</th>
            <th style="padding: 6px; width: 38%;">预测结论 (初盘 ➔ 最新)</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>

      <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 15px; margin-bottom: 0;">
        💬 水位与结论异动实时跟踪中 • <a href="https://victortang0.github.io/football-intelligence/" style="color: #00d4ff; text-decoration: none;">打开 MATCH IQ 看板 ➔</a>
      </p>
    </div>
    """
    return send_push("💧 MATCH IQ 水位变动与最新结论警报", content)

def push_closing_summary(matches, is_pre_final=False):
    sorted_matches = sort_matches_by_date_and_code(matches)
    rows_html = ""
    for m in sorted_matches:
        match_no = m.get("match_no", "")
        league = m.get("league", "")
        home = m.get("home", "")
        away = m.get("away", "")
        
        uc = m.get("ultimate_conclusion", {})
        baseline_rec = m.get("baseline_recommendation", "--").split("(")[0].strip()
        current_rec = uc.get("recommendation", "--").split("(")[0].strip()
        score = uc.get("predicted_score", "--")
        
        has_changed = (baseline_rec != current_rec and baseline_rec != "--")
        
        rec_display = current_rec
        if has_changed:
            rec_display = f"""<span style="text-decoration: line-through; color: #64748b; font-size: 9.5px;">{baseline_rec}</span> ➔ <span style="color: #f43f5e; font-weight: bold;">{current_rec}</span>"""

        rows_html += f"""
        <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <td style="padding: 6px; font-weight: bold; color: #94a3b8;">{match_no}</td>
          <td style="padding: 6px; color: #94a3b8;">{league}</td>
          <td style="padding: 6px; font-weight: bold;">{home} vs {away}</td>
          <td style="padding: 6px; color: #38bdf8;">{rec_display} <span style="font-size: 10px; color: #64748b;">({score})</span></td>
        </tr>
        """

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
      
      <table style="width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 11px; color: #e2e8f0; text-align: left;">
        <thead>
          <tr style="background-color: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
            <th style="padding: 6px; width: 12%;">编号</th>
            <th style="padding: 6px; width: 15%;">联赛</th>
            <th style="padding: 6px; width: 38%;">对阵</th>
            <th style="padding: 6px; width: 35%;">终盘预测结论</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>

      <div style="background-color: {footer_bg}; padding: 10px; border-radius: 6px; border: 1px solid {footer_border}; font-size: 13px; text-align: center; font-weight: bold; color: {footer_color}; margin-top: 15px;">
        {footer_text}
      </div>

      <p style="font-size: 11px; color: #64748b; text-align: center; margin-top: 15px; margin-bottom: 0;">
        💬 终盘结论已推送锁定 • <a href="https://victortang0.github.io/football-intelligence/" style="color: #00d4ff; text-decoration: none;">打开 MATCH IQ ➔</a>
      </p>
    </div>
    """
    return send_push(email_title, content)
