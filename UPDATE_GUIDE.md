# MATCH IQ — 操作手册

## 快速开始

### 本地预览
```bash
cd football-intelligence
npx serve .         # 方法1（推荐）
# 或
python -m http.server 8080  # 方法2
# 然后打开 http://localhost:8080
```

> ⚠ 直接双击打开 index.html（file://）时，由于浏览器安全限制，JSON数据无法加载。请务必通过 HTTP 服务器访问。

### GitHub → Cloudflare Pages 部署
1. 将 `football-intelligence/` 文件夹作为 GitHub 仓库根目录
2. Cloudflare Pages → 新建项目 → 连接仓库 → **框架预设选"None"**
3. 构建命令留空，输出目录填 `/`

---

## 更新命令一览

### 🔴 命令 A：分析新赛事（最常用）
**使用场景**：有新的赛程需要分析时

```
发送给 AI：
[上传赛程截图] + "分析今日赛事"
```

**AI 将自动执行**：
1. OCR 识别图片中所有比赛（主客队 / 时间 / 联赛）
2. 抓取历史未验证赛果 → 计算预测误差 → 自动优化权重
3. 逐场抓取双方本赛季数据（365scores / footballant）
4. 抓取三家公司欧赔 + 亚盘（初盘 + 即时盘）
5. 全网搜索：新闻 / 社媒 / 媒体预测 / 天气 / 场地
6. 运行41项决策因子模型 → 生成完整分析
7. 输出所有 JSON 文件内容

**你的操作**：
```bash
# 将 AI 输出的 JSON 内容覆盖到对应文件，然后：
git add data/
git commit -m "update: $(date '+%Y-%m-%d') 赛事分析"
git push
# Cloudflare 自动部署，约 1-2 分钟后生效
```

---

### 🟡 命令 B：更新盘口数据
**使用场景**：临近开赛前（建议开赛前 2 小时执行）

```
发送给 AI：
"更新今日盘口"
或
"更新 [主队 vs 客队] 盘口"
```

**AI 将更新**：`matches.json` 中各场比赛的 `odds_analysis` 部分

---

### 🟢 命令 C：赛后权重进化（核心功能）
**使用场景**：比赛全部结束后（建议第二天执行）

```
发送给 AI：
"更新赛果并进化模型"
```

**AI 将自动执行**：
1. 抓取所有未验证比赛的最终赛果
2. 对比各项预测结论（胜负 / 比分 / 大小球 / 半全场）
3. 计算各决策因子的预测贡献误差
4. 贝叶斯梯度优化：误差大的因子降权，准确的升权
5. 归一化确保总权重 = 100%
6. 输出更新后的 `weights.json` + `history.json` + `model_evolution.json`

---

### 🔵 命令 D：单场/单队查询
```
"查询 [队名] 近期数据"
"分析 [主队 vs 客队] 的盘口走向"
"搜索 [队名] 今日最新新闻"
"重新生成 [比赛ID] 的结论"
```

---

## 文件更新频率参考

| 文件 | 更新频率 | 触发命令 |
|------|---------|---------|
| `data/matches.json` | 每次分析新赛事 | 命令 A |
| `data/weights.json` | 每次赛后进化 | 命令 C |
| `data/history.json` | 每次赛后进化 | 命令 C |
| `data/model_evolution.json` | 每次赛后进化 | 命令 C |
| `data/config.json` | 极少（人工修改） | 手动 |

---

## JSON 文件格式说明

### matches.json
根节点：
- `is_demo` (bool)：true = 演示数据，false = 真实数据
- `generated_at`：生成时间
- `model_version`：使用的模型版本
- `matches`：比赛数组

每场比赛关键字段：
- `ultimate_conclusion`：终极结论（顶部显示）
- `odds_analysis`：赔率分析（含烟雾弹、庄家意图）
- `intelligence`：情报（新闻/社媒/媒体预测）
- `public_vs_bookmaker`：散户vs庄家对比表
- `conclusions`：四种结论（主流/冷门/激进/信心）

### weights.json
- `version`：当前版本号（如 v1.3）
- `factors`：41个决策因子，每个包含 `weight`（当前权重）和 `delta`（本次变动）

### model_evolution.json
- `snapshots`：每次进化的快照数组，包含进化前后权重对比

---

## 常见问题

**Q：网站数据没有更新？**
A：确认已 `git push`，等待 1-2 分钟后强制刷新页面（Ctrl+Shift+R）

**Q：本地双击 index.html 打不开数据？**
A：需要 HTTP 服务器。运行 `npx serve .` 后通过 localhost 访问

**Q：AI 分析完如何更新多个文件？**
A：AI 会依次输出每个 JSON 文件的完整内容，你逐一复制并覆盖对应文件即可

**Q：进化后权重变化很小？**
A：正常。学习率初始为 0.05，随验证场次增加逐步降低，防止过拟合。需要积累足够场次才能看到显著变化。
