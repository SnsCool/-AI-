# Supabase セットアップ手順

## 1. Supabase プロジェクト作成

1. [Supabase](https://supabase.com) にアクセス
2. 「Start your project」をクリック
3. GitHubアカウントでログイン
4. 「New Project」をクリック
5. 以下を入力:
   - Organization: 選択または新規作成
   - Project name: `zoom-meeting-analysis`（任意）
   - Database Password: 強力なパスワードを設定（メモしておく）
   - Region: Northeast Asia (Tokyo) を選択
6. 「Create new project」をクリック

## 2. APIキーの取得

1. プロジェクトダッシュボードで「Settings」→「API」
2. 以下をコピーして `.env` に設定:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` → `SUPABASE_ANON_KEY`
   - `service_role secret` → `SUPABASE_SERVICE_ROLE_KEY`

## 3. Supabase CLI インストール

```bash
# macOS
brew install supabase/tap/supabase

# npm
npm install -g supabase

# 確認
supabase --version
```

## 4. プロジェクトをリンク

```bash
cd /Users/hatakiyoto/-AI-egent-libvela/zoom

# Supabaseにログイン
supabase login

# プロジェクトをリンク（Project RefはダッシュボードのURLから取得）
# https://supabase.com/dashboard/project/[PROJECT_REF]
supabase link --project-ref <your-project-ref>
```

## 5. マイグレーション実行

```bash
# ローカルのマイグレーションファイルをリモートに適用
supabase db push

# または、SQLエディタで直接実行
# ダッシュボード → SQL Editor → New query → db/migrations/001_create_success_knowledge.sql の内容を貼り付け → Run
```

## 6. 確認

```bash
# テーブル一覧を確認
supabase db remote list

# または、ダッシュボードで確認
# Table Editor → success_knowledge テーブルが作成されていればOK
```

## 7. .env ファイル作成

```bash
cd /Users/hatakiyoto/-AI-egent-libvela/zoom
cp .env.example .env
# .env を編集して実際の値を入力
```

## トラブルシューティング

### pgvector が有効化できない場合
ダッシュボード → Database → Extensions → `vector` を検索 → Enable

### IVFFlat インデックスが作成できない場合
データが少ない場合は以下で代替:
```sql
CREATE INDEX idx_success_knowledge_embedding ON success_knowledge
USING hnsw (embedding vector_cosine_ops);
```

### RLSでアクセスできない場合
開発中は一時的に無効化:
```sql
ALTER TABLE success_knowledge DISABLE ROW LEVEL SECURITY;
```
