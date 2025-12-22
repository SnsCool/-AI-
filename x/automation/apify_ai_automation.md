# Apify AI関連投稿取得自動化

## 概要
AI関連の最新情報を自動取得して、analysisフォルダに格納する自動化システムです。

## 対象アカウント
- @OpenAI
- @AnthropicAI
- @GoogleAI
- @MicrosoftAI
- @huggingface
- @LangChainAI
- @ReplicateAI
- @RunPod
- @togethercompute
- @Groq

## 取得条件
- いいね数: 100以上
- 期間: 過去7日
- 言語: 英語・日本語
- キーワード: AI, machine learning, deep learning, LLM, GPT, Claude

## 自動化設定

### 1. Apify設定
```javascript
// Apify Actor設定
{
  "searchTerms": ["AI", "machine learning", "LLM", "GPT", "Claude"],
  "accounts": ["@OpenAI", "@AnthropicAI", "@GoogleAI"],
  "minLikes": 100,
  "maxResults": 50,
  "language": "en,ja"
}
```

### 2. 実行スケジュール
- **頻度**: 毎日 14:00 JST
- **実行時間**: 約5分
- **保存先**: `analysis/ai_trends/`

### 3. データ形式
```
analysis/ai_trends/
├── apify_ai_trends_20250115.txt
├── apify_openai_20250115.txt
├── apify_anthropic_20250115.txt
└── apify_google_20250115.txt
```

## 実行方法

### 手動実行
```bash
# Apify CLIで実行
apify run apify/twitter-scraper --config config.json
```

### 自動実行
```bash
# cronで毎日14:00に実行
0 14 * * * /path/to/ai_trends_fetcher.sh
```

## データ処理
1. **取得**: Apifyでデータを取得
2. **フィルタリング**: AI関連の投稿のみ抽出
3. **保存**: analysisフォルダに格納
4. **通知**: 取得完了をSlack/Discordに通知
