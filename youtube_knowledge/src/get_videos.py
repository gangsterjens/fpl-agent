import channels_fetcher as cf
import supabase_client as sc
from dotenv import load_dotenv
import os
import json

# Laster inn fra .env-filen automatisk (default søker i current working dir)
load_dotenv()

# variables from python
sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))


channels = sb.get_data('channels')
print('Fetched channels from Supabase:', channels)
#channels = channels.json()
channels = channels.data
#print(channels)
for el in channels:
    data = cf.get_channels_video_urls(el['channel_id'], os.getenv('YT_API_KEY'))
    print('Inserting videos for channel:', el['channel_id'])
    sb.upsert_data('videos', data, 'video_id')


