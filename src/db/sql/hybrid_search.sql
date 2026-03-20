-- Hybrid search migration: adds full-text search alongside vector search
-- Run this in the Supabase SQL Editor (one-time setup)

-- 1. Add auto-generated tsvector column for full-text search
ALTER TABLE embedded_documents
  ADD COLUMN IF NOT EXISTS fts tsvector
  GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

-- 2. Create GIN index for fast full-text lookups
CREATE INDEX IF NOT EXISTS idx_embedded_documents_fts
  ON embedded_documents USING gin(fts);

-- 3. Hybrid search function using Reciprocal Rank Fusion (RRF)
--    The semantic CTE skips date filtering to allow the HNSW/IVFFlat index
--    to work. Date filtering is applied after the RRF merge.
CREATE OR REPLACE FUNCTION hybrid_search_embedded_documents(
  query_text text,
  query_embedding vector(1536),
  match_count int,
  min_published_at text DEFAULT '2020-01-01',
  max_published_at text DEFAULT '2099-12-31',
  full_text_weight float DEFAULT 1.0,
  semantic_weight float DEFAULT 1.0,
  rrf_k int DEFAULT 50
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql
AS $$
WITH full_text AS (
  SELECT
    ed.id,
    ROW_NUMBER() OVER (
      ORDER BY ts_rank_cd(ed.fts, websearch_to_tsquery('english', query_text)) DESC
    ) AS rank_ix
  FROM embedded_documents ed
  WHERE
    ed.fts @@ websearch_to_tsquery('english', query_text)
    AND (ed.metadata->>'published_at') >= min_published_at
    AND (ed.metadata->>'published_at') <= max_published_at
  ORDER BY rank_ix
  LIMIT LEAST(match_count, 30) * 2
),
semantic AS (
  SELECT
    ed.id,
    ROW_NUMBER() OVER (
      ORDER BY ed.embedding <=> query_embedding
    ) AS rank_ix
  FROM embedded_documents ed
  ORDER BY ed.embedding <=> query_embedding
  LIMIT LEAST(match_count, 30) * 4
)
SELECT
  ed.id,
  ed.content,
  ed.metadata,
  (
    COALESCE(1.0 / (rrf_k + full_text.rank_ix), 0.0) * full_text_weight +
    COALESCE(1.0 / (rrf_k + semantic.rank_ix), 0.0) * semantic_weight
  )::float AS similarity
FROM
  full_text
  FULL OUTER JOIN semantic ON full_text.id = semantic.id
  JOIN embedded_documents ed ON COALESCE(full_text.id, semantic.id) = ed.id
WHERE
  (ed.metadata->>'published_at') >= min_published_at
  AND (ed.metadata->>'published_at') <= max_published_at
ORDER BY similarity DESC
LIMIT LEAST(match_count, 30);
$$;
