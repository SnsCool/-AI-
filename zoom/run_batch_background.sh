#!/bin/bash
# Zoomバッチ処理をバックグラウンドで実行
#
# 使用方法:
#   ./run_batch_background.sh --from 2026-01-01 --to 2026-01-31 --reprocess
#   ./run_batch_background.sh --all-groups --reprocess
#
# ログ確認:
#   tail -f logs/batch_*.log
#
# プロセス確認:
#   ps aux | grep batch_zoom

cd "$(dirname "$0")"

# ログディレクトリ作成
mkdir -p logs

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/batch_background_$TIMESTAMP.log"

echo "バックグラウンドで実行開始..."
echo "ログファイル: $LOG_FILE"
echo "プロセス確認: ps aux | grep batch_zoom"
echo "ログ確認: tail -f $LOG_FILE"

# nohupでバックグラウンド実行
nohup ./run_batch.sh "$@" > "$LOG_FILE" 2>&1 &

PID=$!
echo "プロセスID: $PID"
echo ""
echo "実行中..."
sleep 3
tail -20 "$LOG_FILE"
