-- task_execution_log: タスク実行履歴（統一トリガー用）
CREATE TABLE IF NOT EXISTS task_execution_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  task_type TEXT NOT NULL,           -- 'x_posting', 'zoom_analysis'
  executed_at TIMESTAMPTZ NOT NULL,  -- 実行時刻
  status TEXT NOT NULL,              -- 'success', 'failed', 'skipped'
  details JSONB                      -- 詳細情報
);

-- 最新の実行を素早く取得するためのインデックス
CREATE INDEX IF NOT EXISTS idx_task_execution_log_type_time
  ON task_execution_log(task_type, executed_at DESC);

-- 最新実行を取得するビュー
CREATE OR REPLACE VIEW latest_task_executions AS
SELECT DISTINCT ON (task_type)
  task_type,
  executed_at,
  status,
  details
FROM task_execution_log
ORDER BY task_type, executed_at DESC;
