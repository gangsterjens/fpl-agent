CREATE OR REPLACE VIEW vector_candidates AS
select v.video_id, c.channel_name, has_vectors FROM videos v
join channels c
  on c.channel_id = v.channel_id
join transcripts t
  on v.video_id = t.video_id
where has_vectors is false