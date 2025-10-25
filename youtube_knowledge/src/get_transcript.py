import json
from youtube_transcript_api import YouTubeTranscriptApi
import supabase_client as sc
import time
import os 
from dotenv import load_dotenv
from llm import llm
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
    full_text = " ".join(item["text"] for item in transcript_data)
    
    where_statement = ('video_id', video_id)
    video_meta = sb.get_data('videos', where_statement=where_statement)
    prompt = f"""
        Refine this text from a YouTube transcript. Here is the metadata from the videos 'About':
        {video_meta} T
        he text you are to refine comes under in user input. 

        Only return the refined text. Not 'certainly here is the refined text' etc etc.. only the text that is refined
        """
    refined_text = llm(full_text ,prompt)

    data = {
        'video_id': video_id,
        'text': refined_text
    }
    try:
        sb.upsert_data('transcripts', data, 'video_id')
        print('Inserted/Updated full transcript for video:', video_id)
    except Exception as e:
        print('Error inserting/updating full transcript for video:', video_id, 'Error:', e)


if __name__ == "__main__":
    upload_full_transcript(video_id=video_id)


