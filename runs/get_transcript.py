import json
from youtube_transcript_api import YouTubeTranscriptApi
import time
channel_id = 'UCcPWnCj5AKC19HaySZjb25g'
video_id = '6cFaRIS7msc'
def get_transcript(video_id):

    print('_______________________ STARTING FETCHING VIDEOS')
    

    ytt_api = YouTubeTranscriptApi()
    data = ytt_api.fetch(video_id)
    data = data.to_raw_data()

    print('_______________________ DONE FETCHING VIDEOS')



    # Write to JSON file
    with open('data1.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


