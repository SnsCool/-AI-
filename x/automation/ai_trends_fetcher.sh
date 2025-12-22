#!/bin/bash

# AI関連投稿取得スクリプト
# 毎日14:00に実行される

# 設定
# .envがあれば読み込み（APIFY_API_KEYなどの秘密情報を含める）
if [ -f ".env" ]; then
  # shellcheck disable=SC1091
  set -a
  . ".env"
  set +a
fi

: "${APIFY_API_KEY:?環境変数APIFY_API_KEYが設定されていません}"
OUTPUT_DIR="/Users/hasegawataichi/Documents/GAS/Xポスト作成/analysis/ai_trends"
DATE=$(date +%Y%m%d)

# ログファイル
LOG_FILE="$OUTPUT_DIR/fetch_$DATE.log"

echo "AI関連投稿取得開始: $(date)" >> $LOG_FILE

# Apifyでデータ取得
mkdir -p "$OUTPUT_DIR/apify_ai_trends_$DATE"
cd /tmp
apify run apify/twitter-scraper \
  --input '{
    "searchTerms": ["AI", "machine learning", "LLM", "GPT", "Claude"],
    "accounts": ["@OpenAI", "@AnthropicAI", "@GoogleAI", "@MicrosoftAI", "@huggingface"],
    "minLikes": 100,
    "maxResults": 50,
    "language": "en,ja"
  }'

# データをコピー
cp -r storage/datasets/default "$OUTPUT_DIR/apify_ai_trends_$DATE"
cd "/Users/hasegawataichi/Documents/GAS/Xポスト作成"

# データ処理
python3 automation/process_ai_data.py "$OUTPUT_DIR/apify_ai_trends_$DATE" "$OUTPUT_DIR"

echo "AI関連投稿取得完了: $(date)" >> $LOG_FILE

# Slack通知（オプション）
# curl -X POST -H 'Content-type: application/json' \
#   --data '{"text":"AI関連投稿取得完了: '$DATE'"}' \
#   YOUR_SLACK_WEBHOOK_URL
