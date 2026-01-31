#!/bin/bash
#
# Notion日次同期スクリプト
# - Notionから差分を取得
# - 変更があればGitHubにpush
#
# 使用方法:
#   crontab -e
#   0 9 * * * /Users/hatakiyoto/-AI-egent-libvela/scripts/daily_notion_sync.sh >> /tmp/notion_sync.log 2>&1
#

set -e

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/notion_sync_$(date +%Y%m%d).log"

# 環境変数を読み込む
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

echo "======================================" | tee -a "$LOG_FILE"
echo "Notion日次同期: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

# Git最新化
echo "[Git] 最新化中..." | tee -a "$LOG_FILE"
git pull origin main 2>&1 | tee -a "$LOG_FILE" || true

# 同期実行
echo "[Sync] Notion同期を実行..." | tee -a "$LOG_FILE"
python3 scripts/sync_notion_mcp.py 2>&1 | tee -a "$LOG_FILE"

# 変更があるかチェック
if git diff --quiet && git diff --cached --quiet; then
    echo "[結果] 変更なし" | tee -a "$LOG_FILE"
else
    echo "[Git] 変更を検出、コミット＆プッシュ..." | tee -a "$LOG_FILE"

    # 変更をステージング
    git add notion_docs/
    git add .notion_sync_state.json 2>/dev/null || true

    # コミット
    COMMIT_MSG="sync: Notion日次同期 $(date '+%Y-%m-%d %H:%M')"
    git commit -m "$COMMIT_MSG

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>" 2>&1 | tee -a "$LOG_FILE"

    # プッシュ
    git push origin main 2>&1 | tee -a "$LOG_FILE"

    echo "[完了] GitHubにプッシュしました" | tee -a "$LOG_FILE"
fi

echo "======================================" | tee -a "$LOG_FILE"
echo "終了: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"
