import requests
import pandas as pd
import supabase_client as sc
import os
from dotenv import load_dotenv
import datetime



load_dotenv()

def get_fpl_event_data() -> list[dict]:
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    data = requests.get(url)
    data = data.json()
    df = pd.DataFrame(data['events'])
    gw_info = df[['name', 'deadline_time', 'average_entry_score', 'finished', 'data_checked', 'is_previous', 'is_current', 'is_next']].to_dict(orient='records')
    return gw_info

def upload_gw_to_sb() -> None:
    fpl_data = get_fpl_event_data()
    sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))
    for event in fpl_data:
        event['inserted_at'] = datetime.datetime.utcnow().isoformat()
        try:
            sb.upsert_data('fpl_gameweek_info', event, 'name')
            print('updated FPL event data:', event['name'])
        except Exception as e:
            print('Error inserting/updating FPL event data:', e)

def get_between_gw() -> tuple[datetime.datetime, datetime.datetime]:
    """
    returns the timestamps of the start and end of the current gameweek
    in datetime format
    
    """
    sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))
    gw_data = sb.get_data('fpl_gameweek_info').data
    gw_df = pd.DataFrame(gw_data)
    gw_df['deadline_time'] = pd.to_datetime(gw_df['deadline_time'])
    start_gw = gw_df[gw_df['is_current'] == True]['deadline_time'].values[0]
    end_gw = gw_df[gw_df['is_next'] == True]['deadline_time'].values[0]
    return start_gw, end_gw

def get_player_info():
    """
    Fethces the the status of the players. Their name, who is eligible and so on. 

    """
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'

    data = requests.get(url)
    data = data.json() 

    df = pd.DataFrame(data['elements'])
    df['selected_by_percent'] = df['selected_by_percent'].astype(float)
    df = df[df['can_select']]
#df = df[df['selected_by_percent'].astype(float) > 10]
    return df[['id', 'web_name', 'first_name', 'second_name', 'selected_by_percent']].sort_values('selected_by_percent', ascending=False).to_dict(orient='records')

if __name__ == "__main__":
    upload_gw_to_sb()
    



