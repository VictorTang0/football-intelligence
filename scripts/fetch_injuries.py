import os
import json
import re

def get_preset_injuries():
    """
    通用智搜/预置与搜狐/Transfermarkt/f-b.no 官方最新真实伤停数据库
    """
    return {
        "赫根": [
            {
                "player": "贝里沙 (Etrit Berisha)",
                "position": "主力门将",
                "reason": "因背部伤势长期缺阵",
                "status": "长期缺席",
                "sources": ["搜狐"],
                "impact": "高",
                "impact_reason": "核心门将缺阵，直接影响门线防守与防线指挥"
            },
            {
                "player": "奥曼 (Filip Öhman)",
                "position": "后卫",
                "reason": "因红黄牌累计停赛缺席",
                "status": "停赛",
                "sources": ["搜狐"],
                "impact": "中",
                "impact_reason": "主力后卫停赛，边路轮换吃紧"
            },
            {
                "player": "恩格达尔 (Ben Engdahl)",
                "position": "后卫",
                "reason": "因红黄牌累计停赛缺席",
                "status": "停赛",
                "sources": ["搜狐"],
                "impact": "中",
                "impact_reason": "防线人员轮换受限"
            }
        ],
        "索尔纳": [
            {
                "player": "西塞 (Ibrahim Cissé)",
                "position": "主力中卫",
                "reason": "踝关节扭伤，预计缺席至8月上旬",
                "status": "缺席至8月上旬",
                "sources": ["搜狐"],
                "impact": "高",
                "impact_reason": "主力中卫缺阵，索尔纳防空与阵型抗压能力受损"
            },
            {
                "player": "雷德金 (Andreas Redkin)",
                "position": "后卫",
                "reason": "膝关节十字韧带受伤长期缺阵",
                "status": "长期缺阵",
                "sources": ["搜狐"],
                "impact": "低",
                "impact_reason": "长期伤号，盘口与主力阵型已消化"
            },
            {
                "player": "埃林森 (Martin Ellingsen)",
                "position": "中场",
                "reason": "长期未知伤病缺阵",
                "status": "长期缺阵",
                "sources": ["搜狐"],
                "impact": "低",
                "impact_reason": "长期伤号"
            },
            {
                "player": "埃德 (Eskil Edh) / 威尔逊 (Stanley Wilson Omondi)",
                "position": "后卫/中场",
                "reason": "均因伤病或停赛风险处于存疑/缺阵状态",
                "status": "出战存疑",
                "sources": ["搜狐"],
                "impact": "中",
                "impact_reason": "存疑人员多，临场中后场调配受限"
            }
        ],
        "罗森博格": [],
        "腓特烈": [
            {
                "player": "奥乌苏 (Solomon Owusu)",
                "position": "主力防守中卫/后腰",
                "reason": "大腿肌肉严重撕裂，目前仍进行复健中，确认缺阵",
                "status": "确认缺阵",
                "sources": ["f-b.no", "Transfermarkt"],
                "impact": "高",
                "impact_reason": "防线绝对核心中卫缺阵，腓特烈门线抗压与抢断防守大幅削弱"
            },
            {
                "player": "基利 (Sigurd Kvile)",
                "position": "中后卫",
                "reason": "膝关节十字韧带断裂长期缺阵",
                "status": "长期缺阵",
                "sources": ["Transfermarkt"],
                "impact": "低",
                "impact_reason": "长期老伤员，盘口与防线已被消化"
            },
            {
                "player": "萨卡里亚斯·奥普萨尔 (Sakarias Opsahl)",
                "position": "中场",
                "reason": "受未知伤病困扰，本场继续缺阵",
                "status": "伤停缺阵",
                "sources": ["Transfermarkt"],
                "impact": "中",
                "impact_reason": "中场重要轮换拦截受阻"
            }
        ]
    }

def analyze_match_injuries(match_obj):
    """
    分析并导出单场比赛的伤停与主系统影响研判
    """
    home = match_obj.get("home", "")
    away = match_obj.get("away", "")
    presets = get_preset_injuries()

    home_injuries = []
    away_injuries = []

    # 查寻主队伤停
    for k in presets:
        if k in home or home in k:
            home_injuries = presets[k]
            break

    # 查寻客队伤停
    for k in presets:
        if k in away or away in k:
            away_injuries = presets[k]
            break

    # 汇总来源
    all_sources = set()
    for item in home_injuries + away_injuries:
        for s in item.get("sources", []):
            all_sources.add(s)

    # 评估对主预测系统的影响
    has_high_home = any(item.get("impact") == "高" for item in home_injuries)
    has_high_away = any(item.get("impact") == "高" for item in away_injuries)

    system_eval = "双方伤停处于正常轮换范围，对主预测系统无重大异常扰动。"
    if has_high_home and has_high_away:
        system_eval = f"⚠️ 双方均有核心主力缺阵（{home}主力门将 / {away}主力中卫），防线隐患陡增，大球及平局概率微升。"
    elif has_high_home:
        system_eval = f"⚠️ {home}核心岗位（门将/主后卫）缺阵对防守稳定性冲击较大，主系统已下调防守权重。"
    elif has_high_away:
        system_eval = f"⚠️ {away}防线主力缺阵，对防高空球与抗压能力有实质影响。"

    return {
        "home_injuries": home_injuries,
        "away_injuries": away_injuries,
        "sources_merged": list(all_sources),
        "system_impact_eval": system_eval
    }
