from langchain_core.tools import tool
from src.fpl import fpl_api as fpl


def _build_team_map() -> dict[int, str]:
    teams = fpl.get_teams()
    return {t['id']: t['name'] for t in teams}


def _fuzzy_match_player(name: str, players: list[dict]) -> dict | None:
    name_lower = name.lower()
    # Exact web_name match first
    for p in players:
        if p['web_name'].lower() == name_lower:
            return p
    # Partial match on web_name
    for p in players:
        if name_lower in p['web_name'].lower():
            return p
    # Match on full name
    for p in players:
        full = f"{p['first_name']} {p['second_name']}".lower()
        if name_lower in full:
            return p
    return None


@tool
def lookup_player(player_name: str) -> str:
    """Look up a player's stats, form, and upcoming fixtures.
    Use this when asked about a specific player's performance, whether to buy/sell them, etc.
    """
    players = fpl.get_player_info()
    player = _fuzzy_match_player(player_name, players)
    if not player:
        return f"Could not find player matching '{player_name}'."

    team_map = _build_team_map()
    detail = fpl.get_player_detail(player['id'])

    # Recent history (last 5 GWs)
    history = detail.get('history', [])
    recent = history[-5:] if history else []
    history_lines = []
    for gw in recent:
        history_lines.append(
            f"  GW{gw['round']}: {gw['total_points']}pts, "
            f"minutes={gw['minutes']}, goals={gw['goals_scored']}, "
            f"assists={gw['assists']}, xG={gw.get('expected_goals', 'N/A')}, "
            f"xA={gw.get('expected_assists', 'N/A')}"
        )

    # Upcoming fixtures (next 5)
    upcoming = detail.get('fixtures', [])[:5]
    fixture_lines = []
    for fix in upcoming:
        opponent_id = fix['team_a'] if fix['is_home'] else fix['team_h']
        opponent = team_map.get(opponent_id, f"Team {opponent_id}")
        venue = "H" if fix['is_home'] else "A"
        difficulty = fix['difficulty']
        fixture_lines.append(f"  GW{fix['event']}: {opponent} ({venue}, FDR {difficulty})")

    lines = [
        f"Player: {player['web_name']} ({player['first_name']} {player['second_name']})",
        f"Selected by: {player['selected_by_percent']}%",
        "",
        "Recent form (last 5 GWs):",
        *(history_lines if history_lines else ["  No recent data"]),
        "",
        "Upcoming fixtures:",
        *(fixture_lines if fixture_lines else ["  No upcoming fixtures"]),
    ]
    return "\n".join(lines)


@tool
def get_upcoming_fixtures(team_name: str = "", gameweek: int = 0) -> str:
    """Get upcoming fixtures, optionally filtered by team or gameweek.
    Use this when asked about fixture difficulty, who plays who, etc.
    Pass team_name to filter for a specific team's fixtures.
    Pass gameweek number to see a specific gameweek's matches.
    """
    team_map = _build_team_map()
    team_name_to_id = {v.lower(): k for k, v in team_map.items()}

    gw = gameweek if gameweek > 0 else None
    fixtures = fpl.get_fixtures(gameweek=gw)

    # Filter to unfinished fixtures if no specific GW requested
    if not gw:
        fixtures = [f for f in fixtures if not f['finished']]

    # Filter by team if specified
    target_id = None
    if team_name:
        name_lower = team_name.lower()
        for tname, tid in team_name_to_id.items():
            if name_lower in tname:
                target_id = tid
                break
        if target_id:
            fixtures = [f for f in fixtures if f['team_h'] == target_id or f['team_a'] == target_id]

    if not fixtures:
        return "No fixtures found matching the criteria."

    # Limit output
    fixtures = fixtures[:20]

    lines = []
    for f in fixtures:
        home = team_map.get(f['team_h'], f"Team {f['team_h']}")
        away = team_map.get(f['team_a'], f"Team {f['team_a']}")
        gw_label = f"GW{f['event']}" if f.get('event') else "TBD"
        kick = f['kickoff_time'][:16] if f.get('kickoff_time') else "TBD"

        if f.get('team_h_score') is not None and f.get('team_a_score') is not None:
            score = f" ({f['team_h_score']}-{f['team_a_score']})"
        else:
            score = ""

        fdr = f" [FDR: H={f.get('team_h_difficulty', '?')}, A={f.get('team_a_difficulty', '?')}]"
        lines.append(f"{gw_label}: {home} vs {away}{score}{fdr} — {kick}")

    return "\n".join(lines)


@tool
def get_gameweek_info() -> str:
    """Get current gameweek status, deadlines, and scores.
    Use this when asked about deadlines, current gameweek, or recent results.
    """
    gw_data = fpl.get_fpl_event_data()

    current = next((g for g in gw_data if g['is_current']), None)
    next_gw = next((g for g in gw_data if g['is_next']), None)
    previous = next((g for g in gw_data if g['is_previous']), None)

    lines = []
    if current:
        lines.append(f"Current: {current['name']}")
        lines.append(f"  Deadline: {current['deadline_time']}")
        lines.append(f"  Average score: {current['average_entry_score']}")
        lines.append(f"  Finished: {current['finished']}")
    if next_gw:
        lines.append(f"\nNext: {next_gw['name']}")
        lines.append(f"  Deadline: {next_gw['deadline_time']}")
    if previous:
        lines.append(f"\nPrevious: {previous['name']}")
        lines.append(f"  Average score: {previous['average_entry_score']}")

    return "\n".join(lines) if lines else "Could not retrieve gameweek info."
