# AI関連投稿自動取得セットアップ手順

## 概要
Apifyを使ってAI関連の最新投稿を自動取得し、analysisフォルダに格納するシステムのセットアップ手順です。

## 必要な準備

### 1. Apifyアカウントの作成
1. [Apify](https://apify.com)にアクセス
2. アカウントを作成
3. APIキーを取得

### 2. 必要なツールのインストール
```bash
# Apify CLIのインストール
npm install -g @apify/cli

# Pythonの依存関係
pip install requests
```

## セットアップ手順

### 1. 設定ファイルの編集
```bash
# automation/apify_ai_automation.mdのAPIキーを設定
APIFY_API_KEY="your_actual_api_key_here"
```

### 2. 実行権限の設定
```bash
chmod +x automation/ai_trends_fetcher.sh
chmod +x automation/process_ai_data.py
```

### 3. cronの設定
```bash
# crontabを編集
crontab -e

# 以下の行を追加
0 14 * * * /Users/hasegawataichi/Documents/GAS/Xポスト作成/automation/ai_trends_fetcher.sh
```

## 使用方法

### 手動実行
```bash
# 手動でAI関連投稿を取得
./automation/ai_trends_fetcher.sh
```

### 自動実行
- 毎日14:00に自動実行
- ログは`analysis/ai_trends/fetch_YYYYMMDD.log`に保存

### データの確認
```bash
# 取得したデータを確認
ls -la analysis/ai_trends/
cat analysis/ai_trends/ai_trends_$(date +%Y%m%d).txt
```

## トラブルシューティング

### よくある問題
1. **APIキーエラー**: ApifyのAPIキーが正しく設定されているか確認
2. **権限エラー**: スクリプトの実行権限を確認
3. **ネットワークエラー**: インターネット接続を確認

### ログの確認
```bash
# 最新のログを確認
tail -f analysis/ai_trends/fetch_$(date +%Y%m%d).log
```

## カスタマイズ

### 取得対象アカウントの変更
`automation/apify_ai_automation.md`のaccountsリストを編集

### 取得条件の変更
`automation/ai_trends_fetcher.sh`の設定を編集

### 実行時間の変更
cronの設定を変更
