-- zoom_accounts: 営業ごとのZoom APIキー管理
CREATE TABLE IF NOT EXISTS zoom_accounts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  assignee TEXT NOT NULL UNIQUE,  -- 担当者名
  api_key TEXT NOT NULL           -- Zoom API Key
);

-- processed_recordings: 処理済み録画の記録（二重処理防止）
CREATE TABLE IF NOT EXISTS processed_recordings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  processed_at TIMESTAMPTZ DEFAULT NOW(),

  recording_id TEXT NOT NULL UNIQUE,  -- ZoomのミーティングID
  assignee TEXT NOT NULL,             -- 担当者名
  meeting_date DATE,                  -- 面談日
  customer_name TEXT                  -- 顧客名
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_zoom_accounts_assignee ON zoom_accounts(assignee);
CREATE INDEX IF NOT EXISTS idx_processed_recordings_assignee ON processed_recordings(assignee);
CREATE INDEX IF NOT EXISTS idx_processed_recordings_recording_id ON processed_recordings(recording_id);
