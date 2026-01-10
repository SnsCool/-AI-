# Zoom Meeting Analysis Agent

Zoom録画を自動分析し、フィードバックを生成するエージェントです。

## 概要

- Zoomアカウントから録画を自動取得
- 文字起こしをGemini AIで分析
- フィードバックをGoogle スプレッドシートに出力

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Zoom API      │────▶│   Gemini AI     │────▶│ Google Sheets   │
│  (録画取得)      │     │   (分析)         │     │   (出力)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│   Supabase      │                           │  Google Docs    │
│ (認証情報/履歴)  │                           │  (文字起こし)    │
└─────────────────┘                           └─────────────────┘
```

## 実行方法

### GitHub Actions（自動実行）

10分ごとに自動実行されます（6グループに分割して処理）。

```yaml
# .github/workflows/meeting_analysis.yml
schedule:
  - cron: '*/10 * * * *'
```

### 手動実行

```bash
# 全アカウント処理
python batch_zoom.py

# テスト実行（書き込みなし）
python batch_zoom.py --dry-run

# 特定グループのみ処理
python batch_zoom.py --group 1
```

## 処理フロー

1. **認証**: Supabase → フォールバック: スプレッドシート「ZoomKeys」
2. **録画取得**: 過去6ヶ月分を取得（月ごとにAPIリクエスト）
3. **文字起こし**: VTTファイルをダウンロード・テキスト抽出
4. **分析**: Gemini AIでフィードバック生成
5. **出力**:
   - Google Docs: 文字起こし全文
   - スプレッドシート「Zoom相談一覧」: 分析結果

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `SUPABASE_URL` | Supabase URL |
| `SUPABASE_ANON_KEY` | Supabase Anonymous Key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key |
| `GEMINI_API_KEY` | Google Gemini API Key |
| `GOOGLE_CREDENTIALS_JSON` | Google サービスアカウント認証情報（JSON） |
| `GOOGLE_SPREADSHEET_ID` | 出力先スプレッドシートID |

## ファイル構成

```
zoom/
├── batch_zoom.py          # メインバッチ処理スクリプト
├── main.py                # 単体実行用
├── requirements.txt       # Python依存パッケージ
└── services/
    ├── zoom_client.py     # Zoom API クライアント
    ├── gemini_client.py   # Gemini AI クライアント
    ├── sheets_client.py   # Google Sheets クライアント
    ├── supabase_client.py # Supabase クライアント
    └── google_drive_client.py # Google Drive クライアント
```

## Zoom認証情報

### 認証フロー

1. Supabase `zoom_accounts` テーブルから取得
2. 失敗時: スプレッドシート「ZoomKeys」シートから取得

### 認証情報の構成

| フィールド | 説明 |
|-----------|------|
| `account_id` | Zoom Account ID |
| `client_id` | Zoom Client ID |
| `client_secret` | Zoom Client Secret |

### 認証情報の更新

Zoom Marketplace (https://marketplace.zoom.us/) で Server-to-Server OAuth アプリの認証情報を確認・更新してください。

## グループ分割処理

33アカウントを6グループに分割し、10分ごとに1グループずつ処理します。

| 時間 | グループ | アカウント |
|------|----------|-----------|
| :00分 | 1 | 1〜6番目 |
| :10分 | 2 | 7〜12番目 |
| :20分 | 3 | 13〜18番目 |
| :30分 | 4 | 19〜24番目 |
| :40分 | 5 | 25〜30番目 |
| :50分 | 6 | 31〜33番目 |

## 出力先

- **Zoom相談一覧シート**: https://docs.google.com/spreadsheets/d/1R5oMbJ7E-QfDFhHR164y8JKs6XLnkJcw8zBm2IPSn8E

### シート列構成

| 列 | 内容 |
|----|------|
| A | 顧客名 |
| B | 担当者 |
| C | 面談日時 |
| D | 所要時間 |
| E | 事前キャンセル（着座/飛び/リスケ等） |
| F | 初回/実施後ステータス（成約/失注/保留等） |
| G | 文字起こし（Google Docsリンク） |
| H | 面談動画（Zoom共有リンク） |
| I | フィードバック |

## トラブルシューティング

### 認証エラー

```
Supabase認証エラー: 400 Bad Request
```

→ Supabaseの認証情報が古い可能性があります。スプレッドシート「ZoomKeys」シートを確認してください。

### タイムアウト

処理が60分を超える場合はタイムアウトします。グループ分割により負荷が分散されています。

### 録画が取得できない

- Zoom録画設定を確認
- アカウントのServer-to-Server OAuthアプリが有効か確認
