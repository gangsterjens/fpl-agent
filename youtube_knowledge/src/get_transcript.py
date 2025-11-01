import json
from youtube_transcript_api import YouTubeTranscriptApi
import supabase_client as sc
import time
import os 
from dotenv import load_dotenv
from llm import llm
import prompts
import fpl_api as fpl
load_dotenv()
channel_id = 'UCcPWnCj5AKC19HaySZjb25g'
video_id = 'txMrwVepihc'
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
    # # Write to JSON file
    # with open('data_1.json', 'w', encoding='utf-8') as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4)

def upload_full_transcript(video_id) -> None:
    transcript_data = get_transcript(video_id)

    # get metadata from video 
    print('Concatenating text')
    full_text = " ".join(item["text"] for item in transcript_data)
    print('Concatenating text_END')

    where_statement = ('video_id', video_id)

    print('### FETCHING METADATA FROM VIDEOS')
    video_meta = sb.get_data('videos', where_statement=where_statement)
    print('### DONE______FETCHING METADATA FROM VIDEOS')

    print('fetching players')
    players = fpl.get_player_info()
    print('fetching players_done')

    prompt = prompts.REFINE_TR_PROMPT
    prompt = prompt.format(players=players, video_meta=video_meta)
    length = len(full_text.split()) + len(prompt.split())
    print(f"sending in a total of {length} words")
    print('#### REFINING TEXT')
    refined_text = llm(full_text ,prompt)
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

    print('UPSERTING DATA___DONE')


if __name__ == "__main__":
    upload_full_transcript(video_id=video_id)


