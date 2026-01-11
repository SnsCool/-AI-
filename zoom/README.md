# Zoom Meeting Analysis Agent

Zoom録画を自動分析し、フィードバックを生成するエージェントです。

## 概要

- Zoomアカウントから録画を自動取得
- 文字起こしをGemini AIで分析
- フィードバックをGoogle スプレッドシートに出力
- 動画をGoogle Driveにアップロード

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Zoom API      │────▶│   Gemini AI     │────▶│ Google Sheets   │
│  (録画取得)      │     │   (分析)         │     │   (出力)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│   Supabase      │                           │  Google Drive   │
│ (認証情報/履歴)  │                           │ (文字起こし/動画) │
└─────────────────┘                           └─────────────────┘
```

## 実行方法

### GitHub Actions（自動実行）

1時間ごとに自動実行されます（6グループに分割してローテーション処理）。

```yaml
# .github/workflows/meeting_analysis.yml
schedule:
  - cron: '0 * * * *'
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
2. **録画取得**: 過去1ヶ月分を取得（APIクォータ節約のため）
3. **処理対象**: 各アカウントの最新1件のみ処理（処理済みはスキップ）
4. **文字起こし**: VTTファイルをダウンロード・テキスト抽出
5. **分析**: Gemini AIでフィードバック生成
6. **動画アップロード**:
   - Zoomから動画をダウンロード
   - サービスアカウント経由でGoogle Driveに一時アップロード
   - GAS経由でユーザーフォルダにコピー（ユーザー所有になる）
   - サービスアカウントの元ファイルを削除（容量節約）
7. **出力**:
   - Google Docs: 文字起こし全文
   - スプレッドシート「Zoom相談一覧」: 分析結果（顧客シートにマッチした場合のみ）
   - スプレッドシート「データ格納」: 全録画の履歴

## 環境変数

| 変数名 | 説明 |
|--------|------|
| `SUPABASE_URL` | Supabase URL |
| `SUPABASE_ANON_KEY` | Supabase Anonymous Key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Service Role Key |
| `GEMINI_API_KEY` | Google Gemini API Key |
| `GOOGLE_CREDENTIALS_JSON` | Google サービスアカウント認証情報（JSON） |
| `GOOGLE_SPREADSHEET_ID` | 出力先スプレッドシートID |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive保存先フォルダID |
| `GAS_WEBAPP_URL` | Google Apps Script Web App URL |

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

32アカウントを6グループに分割し、1時間ごとに1グループずつ処理します。
6時間で全アカウントを1周します。

| 時間（UTC） | グループ | アカウント |
|-------------|----------|-----------|
| 0時, 6時, 12時, 18時 | 1 | 1〜6番目 |
| 1時, 7時, 13時, 19時 | 2 | 7〜12番目 |
| 2時, 8時, 14時, 20時 | 3 | 13〜18番目 |
| 3時, 9時, 15時, 21時 | 4 | 19〜24番目 |
| 4時, 10時, 16時, 22時 | 5 | 25〜30番目 |
| 5時, 11時, 17時, 23時 | 6 | 31〜32番目 |

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
| H | 面談動画（Google Driveリンク） |
| I | フィードバック |

### 書き込み条件

- **Zoom相談一覧シート**: 顧客管理シートにマッチした場合のみ書き込み
- **データ格納シート**: 全録画を書き込み（履歴蓄積用）

### 処理済み管理

- Supabase `processed_recordings` テーブルで管理
- ステータスが「着座」「飛び」の場合は処理済みマーク（再処理しない）
- それ以外は処理済みマークなし（ステータス更新時に再処理される）

## トラブルシューティング

### 認証エラー

```
Supabase認証エラー: 400 Bad Request
```

→ Supabaseの認証情報が古い可能性があります。スプレッドシート「ZoomKeys」シートを確認してください。

### タイムアウト

処理が60分を超える場合はタイムアウトします。グループ分割により負荷が分散されています。

### 録画が取得できない

- Zoom録画設定を確認（クラウド録画が有効か）
- アカウントのServer-to-Server OAuthアプリが有効か確認
- ローカル録画を使用している場合はクラウド録画に取得できません

### 動画アップロードエラー

- サービスアカウントのDrive容量を確認
- GAS Web App URLが正しいか確認
- GASのデプロイが最新か確認
