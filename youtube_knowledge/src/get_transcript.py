import json
from youtube_transcript_api import YouTubeTranscriptApi
import supabase_client as sc
import time
import os 
from dotenv import load_dotenv
load_dotenv()
channel_id = 'UCcPWnCj5AKC19HaySZjb25g'
video_id = '6cFaRIS7msc'
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
    full_text = " ".join(item["text"] for item in transcript_data)
    data = {
        'video_id': video_id,
        'text': full_text
    }
    try:
        sb.upsert_data('transcripts', data, 'video_id')
        print('Inserted/Updated full transcript for video:', video_id)
    except Exception as e:
        print('Error inserting/updating full transcript for video:', video_id, 'Error:', e)


if __name__ == "__main__":
    upload_full_transcript(video_id=video_id)


