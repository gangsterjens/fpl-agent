-- Table: transcript_facts
-- Run this DDL in the Supabase SQL Editor to create the table.

CREATE TABLE IF NOT EXISTS transcript_facts (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  video_id text REFERENCES videos(video_id),
  overthoughts jsonb,
  players jsonb,
  created_at timestamptz DEFAULT now(),
  UNIQUE(video_id)
);

CREATE INDEX IF NOT EXISTS idx_transcript_facts_video_id
  ON transcript_facts(video_id);


-- Function: search_player_facts
-- Unnests the players JSONB array and filters by name / action / date range.

CREATE OR REPLACE FUNCTION search_player_facts(
  p_player_name text,
  p_action_filter text DEFAULT NULL,
  p_min_date text DEFAULT '2020-01-01',
  p_max_date text DEFAULT '2099-12-31',
  p_limit int DEFAULT 20
)
RETURNS TABLE (
  video_id text,
  title text,
  channel_name text,
  published_at text,
  player_name text,
  action text,
  reason text,
  overthoughts jsonb
)
LANGUAGE sql STABLE
AS $$
  SELECT
    v.video_id,
    v.title,
    v.channel_name,
    v.published_at::text,
    p.value->>'name'   AS player_name,
    p.value->>'action'  AS action,
    p.value->>'reason'  AS reason,
    tf.overthoughts
  FROM transcript_facts tf
  JOIN videos v ON v.video_id = tf.video_id
  CROSS JOIN LATERAL jsonb_array_elements(tf.players) AS p(value)
  WHERE p.value->>'name' ILIKE '%' || p_player_name || '%'
    AND (p_action_filter IS NULL OR p.value->>'action' = p_action_filter)
    AND v.published_at::date >= p_min_date::date
    AND v.published_at::date <= p_max_date::date
  ORDER BY v.published_at DESC
  LIMIT p_limit;
$$;
