# AI Research Mode - 最新AI情報の自動収集と投稿

## 概要

特定のアカウントではなく、AI関連のキーワードで検索して最新情報を自動収集・投稿する機能です。

## 主な機能

### 🔍 AI Research Mode（AI検索モード - 強化版）

#### 3段階の情報収集戦略

**1. 📢 公式アカウント優先取得**
- OpenAI、Anthropic、GoogleAIなど15の公式アカウントから直接取得
- **いいね数フィルタなし**: 投稿直後の重要情報も逃さない
- Sam Altman、Andrej Karpathy、Yann LeCunなどキーパーソンも含む

**2. 🚀 リリース・発表キーワード検出**
- "released", "announced", "launching", "発表", "リリース"などを検出
- AIキーワード + リリースキーワードの組み合わせで高精度検索
- 新製品・新機能の発表を優先的にキャッチ

**3. 🔎 一般AI関連検索**
- ChatGPT、Claude、Gemini、LLMなど20種類のキーワードで検索
- いいね数50以上でフィルタリング（品質保証）
- 多言語対応（英語・日本語）

#### ⏰ 時間ベースフィルタリング
- **過去24時間以内**の投稿のみを対象（デフォルト）
- 設定で6時間、12時間、48時間などに変更可能
- 最新のアップデート情報に特化

#### 🎯 優先度ソート
1. **Official**: 公式アカウントからの投稿（最優先）
2. **Release**: リリース・発表キーワードを含む投稿
3. **General**: 一般的なAI関連投稿

### 👤 Account Mode（アカウントモード）
- 特定のアカウントからツイートを取得（従来の動作）

## 設定ファイル: `ai_search_config.json`

```json
{
  "ai_research_mode": true,  // AI検索モードを有効化
  "search_keywords": [        // 検索キーワード（自由に編集可能）
    "ChatGPT",
    "Claude AI",
    "Gemini",
    "GPT-4",
    "GPT-5",
    "OpenAI",
    "Anthropic",
    "Google AI",
    "LLM",
    "AI breakthrough",
    "AI release",
    "AI update",
    "Sora AI",
    "Stable Diffusion"
  ],
  "filters": {
    "min_likes": 50,          // 最小いいね数（品質フィルタ）
    "max_tweets": 20,         // 最大取得ツイート数
    "languages": ["en", "ja"], // 対応言語
    "sort_by": "Latest"       // ソート順（Latest: 最新順）
  },
  "fallback_accounts": [      // フォールバック用アカウント
    "OpenAI",
    "AnthropicAI",
    "GoogleAI"
  ]
}
```

## 使い方

### 1. AI Research Mode（推奨）

キーワード検索で最新AI情報を収集：

```bash
# ai_search_config.jsonを編集
{
  "ai_research_mode": true,  // これをtrueにする
  ...
}

# 実行（X投稿なし）
python main.py

# X投稿あり
python main.py --post-to-x
```

### 2. Account Mode

特定アカウントからツイートを取得：

```bash
# ai_search_config.jsonを編集
{
  "ai_research_mode": false,  // これをfalseにする
  ...
}

# 実行
python main.py
```

## キーワードのカスタマイズ

`ai_search_config.json`の`search_keywords`を編集して、検索キーワードを自由に追加・削除できます：

```json
"search_keywords": [
  // 基本的なAIキーワード
  "ChatGPT",
  "Claude AI",
  "Gemini",
  "GPT-4",
  "LLM",

  // 企業名
  "OpenAI",
  "Anthropic",
  "Google AI",
  "Microsoft AI",

  // 具体的なプロダクト
  "Sora AI",
  "DALL-E",
  "Midjourney",
  "Stable Diffusion",

  // トレンドキーワード
  "AI breakthrough",
  "AI release",
  "AI update",
  "AGI",

  // 日本語キーワード
  "人工知能",
  "機械学習",
  "深層学習"
]
```

## フィルタ設定

### いいね数でフィルタリング

```json
"filters": {
  "min_likes": 50  // 50いいね以上のツイートのみ取得
}
```

- **10-50**: 幅広く情報を収集（ノイズ多め）
- **50-100**: バランスの取れた品質
- **100+**: 高品質だが情報量が少ない

