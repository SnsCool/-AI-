#!/bin/bash
# ===========================================
# Sales Feedback Agent - セットアップスクリプト
# ===========================================

set -e

echo "================================================"
echo "  Sales Feedback Agent - RAGFlow セットアップ"
echo "================================================"
echo ""

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# -------------------------------------------
# 前提条件チェック
# -------------------------------------------
echo -e "${YELLOW}[1/5] 前提条件をチェック中...${NC}"

# Docker チェック
if ! command -v docker &> /dev/null; then
    echo -e "${RED}エラー: Docker がインストールされていません${NC}"
    echo "Docker をインストールしてください: https://docs.docker.com/get-docker/"
    exit 1
fi

# Docker Compose チェック
if ! docker compose version &> /dev/null; then
    echo -e "${RED}エラー: Docker Compose がインストールされていません${NC}"
    echo "Docker Compose v2 をインストールしてください"
    exit 1
fi

# Docker バージョンチェック
DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0")
echo "  Docker バージョン: $DOCKER_VERSION"

echo -e "${GREEN}  ✓ 前提条件OK${NC}"
echo ""

# -------------------------------------------
# 環境変数ファイル作成
# -------------------------------------------
echo -e "${YELLOW}[2/5] 環境変数ファイルを準備中...${NC}"

if [ ! -f .env ]; then
    cp .env.example .env

    # ランダムなパスワードを生成
    MYSQL_PASS=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)
    MINIO_PASS=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9' | head -c 16)

    # パスワードを置換
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your_secure_password_here/${MYSQL_PASS}/" .env
        sed -i '' "s/MINIO_PASSWORD=.*/MINIO_PASSWORD=${MINIO_PASS}/" .env
    else
        # Linux
        sed -i "s/your_secure_password_here/${MYSQL_PASS}/" .env
        sed -i "s/MINIO_PASSWORD=.*/MINIO_PASSWORD=${MINIO_PASS}/" .env
    fi

    echo -e "${GREEN}  ✓ .env ファイルを作成しました${NC}"
    echo -e "${YELLOW}  ⚠ .env ファイルを確認し、必要に応じて編集してください${NC}"
else
    echo -e "${GREEN}  ✓ .env ファイルは既に存在します${NC}"
fi
echo ""

# -------------------------------------------
# ディレクトリ作成
# -------------------------------------------
echo -e "${YELLOW}[3/5] 必要なディレクトリを作成中...${NC}"

mkdir -p uploads
mkdir -p logs

echo -e "${GREEN}  ✓ ディレクトリ作成完了${NC}"
echo ""

# -------------------------------------------
# Docker イメージのプル
# -------------------------------------------
echo -e "${YELLOW}[4/5] Docker イメージをダウンロード中...${NC}"
echo "  （初回は時間がかかります）"

docker compose pull

echo -e "${GREEN}  ✓ イメージダウンロード完了${NC}"
echo ""

# -------------------------------------------
# サービス起動
# -------------------------------------------
echo -e "${YELLOW}[5/5] サービスを起動中...${NC}"

docker compose up -d

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  セットアップ完了！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "アクセス方法:"
echo "  RAGFlow Web UI: http://localhost:8080"
echo "  MinIO Console:  http://localhost:9001"
echo ""
echo "次のステップ:"
echo "  1. http://localhost:8080 にアクセス"
echo "  2. アカウントを作成（初回のみ）"
echo "  3. 設定 > Model Providers で Gemini API キーを設定"
echo "  4. ナレッジベースを作成"
echo ""
echo "サービス状態確認:"
echo "  docker compose ps"
echo ""
echo "ログ確認:"
echo "  docker compose logs -f ragflow"
echo ""
echo "停止:"
echo "  docker compose down"
echo ""
