-- pgvector拡張を有効化
CREATE EXTENSION IF NOT EXISTS vector;

-- 成功ナレッジテーブル
CREATE TABLE IF NOT EXISTS success_knowledge (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- 基本情報
  meeting_date DATE NOT NULL,
  assignee TEXT NOT NULL,
  customer_name TEXT,

  -- 分析結果
  closing_result TEXT NOT NULL,
  talk_ratio_sales INT,
  talk_ratio_customer INT,
  issues_heard TEXT[],
  proposal TEXT[],
  good_points TEXT[],
  improvement_points TEXT[],
  success_keywords TEXT[],

  -- RAG用
  summary TEXT,
  embedding VECTOR(768),

  -- メタデータ
  transcript_file_path TEXT,
  video_file_path TEXT,
  sheet_row_id TEXT
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_success_knowledge_assignee ON success_knowledge(assignee);
CREATE INDEX IF NOT EXISTS idx_success_knowledge_meeting_date ON success_knowledge(meeting_date);
CREATE INDEX IF NOT EXISTS idx_success_knowledge_closing_result ON success_knowledge(closing_result);
CREATE INDEX IF NOT EXISTS idx_success_knowledge_customer_name ON success_knowledge(customer_name);

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
