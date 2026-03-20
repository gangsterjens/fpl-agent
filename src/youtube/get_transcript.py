from src.youtube import get_videos as gv
import json
from youtube_transcript_api import YouTubeTranscriptApi
from src.db import supabase_client as sc
import time
import os
from dotenv import load_dotenv
from src.processing.llm import llm
from src.processing import prompts
from src.fpl import fpl_api as fpl
load_dotenv()
# channel_id = 'UCcPWnCj5AKC19HaySZjb25g'
# video_id = 'txMrwVepihc'
sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))
def get_transcript(video_id) -> list[dict]:

    print('_______________________ STARTING FETCHING VIDEOS')
    

    ytt_api = YouTubeTranscriptApi()
    data = ytt_api.fetch(video_id)
    data = data.to_raw_data()

    print('_______________________ DONE FETCHING VIDEOS')

    for el in data:
        el['video_id'] = video_id

    return data

def upload_full_transcript(video_id) -> None:
    transcript_data = get_transcript(video_id)

    # get metadata from video 
    print('Concatenating text')
    full_text = " ".join(item["text"] for item in transcript_data)

    where_statement = ('video_id', video_id)

    print('### FETCHING METADATA FROM VIDEOS')
    video_meta = sb.get_data('videos', where_statement=where_statement)

    print('fetching players')
    players = fpl.get_player_info()

    prompt = prompts.REFINE_TR_PROMPT
    prompt = prompt.format(players=players, video_meta=video_meta)
    length = len(full_text.split()) + len(prompt.split())
    print(f"sending in a total of {length} words")
    print('#### REFINING TEXT')
    refined_text = llm(full_text, prompt)
    print('#### REFINING TEXT____DONE')

    data = {
        'video_id': video_id,
        'text': refined_text
    }
    print('UPSERTING DATA')
    try:
        sb.upsert_data('transcripts', data, 'video_id', not_refresher=False)
        print('Inserted/Updated full transcript for video:', video_id)
    except Exception as e:
        print('Error inserting/updating full transcript for video:', video_id, 'Error:', e)

    print('___DONE')

def get_transcript_candidates(rewrite=True) -> list:
    if rewrite:
        data = sb.get_data('transcript_candidates_rewrite')
    else:
        data = sb.get_data('transcript_candidates')
    candidates = []
    
    for id in data.data:
        candidates.append(id['video_id'])
    return candidates

def fill_up_latest() -> None:
    gv.get_videos()
    fpl.upload_gw_to_sb()
    candidates = get_transcript_candidates()
    if len(candidates) < 1:
        print('No new transcripts available')
        return None
    for video_id in candidates:
        upload_full_transcript(video_id=video_id)

if __name__ == "__main__":
    fill_up_latest()
    



