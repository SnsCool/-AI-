#!/bin/bash
# APIサーバー起動スクリプト

cd "$(dirname "$0")"

# 仮想環境を有効化
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 仮想環境が見つかりません。セットアップを実行してください:"
    echo "   python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# ポート設定（デフォルト: 8000）
PORT=${API_PORT:-8000}

echo "🚀 APIサーバーを起動します"
echo "   http://localhost:$PORT"
echo "   http://localhost:$PORT/docs (Swagger UI)"
echo ""

# uvicornでサーバー起動
uvicorn main:app --reload --host 0.0.0.0 --port $PORT
