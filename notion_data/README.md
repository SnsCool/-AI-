# Notion Data - 構造化データ管理

Notion MCPを使用した情報抽出・構造化データの管理ディレクトリです。

## ディレクトリ構成

```
notion_data/
├── pages/           # ページ一覧・構造データ
│   └── notion_pages_list.md
├── databases/       # データベース構造データ
├── knowledge/       # ナレッジ抽出データ
└── exports/         # エクスポートデータ
```

## 各ディレクトリの役割

### pages/
- Notionワークスペース内の全ページ一覧
- ページ構造・階層情報
- 定期的に自動更新

### databases/
- データベースのスキーマ情報
- プロパティ定義
- リレーション構造

### knowledge/
- ページコンテンツから抽出したナレッジ
- カテゴリ別整理データ
- 検索用インデックス

### exports/
- 一時的なエクスポートデータ
- バックアップファイル

## 更新方法

Notion MCPエージェントが自動的にデータを更新します。

## API Token

- GitHub Secrets: `NOTION_API_TOKEN`
- ローカル: `.env` ファイル
