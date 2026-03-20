import requests
import pandas as pd
from src.db import supabase_client as sc
import os
from dotenv import load_dotenv
import datetime



load_dotenv()

def get_fpl_event_data() -> list[dict]:
    """
    fetches the gameweek info from the official fpl-api. Important for keeping track of what gameweek it is, and whats the current deadline and last events timestamp.
    """
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    data = requests.get(url)
    data = data.json()
    df = pd.DataFrame(data['events'])
    gw_info = df[['name', 'deadline_time', 'average_entry_score', 'finished', 'data_checked', 'is_previous', 'is_current', 'is_next']].to_dict(orient='records')
    return gw_info

def upload_gw_to_sb() -> None:
    """
    Updates the latest gameweek-info. Important to keep track of last gw and the upcoming deadline
    """

    fpl_data = get_fpl_event_data()
    sb = sc.SupabaseClient(os.getenv('SB_API_KEY'), os.getenv('SB_URL'))
    for event in fpl_data:
        event['inserted_at'] = datetime.datetime.utcnow().isoformat()
        try:
            sb.upsert_data('fpl_gameweek_info', event, 'name', not_refresher=False)
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
    Fetches the the status of the players. Their name, who is eligible and so on. 

    """
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'

    data = requests.get(url)
    data = data.json() 

    df = pd.DataFrame(data['elements'])
    df['selected_by_percent'] = df['selected_by_percent'].astype(float)
    df = df[df['can_select']]
#df = df[df['selected_by_percent'].astype(float) > 10]
    return df[['id', 'web_name', 'first_name', 'second_name', 'selected_by_percent']].sort_values('selected_by_percent', ascending=False).to_dict(orient='records')

BASE_URL = 'https://fantasy.premierleague.com'


def _get_bootstrap_static() -> dict:
    """Fetch and cache bootstrap-static data."""
    resp = requests.get(f'{BASE_URL}/api/bootstrap-static/')
    resp.raise_for_status()
    return resp.json()


def get_teams() -> list[dict]:
    """Get all Premier League teams with id, name, short_name, strength."""
    data = _get_bootstrap_static()
    teams = data['teams']
    return [
        {'id': t['id'], 'name': t['name'], 'short_name': t['short_name'], 'strength': t['strength']}
        for t in teams
    ]


def get_fixtures(gameweek: int | None = None) -> list[dict]:
    """Get fixtures, optionally filtered by gameweek."""
    url = f'{BASE_URL}/api/fixtures/'
    if gameweek:
        url += f'?event={gameweek}'
    resp = requests.get(url)
    resp.raise_for_status()
    fixtures = resp.json()
    return [
        {
            'event': f.get('event'),
            'team_h': f['team_h'],
            'team_a': f['team_a'],
            'team_h_difficulty': f.get('team_h_difficulty'),
            'team_a_difficulty': f.get('team_a_difficulty'),
            'kickoff_time': f.get('kickoff_time'),
            'team_h_score': f.get('team_h_score'),
            'team_a_score': f.get('team_a_score'),
            'finished': f.get('finished', False),
        }
        for f in fixtures
    ]


def get_player_detail(player_id: int) -> dict:
    """Get detailed player info including history and upcoming fixtures."""
    resp = requests.get(f'{BASE_URL}/api/element-summary/{player_id}/')
    resp.raise_for_status()
    return resp.json()


def get_gameweek_live(event_id: int) -> dict:
    """Get live stats for all players in a given gameweek."""
    resp = requests.get(f'{BASE_URL}/api/event/{event_id}/live/')
    resp.raise_for_status()
    return resp.json()


class FPLAuthClient:
    """Authenticated FPL client for team management operations."""

    LOGIN_URL = 'https://users.premierleague.com/accounts/login/'
    API_BASE = 'https://fantasy.premierleague.com/api'

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self._manager_id: int | None = None
        self._login()

    def _login(self):
        # GET the login page to obtain csrftoken cookie
        self.session.get('https://users.premierleague.com/accounts/login/')
        csrftoken = self.session.cookies.get('csrftoken')
        if not csrftoken:
            raise RuntimeError('Could not obtain CSRF token from FPL login page')

        payload = {
            'login': self.email,
            'password': self.password,
            'app': 'plfpl-web',
            'redirect_uri': 'https://fantasy.premierleague.com/',
            'csrfmiddlewaretoken': csrftoken,
        }
        resp = self.session.post(
            self.LOGIN_URL,
            data=payload,
            headers={'Referer': 'https://users.premierleague.com/accounts/login/'},
        )
        resp.raise_for_status()

        if 'pl_profile' not in self.session.cookies.get_dict():
            raise RuntimeError(
                'FPL login failed — pl_profile cookie not set. Check email/password.'
            )

    def _csrf_header(self) -> dict:
        token = self.session.cookies.get('csrftoken', '')
        return {'X-CSRFToken': token, 'Referer': 'https://fantasy.premierleague.com/'}

    def get_manager_id(self) -> int:
        if self._manager_id:
            return self._manager_id
        resp = self.session.get(f'{self.API_BASE}/me/')
        resp.raise_for_status()
        data = resp.json()
        self._manager_id = data['player']['entry']
        return self._manager_id

    def get_my_team(self, manager_id: int) -> dict:
        resp = self.session.get(f'{self.API_BASE}/my-team/{manager_id}/')
        resp.raise_for_status()
        return resp.json()

    def make_transfer(self, manager_id: int, transfers_payload: list[dict], event_id: int) -> dict:
        body = {
            'confirmed': True,
            'entry': manager_id,
            'event': event_id,
            'transfers': transfers_payload,
        }
        resp = self.session.post(
            f'{self.API_BASE}/transfers/',
            json=body,
            headers=self._csrf_header(),
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {'status': 'ok'}

    def set_lineup(self, manager_id: int, picks: list[dict], chip: str | None = None) -> dict:
        body = {'picks': picks}
        if chip:
            body['chip'] = chip
        resp = self.session.post(
            f'{self.API_BASE}/my-team/{manager_id}/',
            json=body,
            headers=self._csrf_header(),
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {'status': 'ok'}


_auth_client: FPLAuthClient | None = None


def get_auth_client() -> FPLAuthClient:
    global _auth_client
    if _auth_client is None:
        email = os.getenv('FPL_EMAIL')
        password = os.getenv('FPL_PASSWORD')
        if not email or not password:
            raise RuntimeError('FPL_EMAIL and FPL_PASSWORD must be set in environment')
        _auth_client = FPLAuthClient(email, password)
    return _auth_client


if __name__ == "__main__":
    upload_gw_to_sb()

