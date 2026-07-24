# Antigravity Project Custom Rules

This document outlines the custom development guidelines, UI aesthetic styling, and data deduction rules tailored for the Football Intelligence (Match IQ) platform. Antigravity agents on any workstation MUST strictly adhere to these rules upon workspace loading.

---

## 1. Interaction & System Communication Style
- **Concise Reporting**: Keep conversational responses highly summarized. Present exact data changes and analysis in structured tables/lists. Avoid redundant explanations or placeholder greetings.
- **Git Auto-Sync**: After updating any core file (e.g., frontend code, Python scripts, history database), always run `bash sync.sh` in the terminal to keep the GitHub repository fully synchronized.
- **Direct Execution**: Perform backend odds updates (`python3 scripts/update_odds_and_news.py`) and history synchronizations (`python3 scripts/sync_history.py`) asynchronously, and report status only after completion.

---

## 2. Core UI Layout & Specific Goals Bolding Rules
- **Goals Double-Color Palette**:
  - Main System recommendation: Blue (`#40a9ff`).
  - M10 System or Duplicate recommendation: Gold (`#ffd700`).
  - *No Global Truncation Merge*: Main system and M10 both allow up to 2 items. Merging allows displaying up to 3-4 entries on clash (e.g., `0[Blue], 2[Blue], 1[Gold]`).
- **History Bolding & Scaled Contrast**:
  - For completed matches, calculate the actual total goals.
  - **Hit Goal Sub-item**: Apply bold (`font-weight: 900`) and scale up (`font-size: 1.15em; display: inline-block;`). Do NOT alter its color (maintain its original Blue/Gold shade).
  - **Missed Goal Sub-items**: Scale down (`font-size: 0.88em; opacity: 0.8; display: inline-block;`) to generate an intuitive contrast layout.
  - **Pending Matches**: Keep all goal numbers at regular font sizes and weights.
- **Odd-Change Lamp Warnings**:
  - Apply `.live-change-lamp` pulsing light indicators directly inside summary tables for fields in `diff_markers` (HAD, Score, Goals, HF) when conclusions change post odds update.

---

## 3. Dynamic Blending: Wind Control & Main System Fusion
- Do not let users struggle between choosing the Main System vs the Wind Control Radar. Dynamically fuse them into the **Confidence Recommendation** box based on `upset_probability` (from `conclusions`):
  - **🟢 Safe Zone (Prob < 40%)**: Follow the mainstream basic outcome (high confidence = single choice, low = regular double choice).
  - **🟡 Moderate Risk Zone (40% <= Prob < 55%)**: Force downgrade the mainstream single outcome to a defensive double chance (e.g., `Home Win` -> `Home Win OR Draw`), appending the yellow `⚠️避险双选` label.
  - **🔴 High Danger Zone (Prob >= 55%)**: Disregard mainstream bias; let the Wind Control Upset Direction overwrite the primary prediction (e.g., forcing double chance in the upset direction), appending the rose `🚨雷达介入` badge.

---

## 4. Statistics & Sourcing Specifications
- **M10 Goals Precision KPI**:
  - The top bar "Goals Accuracy" card MUST calculate and reflect only the accuracy of the M10 golden goal recommendations.
  - Exclude any match where M10 did not trigger a specific goal prediction from both numerator and denominator.
- **Dynamic Handicap Line**:
  - Always extract handicap indexes directly from JcOfficial via `match.handicap_line`. Do NOT hardcode fixed lines (e.g., assuming -1). Keep signs (e.g., `+1` or `-1`) dynamically derived.