### 取得数の調整

```json
"filters": {
  "max_tweets": 20  // 最大20ツイートまで取得
}
```

## ワークフロー

```
1. 🔍 データ収集
   ↓ Apify API経由でキーワード検索
   ↓ いいね数でフィルタリング

2. 💾 分析・格納
   ↓ analysis/ai_research_*.json に保存

3. 📝 フォーマット選択
   ↓ format/*.md から読み込み

4. 🧠 スタイル参照
   ↓ brain/*.md から読み込み

5. ✍️ 投稿作成
   ↓ Geminiで投稿文を生成

6. 🚀 投稿完了
   ↓ Google Driveに保存
   ↓ X APIで投稿（オプション）
```

## GitHub Actions での実行

### 手動実行

1. **Actions** タブ → **Unified Agent Scheduler** を選択
2. **Run workflow** をクリック
3. オプションを選択：
   - **Test mode**: `true`（X投稿なし）
   - **Dry run**: `false`

### 自動実行

30分ごとに自動実行されます（cron: `'0,30 * * * *'`）

## 設定のカスタマイズ例

### 超最新情報重視（6時間以内）

公式発表から6時間以内の情報のみを収集：

```json
{
  "filters": {
    "time_range_hours": 6,
    "min_likes": 10,
    "official_min_likes": 0
  },
  "priority_settings": {
    "enable_official_priority": true,
    "enable_release_keywords": true,
    "enable_time_filter": true
  }
}
```

### 公式アカウントのみ追跡

公式アカウントとリリースキーワードに絞る：

```json
{
  "priority_settings": {
    "enable_official_priority": true,
    "enable_release_keywords": true,
    "enable_time_filter": false
  }
}
```

### 幅広く収集（時間フィルタなし）

```json
{
  "filters": {
    "time_range_hours": 168,  // 7日間
    "min_likes": 30
  }
}
```

## トラブルシューティング

### 最新情報が見つからない場合

1. **時間範囲を広げる**: `time_range_hours`を24→48に変更
2. **公式アカウントを追加**: `official_accounts`リストに追加
3. **リリースキーワードを追加**: `release_keywords`に業界固有の用語を追加

### ツイートが見つからない場合

1. **キーワードを増やす**: `search_keywords`に追加
2. **いいね数を下げる**: `min_likes`を50→30に変更
3. **取得数を増やす**: `max_tweets`を20→50に変更

### 低品質なツイートが多い場合

1. **いいね数を上げる**: `min_likes`を50→100に変更
2. **公式アカウント優先を有効化**: `enable_official_priority: true`
3. **時間フィルタを厳しく**: `time_range_hours`を24→12に変更

## サンプル設定

### 最新情報重視（幅広く収集）

```json
{
  "filters": {
    "min_likes": 30,
    "max_tweets": 50,
    "sort_by": "Latest"
  }
}
```

### 品質重視（厳選して収集）

```json
{
  "filters": {
    "min_likes": 100,
    "max_tweets": 10,
    "sort_by": "Top"
  }
}
```

## まとめ

### 🎯 何が変わったか

**従来の課題**:
- いいね数フィルタで投稿直後の重要情報を見逃す
- 公式発表を検出できない
- 古い情報も混ざってしまう

**強化版の解決策**:
- ✅ **公式アカウント優先**: いいね数に関わらず取得
- ✅ **リリースキーワード検出**: "announced", "released"などを自動検出
- ✅ **時間フィルタ**: 過去24時間以内の最新情報に限定
- ✅ **3段階の優先度ソート**: 公式 > リリース > 一般

### 🚀 おすすめ設定

**バランス型（デフォルト）**:
- 公式アカウント: いいね数なし
- リリースキーワード: いいね10以上
- 一般検索: いいね50以上
- 時間フィルタ: 24時間以内

**超最新重視型**:
- 時間フィルタ: 6時間以内
- 公式アカウント + リリースキーワードのみ
- 一般検索は無効化

**網羅型**:
- 時間フィルタ: 48-72時間
- いいね数: 30以上
- 全ての検索方法を有効化

AI Research Mode（強化版）を使うと、**投稿直後の重要な技術発表も逃さず**、AI業界全体の最新情報を自動収集できます。
