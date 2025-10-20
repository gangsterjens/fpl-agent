import googleapiclient.discovery
from datetime import datetime

def get_channels_video_urls(channel_id, yt_api_key):
  # Replace with your API key and channel ID
  
  #channel_id = "UC8043oOKTB4uP8Nq15Kz6bg"

  # Build the API service
  youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=yt_api_key)

  # Request channel information to get the upload playlist ID
  request = youtube.channels().list(part="contentDetails", id=channel_id)
  response = request.execute()

  youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=yt_api_key)
  # Request channel information to get the upload playlist ID
  request = youtube.channels().list(part="contentDetails", id=channel_id)
  response = request.execute()

  # Get the upload playlist ID
  upload_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

  # Retrieve all videos from the upload playlist
  all_videos = []
  next_page_token = None

  while True:
      playlist_request = youtube.playlistItems().list(
          playlistId=upload_playlist_id,
          part="snippet",
          maxResults=50,  # Max is 50 per request
          pageToken=next_page_token
      )
      playlist_response = playlist_request.execute()

      # Append current page of videos to the list
      all_videos.extend(playlist_response['items'])

      # Check if there's another page
      next_page_token = playlist_response.get('nextPageToken')
      if not next_page_token:
          break

  channel_videos_info = []
  for item in all_videos:
    matchday_date = datetime.strptime('2025-08-18 00:00:00', '%Y-%m-%d %H:%M:%S')
    date = datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
    if date > matchday_date:
      tmp_dict = {}
      video_id = item['snippet']['resourceId']['videoId']
      tmp_dict['video_id'] = video_id
      tmp_dict['video_url'] = f"https://www.youtube.com/watch?v={video_id}"
      tmp_dict['title'] = item['snippet']['title']
      tmp_dict['description'] = item['snippet']['description'].replace('\n','')
      tmp_dict['channel_name'] = item['snippet']['channelTitle']
      tmp_dict['published_at'] = item['snippet']['publishedAt']
      tmp_dict['channel_id'] = channel_id
      channel_videos_info.append(tmp_dict)
    #return channel_videos_info
  channel_videos_info
  return channel_videos_info