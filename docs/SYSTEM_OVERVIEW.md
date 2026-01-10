# X自動投稿システム 要件定義書

## 1. システム概要

このシステムは、AI関連の最新情報をX（Twitter）から自動収集し、投稿を生成してXに自動投稿するワークフローです。

### 処理の流れ

```
1. データ収集（Apify API）
   ↓
2. 投稿文生成（Google Gemini）
   ↓
3. Google Driveに保存
   ↓
4. スプレッドシートに記録
   ↓
5. Xに自動投稿
```

---

## 2. 取得対象アカウント（13アカウント）

### AI企業公式アカウント

| アカウント | 説明 |
|-----------|------|
| @OpenAI | OpenAI公式（ChatGPT開発元） |
| @AnthropicAI | Anthropic公式（Claude開発元） |
| @GoogleAI | Google AI公式 |
| @GoogleDeepMind | Google DeepMind公式 |
| @StabilityAI | Stability AI公式（Stable Diffusion開発元） |
| @huggingface | Hugging Face公式（AI/MLプラットフォーム） |
| @MistralAI | Mistral AI公式 |

### AI業界キーパーソン

| アカウント | 説明 |
|-----------|------|
| @ylecun | Yann LeCun（Meta AI チーフサイエンティスト） |
| @jeffdean | Jeff Dean（Google SVP） |
| @demishassabis | Demis Hassabis（DeepMind CEO） |
| @AravSrinivas | Arav Srinivas（Perplexity CEO） |

### 日本のAI関連アカウント

| アカウント | 説明 |
|-----------|------|
| @mako_yukinari | 日本のAI関連発信者 |
| @ctgptlb | 日本のAI関連発信者 |

---

## 3. 実行スケジュール

### 自動実行（GitHub Actions）

| 時刻（JST） | 説明 |
|------------|------|
| 7:00 | 朝の定期実行 |
| 9:00 | 午前の定期実行 |
| 18:45 | 夕方の定期実行 |
| 20:00 | 夜の定期実行 |

**1日4回、自動的にワークフローが実行されます。**

### 手動実行

GitHub ActionsのWorkflow dispatchから手動実行も可能です。

---

## 4. コスト

### Apify API（データ収集）

| 項目 | 値 |
|------|-----|
| 料金単価 | $0.0004/ツイート |
| 1回あたりの取得数 | 13件（13アカウント × 1件） |
| **1回あたりのコスト** | **約$0.005** |
| 1日のコスト（4回実行） | 約$0.02 |
| **月間コスト** | **約$0.60** |

### 利用プラン

- **Apify Starterプラン**: $39/月
- 月間使用率: 約1.5%（余裕あり）

---

## 5. 使用しているAPI・サービス

| サービス | 用途 |
|---------|------|
| **Apify** | Xからのデータ収集 |
| **Google Gemini** | 投稿文の自動生成 |
| **Google Drive** | 生成データの保存 |
| **Google Spreadsheet** | 投稿ログの記録 |
| **X API** | 投稿の自動投稿 |
| **GitHub Actions** | ワークフローの自動実行 |

---

## 6. 設定ファイル

### アカウント設定

**ファイル**: `x/ai_search_config.json`

```json
{
  "official_accounts": [
    "OpenAI",
    "AnthropicAI",
    "GoogleAI",
    ...
  ]
}
```

このファイルを編集することで、取得対象アカウントを変更できます。

### ワークフロー設定

**ファイル**: `.github/workflows/daily_agent.yml`

- 実行スケジュール
- 最大投稿数（デフォルト: 100件）
- 環境変数の設定

---

## 7. 出力先

### Google Drive

- 生成された投稿文（.txt）
- 動画ファイル（.mp4）※ある場合

### Google Spreadsheet

| カラム | 内容 |
|--------|------|
| 日時 | 投稿日時 |
| 元ツイートURL | 情報元のURL |
| 生成テキスト | AIが生成した投稿文 |
| 投稿ステータス | 成功/失敗 |

---

## 8. トラブルシューティング

### よくある問題

| 問題 | 原因 | 解決策 |
|------|------|--------|
| X投稿が403エラー | API権限不足 | X Developer Portalで「Read and Write」権限を有効化 |
| Apifyでデータ取得失敗 | 使用量制限超過 | Apifyダッシュボードで制限を確認・引き上げ |
| アカウントが取得されない | アカウント名の誤り | ai_search_config.jsonを確認 |

---

## 9. 更新履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-10 | 個別API呼び出しに変更（コスト97%削減） |
| 2026-01-10 | アカウントリスト更新（13アカウント） |
| 2026-01-10 | max_postsデフォルト値を100に変更 |

---

## 10. 連絡先・サポート

問題が発生した場合は、GitHubリポジトリのIssuesに報告してください。
