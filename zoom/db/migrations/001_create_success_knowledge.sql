-- Migration: 001_create_success_knowledge
-- Description: 成功ナレッジテーブルの作成
-- Created: 2025-12-30

-- pgvector拡張を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- 成功ナレッジテーブル
CREATE TABLE IF NOT EXISTS success_knowledge (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- 基本情報
  meeting_date DATE NOT NULL,
  assignee TEXT NOT NULL,              -- 担当者
  customer_name TEXT,                  -- 顧客名

  -- 分析結果
  closing_result TEXT NOT NULL,        -- 成約 / 未成約 / 継続
  talk_ratio_sales INT,                -- 営業の話す割合（%）
  talk_ratio_customer INT,             -- 顧客の話す割合（%）
  issues_heard TEXT[],                 -- ヒアリングした課題（配列）
  proposal TEXT[],                     -- 提案内容（配列）
  good_points TEXT[],                  -- 良かった点（配列）
  improvement_points TEXT[],           -- 改善点（配列）
  success_keywords TEXT[],             -- 成功キーワード（配列）

  -- RAG用
  summary TEXT,                        -- 商談要約（検索用）
  embedding VECTOR(768),               -- Embeddingベクトル（Gemini text-embedding-004）

  -- メタデータ
  transcript_file_path TEXT,           -- 文字起こしファイルパス
  video_file_path TEXT,                -- 動画ファイルパス
  sheet_row_id TEXT                    -- zoom相談一覧シートの行ID
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_success_knowledge_assignee ON success_knowledge(assignee);
CREATE INDEX IF NOT EXISTS idx_success_knowledge_meeting_date ON success_knowledge(meeting_date);
CREATE INDEX IF NOT EXISTS idx_success_knowledge_closing_result ON success_knowledge(closing_result);
CREATE INDEX IF NOT EXISTS idx_success_knowledge_customer_name ON success_knowledge(customer_name);

-- ベクトル検索用インデックス（IVFFlat）
CREATE INDEX IF NOT EXISTS idx_success_knowledge_embedding ON success_knowledge
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- updated_at自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_success_knowledge_updated_at
  BEFORE UPDATE ON success_knowledge
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- RLS（Row Level Security）有効化
ALTER TABLE success_knowledge ENABLE ROW LEVEL SECURITY;

-- ポリシー: サービスロールは全操作可能
CREATE POLICY "Service role has full access" ON success_knowledge
  FOR ALL
  USING (auth.role() = 'service_role');

-- コメント
COMMENT ON TABLE success_knowledge IS '営業商談の成功ナレッジを蓄積するテーブル';
COMMENT ON COLUMN success_knowledge.embedding IS 'Gemini text-embedding-004 で生成した768次元ベクトル';
