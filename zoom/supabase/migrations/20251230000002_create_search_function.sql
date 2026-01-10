-- 類似ナレッジ検索関数
CREATE OR REPLACE FUNCTION match_success_knowledge(
  query_embedding VECTOR(768),
  match_count INT DEFAULT 5,
  filter_closing_result TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  meeting_date DATE,
  assignee TEXT,
  customer_name TEXT,
  closing_result TEXT,
  good_points TEXT[],
  success_keywords TEXT[],
  summary TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    sk.id,
    sk.meeting_date,
    sk.assignee,
    sk.customer_name,
    sk.closing_result,
    sk.good_points,
    sk.success_keywords,
    sk.summary,
    1 - (sk.embedding <=> query_embedding) AS similarity
  FROM success_knowledge sk
  WHERE
    (filter_closing_result IS NULL OR sk.closing_result = filter_closing_result)
    AND sk.embedding IS NOT NULL
  ORDER BY sk.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
