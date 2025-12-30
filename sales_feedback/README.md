# Sales Feedback Agent（営業フィードバックエージェント）

RAGFlowを活用した営業会議分析・ナレッジ蓄積システム

## 概要

```
┌─────────────────────────────────────────────────────────┐
│                   Sales Feedback Agent                   │
│                                                          │
│   📄 議事録        🎥 動画        🎤 音声               │
│      ↓               ↓              ↓                   │
│   ┌─────────────────────────────────────────┐           │
│   │           RAGFlow                        │           │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │           │
│   │  │ドキュメント│  │ベクトル │  │ AI分析  │  │           │
│   │  │  解析    │→│  検索   │→│ (Gemini)│  │           │
│   │  └─────────┘  └─────────┘  └─────────┘  │           │
│   └─────────────────────────────────────────┘           │
│                        ↓                                 │
│   ┌─────────────────────────────────────────┐           │
│   │  📊 フィードバック  │  📚 ナレッジ蓄積  │           │
│   └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

## 機能

- **議事録分析**: Zoom会議の議事録をアップロードして自動分析
- **営業スキル評価**: ヒアリング力、提案力、クロージングなど6項目で評価
- **フィードバック生成**: 良かった点・改善点を具体的に提示
- **ナレッジ蓄積**: 成功事例を蓄積し、検索可能に
- **ベストプラクティス検索**: 類似商談の成功パターンを検索

## 必要環境

- Docker >= 24.0.0
- Docker Compose >= v2.26.1
- RAM: 16GB以上推奨
- ディスク: 50GB以上

## クイックスタート

### 1. セットアップ

```bash
cd sales_feedback
./setup.sh
```

### 2. 初期設定

1. **Web UIにアクセス**
   ```
   http://localhost:8080
   ```

2. **アカウント作成**
   - 「Sign up」からアカウントを作成

3. **LLM設定**
   - 右上のアイコン → 「Model Providers」
   - 「Google」を選択
   - Gemini API キーを入力

### 3. ナレッジベース作成

1. 「Knowledge Base」→「+ Create Knowledge Base」
2. 名前: `sales_knowledge`（営業ナレッジ）
3. 設定:
   - Embedding Model: お好みのモデル
   - Chunk Method: `Naive`（シンプル）または `Book`（構造化）

### 4. ドキュメントアップロード

1. 作成したナレッジベースを選択
2. 「+ Add Files」をクリック
3. 議事録（PDF/Word/テキスト）をアップロード
4. 自動で解析・インデックス化

### 5. チャットで質問

1. 「Chat」→「+ New Chat」
2. 作成したナレッジベースを選択
3. 質問例:
   - 「IT業界への提案で成功したパターンは？」
   - 「クロージングで効果的だったフレーズは？」
   - 「〇〇社との商談で良かった点は？」

## ディレクトリ構成

```
sales_feedback/
├── docker-compose.yml    # Docker構成
├── .env.example          # 環境変数テンプレート
├── .env                  # 環境変数（自動生成）
├── setup.sh              # セットアップスクリプト
├── uploads/              # アップロードファイル
├── logs/                 # ログファイル
└── README.md             # このファイル
```

## 運用コマンド

```bash
# サービス起動
docker compose up -d

# サービス停止
docker compose down

# ログ確認
docker compose logs -f ragflow

# サービス状態確認
docker compose ps

# 全データ削除（リセット）
docker compose down -v
```

## ポート一覧

| サービス | ポート | 用途 |
|---------|-------|------|
| RAGFlow | 8080 | Web UI & API |
| MinIO Console | 9001 | ファイルストレージ管理 |

## API連携

### APIキー取得

1. RAGFlow Web UIにログイン
2. 右上アイコン → 「API」
3. APIキーをコピー

### サンプルリクエスト

```bash
# ドキュメントアップロード
curl -X POST "http://localhost:8080/api/v1/datasets/{dataset_id}/documents" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@meeting_notes.pdf"

# チャット（質問）
curl -X POST "http://localhost:8080/api/v1/chats/{chat_id}/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "成功した商談のパターンを教えて",
    "stream": false
  }'
```

## 営業フィードバック用プロンプト例

ナレッジベース作成時に、以下のシステムプロンプトを設定することで
営業分析に特化した回答が得られます：

```
あなたは経験豊富な営業マネージャーです。
アップロードされた商談議事録を分析し、以下の観点でフィードバックしてください：

【評価項目】
1. ヒアリング力（顧客の課題・ニーズを引き出せているか）
2. 提案力（課題に対する解決策を適切に提示できているか）
3. 異議対応（顧客の懸念・反論に適切に対応できているか）
4. クロージング（次のアクションへ適切に導けているか）
5. ラポール構築（信頼関係を構築できているか）
6. BANT確認（Budget/Authority/Need/Timelineを確認できているか）

【出力形式】
- 各項目を5段階で評価
- 良かった点を具体的な発言とともに列挙
- 改善点を具体的な代替案とともに提示
- 次回に活かせるアクションポイントを3つ
```

## トラブルシューティング

### サービスが起動しない

```bash
# ログを確認
docker compose logs

# リソース確認
docker system df

# 再起動
docker compose restart
```

### メモリ不足

`.env`でElasticsearchのメモリを調整：
```yaml
# docker-compose.yml の elasticsearch サービス
ES_JAVA_OPTS=-Xms256m -Xmx256m
```

### ポート競合

`.env`でポートを変更：
```
RAGFLOW_PORT=8081
```

## 今後の拡張予定

- [ ] 音声ファイルの自動文字起こし（AssemblyAI連携）
- [ ] Zoom録画の自動取得（Zoom API連携）
- [ ] Slack通知連携
- [ ] 自動評価レポート生成

## 参考リンク

- [RAGFlow 公式ドキュメント](https://ragflow.io/docs/dev/)
- [RAGFlow GitHub](https://github.com/infiniflow/ragflow)
