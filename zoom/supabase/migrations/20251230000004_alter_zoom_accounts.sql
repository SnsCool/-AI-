-- zoom_accounts テーブルを修正（OAuth方式に対応）
ALTER TABLE zoom_accounts
  ADD COLUMN IF NOT EXISTS account_id TEXT,
  ADD COLUMN IF NOT EXISTS client_id TEXT,
  ADD COLUMN IF NOT EXISTS client_secret TEXT;

-- api_key列は不要なので削除（エラーになる場合はスキップ）
ALTER TABLE zoom_accounts DROP COLUMN IF EXISTS api_key;

-- サンプルデータ挿入
INSERT INTO zoom_accounts (assignee, account_id, client_id, client_secret) VALUES
  ('畑 来世人', 'xLiP_rw0RNmohjmt5Ptp7w', 'aIVa1hW7RamWvAIIcsfbwQ', 'MPzurThH6MhncXVZWoj5K86KZaf39UaR')
ON CONFLICT (assignee) DO UPDATE SET
  account_id = EXCLUDED.account_id,
  client_id = EXCLUDED.client_id,
  client_secret = EXCLUDED.client_secret;
