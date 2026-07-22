---
name: dynamic-score-inference
description: Mandatory rule and workflow protocol forbidding any static hardcoding of match scores, half-full time results, or flatlined confidence levels. All predicted scorelines (most_likely_score / predicted_score), half-full combinations (half_full), and confidence levels (confidence) must be dynamically deduced using bivariate Poisson regression over M01-M10 factor scores, team expected goals (EG), weather, and live Sporttery CRS hot scores whenever any match condition, odds, or team stats change.
---

# Dynamic Score & Half-Full Inference Protocol (无静态比分硬编码规范)

## 核心原则 (Golden Rule)
**绝对禁止在任何脚本、推演模块、兜底分支或总结渲染中对比赛比分（`predicted_score` / `most_likely_score`）、半全场（`half_full`）或置信度（`confidence`）进行任何形式的静态硬编码（如一律赋分 "3-0" / "0-3" 或硬编码 "85%" 置信度）。**

无论比赛属于何种类型（包括但不限于：基本面实力悬殊的强队交锋、深盘碾压局、冷门防范局、平局拉锯局），比分与半全场预测都必须作为**多维数据动态推演的科学产物**。

---

## 1. 动态比分推演算子 (Dynamic Score Inference Operator)

比分预测必须由 **双变量泊松回归（Bivariate Poisson Expected Goals Model）** 结合 M01-M10 因子评分与即时盘口动态计算：

### 1.1 期望进球数（$\text{EG}_{\text{home}}$ 与 $\text{EG}_{\text{away}}$）计算公式
1. **基础攻防效能（Standings & Team Stats）**：
   $$\text{EG}_{\text{home\_base}} = \frac{\text{主队场均进球} + \text{客队场均失球}}{2.0}$$
   $$\text{EG}_{\text{away\_base}} = \frac{\text{客队场均进球} + \text{主队场均失球}}{2.0}$$

2. **近期状态与动能微调（M03 Form Impact）**：
   $$\text{EG}_{\text{home}} += (\text{主队近5场胜场数} - \text{主队近5场负场数}) \times 0.04$$
   $$\text{EG}_{\text{away}} += (\text{客队近5场胜场数} - \text{客队近5场负场数}) \times 0.04$$

3. **环境与气候制约（M07 Weather Impact）**：
   若球场降雨或降雪（如雷阵雨、大雨）：
   $$\text{EG}_{\text{home}} \leftarrow \text{EG}_{\text{home}} \times 0.85, \quad \text{EG}_{\text{away}} \leftarrow \text{EG}_{\text{away}} \times 0.85$$

4. **MoE 专家模型方向修正（MoE Score Integration）**：
   若推荐方向为强队胜出（`is_strong_favorite`）：
   $$\text{EG}_{\text{home}} = \max(\text{EG}_{\text{home}}, \text{EG}_{\text{away}} + 1.2)$$
   若推荐方向为强队客胜（`is_away_strong_favorite`）：
   $$\text{EG}_{\text{away}} = \max(\text{EG}_{\text{away}}, \text{EG}_{\text{home}} + 1.2)$$

### 1.2 比分推演输出规则
* **禁止输出单一硬编码比分**：比分必须输出为最可能打出的前 2~3 个概率梯度（如 `2-0`, `3-0`, `3-1` 或 `0-2`, `0-1`），并附带体彩官方 CRS 热度指示（`竞彩首选`）。
* **格式统一**：`m["conclusions"]["most_likely_score"]` 与 `m["ultimate_conclusion"]["predicted_score"]` 必须全流程保持 **100% 强一致**，严禁不同字段输出互相冲突的比分。

---

## 2. 半全场推演算子 (Half-Full Time Inference Operator)

半全场结果（`half_full`）必须根据上半场与全场期望进球数（$\text{EG}_{\text{HT}}, \text{EG}_{\text{FT}}$）进行动态推导：
- 若 $\text{EG}_{\text{home}} \gg \text{EG}_{\text{away}}$（主队强优势）：推演 `胜/胜`, `平/胜`
- 若 $\text{EG}_{\text{away}} \gg \text{EG}_{\text{home}}$（客队强优势）：推演 `负/负`, `平/负`
- 若双方势均力敌且期望总进球 $< 2.2$：推演 `平/平`, `平/胜` 或 `平/负`
- 结合竞彩官方半全场投注比例（`sporttery_hot_hafu`）动态标记首选。

---

## 3. 动态置信度算子 (Dynamic Confidence Operator)

- 严禁对任何预测赋予固定硬编码置信度（如一律赋分 `85%`）。
- 置信度必须由 MoE 专家共识度、凯利方差、爆冷风险及强队硬实力分差做**连续函数拟合**：
  $$\text{Confidence} = 48 + \text{int}(|\text{MoE Score}| \times 40)$$
  - 极高风险/爆冷防范局：置信度进行折扣缩减（如 `36%` ~ `52%`）。
  - 实力与交锋绝对碾压局：置信度动态区间限制在 `76%` ~ `88%`，根据 MoE 共识度呈现阶梯差，严禁一刀切。

---

## 4. 自动化对账与防硬编码检测 (Audit Workflow)

在运行 `python3 scripts/update_odds_and_news.py` 或 `analyze_today_matches.py` 后，必须执行自动化检测：
1. 检查所有待预测赛事的 `predicted_score` 是否与 `most_likely_score` 100% 相同。
2. 检查是否存在 3 场以上赛事出现完全相同的比分文本与完全相同的置信度数字。若触发，自动拦截并告警。
