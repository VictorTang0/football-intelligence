#!/bin/bash
# ============================================================
# MATCH IQ — Git Synchronization Script
# Commits and pushes changes to GitHub automatically
# ============================================================

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Check if there are changes to commit
if [[ -z $(git status -s) ]]; then
  echo "✨ [Match IQ Sync] 没有检测到文件更改，无需同步。"
  exit 0
fi

# Stage changes
git add data/ matches.json weights.json history.json model_evolution.json config.json 2>/dev/null
git add index.html css/ js/ 2>/dev/null

# Create commit message with current timestamp
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
COMMIT_MSG="update: 自动同步数据于 ${TIMESTAMP}"

git commit -m "${COMMIT_MSG}"

echo "🚀 [Match IQ Sync] 正在推送至 GitHub..."
git push origin main

if [ $? -eq 0 ]; then
  echo "✅ [Match IQ Sync] 同步成功！"
else
  echo "❌ [Match IQ Sync] 同步失败。请检查您的网络连接或 Git 凭证配置。"
  exit 1
fi
