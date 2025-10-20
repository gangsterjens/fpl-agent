from src import channels_fetcher as cf
from src import supabase_client as sc
from dotenv import load_dotenv
import os
import json

# Laster inn fra .env-filen automatisk (default søker i current working dir)
load_dotenv()

# variables from python
sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))


channels = sb.get_data('channels')
#channels = channels.json()
channels = channels.data
#print(channels)
for el in channels:
    print()
    data = cf.get_channels_video_urls(el['channel_id'])
    sb.upsert_data('videos', data, 'video_id')


