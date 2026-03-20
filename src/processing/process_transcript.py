import json
from src.db import supabase_client as sc
from src.processing.llm import llm
from src.processing import prompts
from src.processing.json_parser import tekst2json
import os
import time
from dotenv import load_dotenv
load_dotenv()

def transcript_to_json() -> None:
    print('downloading data')
    sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))
    data = sb.get_data('transcripts')
    data = data.data
    print(f'Processing {len(data)} transcripts')
    print('looping through')
    json_list = []
    for el in data[-5:-3]:
        start_time = time.time()
        prompt = prompts.JSON_SUMMARY
        prompt = prompt.format(transcript=el['text'])
        print(f'sending in length of {len(prompt.split())}')
        json_result = llm(prompt, system_prompt='You are a helpfull assistant, that only does as instructed. At the end: Do only return a valid Json')
        json_result = tekst2json(json_result)
        json_result['video_id'] = el['video_id']
        print(time.time() - start_time, 'seconds')
    json_list.append(json_result)
    with open('test_json.json', 'w') as e:
        json.dump(json_list, e)


def upload_transcript_json_data() -> None:
    with open('test_data.json' 'r') as e:
        data = json.load(e)
    video_id = data['video_id']
    meta_json_transcript = [{key: item[key] for key in ("type", "video_id", "summary") if key in item} for item in data]
    player_json = []
    for el in data:
        name = el['name']
        decision = el['decision']
        summary = el['summary']
        citation = el['citation']
        player_json.append(video_id, name, decision, summary, citation)
    

if __name__ == '__main__':
    transcript_to_json()
