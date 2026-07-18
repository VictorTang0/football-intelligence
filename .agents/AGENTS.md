# Match IQ Customization Rules

## 1. 今日预测和更新盘口工作流规范

在执行以下两项核心工作流时，分析师模型必须包含检索更新最新的新闻、社媒预测、大众情绪与舆论消息：
1. **今日预测工作流 (分析今日赛事 / Command A)**
2. **更新盘口工作流 (更新今日盘口 / Command B)**

### 🧱 赛事标准化录入要求（防呆机制）：
- **禁止手动裸写骨架**：在 Command A 识别出新赛事后，**严禁**手动拼装不完整或缺少 `team_stats/season_stats` 等庞大树状字段的 JSON 骨架直接写入 `matches.json`。
- **全自动联运流程**：已将所有初始化与数据抓取操作合并为单主脚本。运行 `python3 scripts/analyze_today_matches.py` 会自动依次执行：抓取最新竞彩在售对阵 -> 擦除旧 pending 缓存 -> 骨架多维初始化 -> 运行盘口更新及新闻舆情研判。这一键工作流彻底规避了手工合并错漏或操作顺序颠倒导致的空白错误。

### 🔍 情报检索与更新标准：
- **已验证新闻 (`intelligence.verified_news`)**：
  - 使用搜索引擎主动检索各场比赛双方的最新的主帅采访、伤停调整、战术倾斜等资讯。
  - 填入 2 条及以上最近 24 小时内已证实的权威报道，包括标题、来源、正面/负面影响评估（`impact`）与验证标记（`verified: true`）。
  - **伤停推演高权重优先**：伤停新闻对核心战斗力影响极大，任何关于核心球员（主力射手、防守铁闸、首发门将）的缺阵、复出，必须作为推理和结论生成的首要权重依据，在 `ultimate_conclusion.reasoning` 中予以重点推演。
- **社媒预测与舆论讨论 (`intelligence.social_buzz`)**：
  - 检索社交平台和论坛上球迷对本场对决的舆论动向与情绪走向。
  - 提炼大众当前热议的核心话题（`notable_discussion`）、当前主要情绪倾向（`sentiment`，如盲目乐观、悲观防冷、分歧剧烈等），以及 trending keywords 热词标记。
- **媒体与算法模型预测 (`intelligence.media_predictions`)**：
  - 搜集主流足球媒体（The Athletic, ESPN）或分析模型（Opta, WhoScored）公布的倾向预测及最可能比分。
- **环境变量 (`weather_impact` / `venue_notes`)**：
  - 获取比赛当天的天气温湿度（尤其是雨雪、高温）以及场地相关信息（如主客场球迷占比、旅行疲劳等）。

### ⏱️ 双阶段情报热更新规范 (Double-Stage Update Workflow)
在赛事推送与临场跟进时，情报富化更新遵循以下分工：
1. **初始分析阶段 (Command A - 赛前 24~48 小时)**：
   - 必须优先拉取并初始化**已验证新闻 (`verified_news`)**和**媒体与算法预测 (`media_predictions`)**（如 Opta、WhoScored 的分值）。此时由于舆情尚在发酵，社媒热议可先初始化为空白。
2. **临场盘口更新阶段 (Command B - 赛前 2~4 小时)**：
   - 必须重点更新即时水位变动、**社媒预测与讨论舆情 (`social_buzz`)**以及**最新舆情倾向 (`sentiment`)**。利用球迷对突发伤停和最终首发的即时讨论反馈，反推庄家大单赔付倾斜和临场诱导陷阱。

### 🧠 决策进化与盘口修正机制：
1. 将检索到的情报结构化写入 `matches.json` 中对应赛事的 `intelligence` 部分。
2. 结合大众情绪和热议点，重新核对**“庄家意图推演 (`bookmaker_intent`)”**和**“烟雾弹避险 (`smoke_screens`)”**，研判庄家是否利用大众舆论进行资金诱导或制造题材陷阱。
3. 若新情报与舆论变化改变了原有的分析面，立即修正 `ultimate_conclusion.recommendation`，并将比赛卡片的 `prediction_updated` 属性设为 `true`，以在界面上显示“预测更新”徽章。

## 2. 赛后权重进化工作流默认指代规范

当用户发送 **“更新赛果并进化模型”** 时，系统与分析师模型在执行该工作流时必须遵循以下默认约定：
- **默认指代范围**：默认针对**“今日对决（Ultimate Card）中当前处于待验证状态（`status = "pending"`）的各场赛事”**进行赛果更新、反向传播权重微调、球队标签核销与模型进化。
- **免予核销机制**：对于最终未正常开赛的延期、取消赛事，在核销赛果时必须显式标注其在 `results` 中的状态为 `postponed`，并跳过标签库更新与模型准确率核销（串关 Leg 以赔率 1.0 免责退水处理）。

## 3. v2.0 决策推理链与预测推演规范

在执行 **“今日预测工作流 (Command A)”** 生成赛事预测结论时，分析师模型必须强制运行以下升级版决策链：
1. **联赛特征对齐 (League Profile Alignment)**：
   - 必须读取 `data/league_profiles.json`，核对当前赛事所属联赛的标签和特征（如：韩职的低转化与平局多、瑞超的人工草皮差异等）。
   - 在 `ultimate_conclusion.reasoning`（终极结论推演）中，必须明文体现这些联赛特征对本次战局的战术预判（例如：“结合韩职特有的低转换平局多特征…”）。
2. **战意分差修正 (Motivation Discrepancy Correction)**：
   - 核实 `team_stats` 中两队所处的积分榜形势，更新 `motivation`（战意指数，0.0 - 1.0）与 `motivation_note`。
   - 如果发生显著战意分差（如：保级队 100% vs 中游队 40%），必须在 `reasoning` 中推演强队可能存在的“无忧虑放水”或战意松懈逻辑，并下调其基本面净实力得分。
3. **资金盘口异常探测 (Kelly & Odds Trap Alert)**：
   - 对比 `config.json` 中的 `odds_trap_threshold` 与 `odds_protect_threshold` 临界值。
   - 如果 Worst Risk 的变盘差值 `worst_diff` 触发了已校准的阈值，必须在 `reasoning` 中显式指出并分析这是“庄家降水保护”还是“庄家升水诱买”，以此调整终极结论。
4. **高信心结论聚焦**：
   - 如果经过推演，主推方向信心极稳且 Confidence >= 80%：
     - 若确定没有明显的爆冷路径和高价值的激进方案，必须在 conclusions 中将 `upset` 设为 `""` 或 `"无明显爆冷路径"`，将 `aggressive` 设为 `""` 或 `"无额外激进方案"`，以便前端 UI 自动渲染虚线槽位。

