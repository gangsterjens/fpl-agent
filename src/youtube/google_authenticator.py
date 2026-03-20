import os
import google.auth
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Path to your OAuth 2.0 credentials JSON file
CLIENT_SECRETS_FILE = '/app/data/credentials.json'

# The required API scope for YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def authenticate_youtube():
    creds = None
    # Token file stores the user's access and refresh tokens, and is created automatically when the
    # authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds, _ = google.auth.load_credentials_from_file('token.json')

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This will prompt the user to log in via a browser.
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the YouTube API client with the credentials
    youtube = build('youtube', 'v3', credentials=creds)
    return youtube

# Example of using the YouTube API
def get_video_details(youtube, video_id):
    request = youtube.videos().list(part='snippet', id=video_id)
    response = request.execute()
    return response

# Example usage
if __name__ == '__main__':
    youtube = authenticate_youtube()

    # Replace with a valid YouTube video ID
    video_id = 'dQw4w9WgXcQ'  # Just an example video ID
    video_details = get_video_details(youtube, video_id)
    print(video_details)
