# Sales Feedback Agent（営業フィードバックエージェント）

GitHub Actionsベースの営業会議分析・ナレッジ蓄積システム

## ワークフロー

```
ワークフロー1: 入力
  │ 議事録/音声をアップロード
  │ メタデータを入力
  ▼
ワークフロー2: 前処理
  │ 音声→テキスト変換（AssemblyAI）
  │ 話者分離
  ▼
ワークフロー3: 分析
  │ Gemini で営業スキル評価
  │ フィードバック生成
  ▼
ワークフロー4: 保存・通知
  │ Drive: レポート保存
  │ Notion: ナレッジ蓄積（成功事例）
  │ Slack: 通知
  ▼
  完了
```

## 機能

- **議事録分析**: 営業会議の議事録を自動分析
- **音声文字起こし**: 音声/動画ファイルを話者分離付きで文字起こし
- **営業スキル評価**: 6項目で1-5点評価
- **フィードバック生成**: 良かった点・改善点を具体的に提示
- **ナレッジ蓄積**: 成功事例をNotionに蓄積
- **Slack通知**: 分析結果を担当者に通知

## 使い方

### 手動実行

1. GitHubリポジトリの「Actions」タブを開く
2. 「Sales Feedback Agent」を選択
3. 「Run workflow」をクリック
4. 以下を入力：
   - `transcript_text`: 議事録テキスト
   - `sales_rep`: 営業担当者名
   - `customer`: 顧客名
   - `industry`: 業種
   - `is_closed`: クロージング成功したか
5. 「Run workflow」で実行

### 音声ファイルの場合

1. 音声/動画ファイルをGoogle Driveにアップロード
2. 共有リンクを取得
3. `audio_url`に入力、`meeting_type`を`audio`に設定

## 評価項目

| 項目 | 評価内容 |
|------|----------|
| ヒアリング力 | 課題・ニーズを引き出せているか |
| 提案力 | 解決策を適切に提示できているか |
| 異議対応 | 反論に適切に対応できているか |
| クロージング | 次のアクションに導けているか |
| ラポール構築 | 信頼関係を構築できているか |
| BANT確認 | 予算/決裁者/ニーズ/時期を確認できているか |

## ディレクトリ構成

```
sales_feedback/
├── src/
│   ├── analyze.py         # Gemini分析
│   ├── transcribe.py      # 音声文字起こし
│   ├── save_to_drive.py   # Drive保存
│   ├── save_to_notion.py  # Notion保存
│   └── notify_slack.py    # Slack通知
├── requirements.txt       # Python依存関係
├── workflow_diagram.md    # ワークフロー図
└── README.md

.github/workflows/
└── sales_feedback.yml     # GitHub Actions
```

## 必要なGitHub Secrets

```
# AI分析
GEMINI_API_KEY              # Gemini API キー

# 音声文字起こし
ASSEMBLYAI_API_KEY          # AssemblyAI API キー

# Google Drive
GCP_SA_KEY_JSON                   # サービスアカウントJSON
SALES_FEEDBACK_DRIVE_FOLDER_ID    # 保存先フォルダID

# Notion
NOTION_TOKEN                # Notion API トークン
SALES_KNOWLEDGE_DB_ID       # ナレッジDBのID

# Slack
SLACK_BOT_TOKEN                  # Slack Bot トークン
SALES_FEEDBACK_CHANNEL_ID        # 通知チャンネルID
```

## Notionデータベース設定

以下のプロパティを持つデータベースを作成してください：

| プロパティ名 | タイプ |
|-------------|--------|
| 名前 | タイトル |
| 日付 | 日付 |
| 担当者 | テキスト |
| 顧客名 | テキスト |
| 業種 | セレクト |
| 商材 | セレクト |
| 総合スコア | 数値 |
| ヒアリング力 | 数値 |
| 提案力 | 数値 |
| クロージング | 数値 |
| クロージング成功 | チェックボックス |

## 出力例

### Slack通知

```
商談フィードバック ⭐

担当者: 山田太郎
顧客: 株式会社ABC
業種: IT
総合スコア: 3.8/5.0

各項目スコア:
ヒアリング力:  ████░ 4/5
提案力:        ███░░ 3/5
異議対応:      ████░ 4/5
クロージング:  ███░░ 3/5
ラポール構築:  ████░ 4/5
BANT確認:      ████░ 4/5

✅ 良かった点
• 課題のヒアリングが丁寧で、顧客の本質的なニーズを引き出せていた
• 具体的な導入事例を交えた説明が効果的だった

📈 改善ポイント
• クロージング時の次アクション提示をより明確に
• 予算感の確認をもう少し早い段階で行う

💡 次回へのアドバイス
1. 商談冒頭でゴール設定を共有する
2. 競合比較資料を準備しておく
3. 決裁フローを早めに確認する
```

## ローカル開発

```bash
# 依存関係インストール
pip install -r sales_feedback/requirements.txt

# 環境変数設定
export GEMINI_API_KEY=your_key
export ASSEMBLYAI_API_KEY=your_key

# 分析実行
python sales_feedback/src/analyze.py \
  --transcript-text "議事録テキスト..." \
  --sales-rep "山田太郎" \
  --customer "株式会社ABC" \
  --industry "IT" \
  --output feedback.json
```

## 今後の拡張予定

- [ ] Zoom Webhook連携（会議終了時自動トリガー）
- [ ] 日次/週次サマリーレポート
- [ ] チーム別・担当者別ダッシュボード
- [ ] ナレッジ検索機能（RAG）
