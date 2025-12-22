# Cron設定 - AI関連投稿自動取得

## 概要
毎日14:00にAI関連の投稿を自動取得するcron設定です。

## 設定手順

### 1. cronの設定
```bash
# crontabを編集
crontab -e

# 以下の行を追加
0 14 * * * /Users/hasegawataichi/Documents/GAS/Xポスト作成/automation/ai_trends_fetcher.sh
```

### 2. 実行権限の設定
```bash
chmod +x /Users/hasegawataichi/Documents/GAS/Xポスト作成/automation/ai_trends_fetcher.sh
chmod +x /Users/hasegawataichi/Documents/GAS/Xポスト作成/automation/process_ai_data.py
```

### 3. ログの確認
```bash
# ログファイルの場所
/Users/hasegawataichi/Documents/GAS/Xポスト作成/analysis/ai_trends/fetch_YYYYMMDD.log

# ログを確認
tail -f /Users/hasegawataichi/Documents/GAS/Xポスト作成/analysis/ai_trends/fetch_$(date +%Y%m%d).log
```

## 実行スケジュール
- **毎日 14:00 JST**: AI関連投稿を取得
- **実行時間**: 約5分
- **保存先**: `analysis/ai_trends/`

## エラー処理
- 取得失敗時はSlackに通知
- ログファイルに詳細を記録
- 再試行は3回まで

## 手動実行
```bash
# 手動で実行
/Users/hasegawataichi/Documents/GAS/Xポスト作成/automation/ai_trends_fetcher.sh
```
