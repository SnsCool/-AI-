#!/bin/bash
# Zoomバッチ処理実行スクリプト
#
# 使用方法:
#   ./run_batch.sh                     # 全件処理
#   ./run_batch.sh --group 1           # グループ1のみ
#   ./run_batch.sh --from 2026-01-01 --to 2026-01-31  # 日付指定
#   ./run_batch.sh --all-groups        # 全グループを順次実行

set -e

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# 仮想環境を有効化
source ../.venv/bin/activate

# デフォルト値
FROM_DATE=""
TO_DATE=""
GROUP=""
ALL_GROUPS=false
REPROCESS=false
DRY_RUN=false

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --from)
            FROM_DATE="$2"
            shift 2
            ;;
        --to)
            TO_DATE="$2"
            shift 2
            ;;
        --group)
            GROUP="$2"
            shift 2
            ;;
        --all-groups)
            ALL_GROUPS=true
            shift
            ;;
        --reprocess)
            REPROCESS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "不明なオプション: $1"
            exit 1
            ;;
    esac
done

# ログファイル
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/batch_$TIMESTAMP.log"

# コマンド構築
CMD="python -u batch_zoom.py"

if [ -n "$FROM_DATE" ]; then
    CMD="$CMD --from-date $FROM_DATE"
fi

if [ -n "$TO_DATE" ]; then
    CMD="$CMD --to-date $TO_DATE"
fi

if [ "$REPROCESS" = true ]; then
    CMD="$CMD --reprocess"
fi

if [ "$DRY_RUN" = true ]; then
    CMD="$CMD --dry-run"
fi

# 全グループ順次実行
if [ "$ALL_GROUPS" = true ]; then
    echo "=== 全グループ順次実行開始 ===" | tee -a "$LOG_FILE"
    echo "ログファイル: $LOG_FILE"

    for i in 1 2 3 4 5 6; do
        echo "" | tee -a "$LOG_FILE"
        echo "=== グループ $i/6 開始: $(date) ===" | tee -a "$LOG_FILE"

        GROUP_CMD="$CMD --group $i --all"
        echo "実行: $GROUP_CMD" | tee -a "$LOG_FILE"

        # nohupで実行（エラーでも継続）
        $GROUP_CMD 2>&1 | tee -a "$LOG_FILE" || {
            echo "グループ $i でエラー発生、次のグループへ継続" | tee -a "$LOG_FILE"
        }

        echo "=== グループ $i/6 完了: $(date) ===" | tee -a "$LOG_FILE"

        # 次のグループの前に少し待機（API制限対策）
        if [ $i -lt 6 ]; then
            echo "10秒待機..." | tee -a "$LOG_FILE"
            sleep 10
        fi
    done

    echo "" | tee -a "$LOG_FILE"
    echo "=== 全グループ処理完了: $(date) ===" | tee -a "$LOG_FILE"
    exit 0
fi

# 単一グループまたは全件実行
if [ -n "$GROUP" ]; then
    CMD="$CMD --group $GROUP"
fi

CMD="$CMD --all"

echo "=== バッチ処理開始: $(date) ===" | tee "$LOG_FILE"
echo "実行: $CMD" | tee -a "$LOG_FILE"
echo "ログファイル: $LOG_FILE"

# 実行
$CMD 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== バッチ処理完了: $(date) ===" | tee -a "$LOG_FILE"
