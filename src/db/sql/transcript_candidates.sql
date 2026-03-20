/*

An view that finds the videos that are not in transcript, 

that also is within the last deadline day of a finished event and before the next one.

*/



CREATE VIEW transcript_candidates AS
WITH gw AS (
  SELECT 
    MAX(CASE WHEN finished = true THEN deadline_time END) AS last_dd,
    MIN(CASE WHEN is_next = true THEN deadline_time END) AS next_dd
  FROM fpl_gameweek_info
),
final_table AS (
  SELECT 
    v.video_id, 
    v.published_at
  FROM videos v
  LEFT JOIN transcripts t 
    ON v.video_id = t.video_id
  WHERE t.video_id IS NULL
    AND v.published_at BETWEEN 
      (SELECT last_dd FROM gw) 
      AND (SELECT next_dd FROM gw)
)
SELECT * FROM final_table;
