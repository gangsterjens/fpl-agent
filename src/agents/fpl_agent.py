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


# ---------------------------------------------------------------------------
# Authenticated team-management tools
# ---------------------------------------------------------------------------

def _get_bootstrap_elements() -> list[dict]:
    """Return full elements list from bootstrap-static."""
    data = fpl._get_bootstrap_static()
    return data['elements']


def _element_type_name(element_type: int) -> str:
    return {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}.get(element_type, '?')


@tool
def get_my_team() -> str:
    """Fetch your current FPL squad: starting XI, bench, captain, bank, free transfers, and available chips."""
    client = fpl.get_auth_client()
    manager_id = client.get_manager_id()
    team_data = client.get_my_team(manager_id)

    elements = _get_bootstrap_elements()
    id_to_player = {p['id']: p for p in elements}
    team_map = _build_team_map()

    picks = team_data.get('picks', [])
    transfers = team_data.get('transfers', {})
    chips = team_data.get('chips', [])

    starting = []
    bench = []
    captain_name = vice_captain_name = ''

    for pick in picks:
        p = id_to_player.get(pick['element'], {})
        name = p.get('web_name', f"ID {pick['element']}")
        pos = _element_type_name(p.get('element_type', 0))
        team_name = team_map.get(p.get('team', 0), '?')
        line = f"{name} ({pos}, {team_name})"

        if pick.get('is_captain'):
            captain_name = name
            line += ' [C]'
        if pick.get('is_vice_captain'):
            vice_captain_name = name
            line += ' [VC]'

        if pick['position'] <= 11:
            starting.append(line)
        else:
            bench.append(line)

    bank = transfers.get('bank', 0) / 10
    free_transfers = transfers.get('limit', 1)
    if transfers.get('made', 0) > 0:
        free_transfers = max(0, free_transfers - transfers['made'])

    available_chips = [c['name'] for c in chips if c['status_for_entry'] == 'available']

    lines = [
        '== Your FPL Squad ==',
        '',
        'Starting XI:',
        *[f'  {i+1}. {s}' for i, s in enumerate(starting)],
        '',
        'Bench:',
        *[f'  {i+1}. {b}' for i, b in enumerate(bench)],
        '',
        f'Captain: {captain_name}',
        f'Vice-captain: {vice_captain_name}',
        f'Bank: £{bank:.1f}m',
        f'Free transfers: {free_transfers}',
        f'Available chips: {", ".join(available_chips) if available_chips else "None"}',
    ]
    return '\n'.join(lines)


@tool
def make_transfer(player_out_name: str, player_in_name: str) -> str:
    """Make a single FPL transfer: sell player_out and buy player_in.
    Use full or partial player names (e.g. 'Haaland', 'Salah').
    """
    client = fpl.get_auth_client()
    manager_id = client.get_manager_id()

    elements = _get_bootstrap_elements()
    all_players = [
        {'id': p['id'], 'web_name': p['web_name'], 'first_name': p['first_name'],
         'second_name': p['second_name'], 'now_cost': p['now_cost'],
         'element_type': p['element_type'], 'selected_by_percent': p.get('selected_by_percent', '0')}
        for p in elements
    ]

    player_out = _fuzzy_match_player(player_out_name, all_players)
    player_in = _fuzzy_match_player(player_in_name, all_players)

    if not player_out:
        return f"Could not find player to sell matching '{player_out_name}'."
    if not player_in:
        return f"Could not find player to buy matching '{player_in_name}'."

    # Get current team to find selling price
    team_data = client.get_my_team(manager_id)
    squad_ids = {pick['element'] for pick in team_data.get('picks', [])}
    if player_out['id'] not in squad_ids:
        return f"{player_out['web_name']} is not in your squad."
    if player_in['id'] in squad_ids:
        return f"{player_in['web_name']} is already in your squad."

    # Find selling price from picks
    selling_price = player_out['now_cost']
    for pick in team_data.get('picks', []):
        if pick['element'] == player_out['id']:
            selling_price = pick.get('selling_price', player_out['now_cost'])
            break

    # Find current event
    gw_data = fpl.get_fpl_event_data()
    current_event = next((g for g in gw_data if g['is_next']), None)
    if not current_event:
        current_event = next((g for g in gw_data if g['is_current']), None)
    if not current_event:
        return 'Could not determine current gameweek.'

    event_id = int(current_event['name'].replace('Gameweek ', ''))

    transfers_payload = [{
        'element_in': player_in['id'],
        'element_out': player_out['id'],
        'purchase_price': player_in['now_cost'],
        'selling_price': selling_price,
    }]

    try:
        client.make_transfer(manager_id, transfers_payload, event_id)
    except Exception as e:
        return f'Transfer failed: {e}'

    cost_in = player_in['now_cost'] / 10
    cost_out = selling_price / 10
    return (
        f"Transfer confirmed: {player_out['web_name']} (£{cost_out:.1f}m) OUT → "
        f"{player_in['web_name']} (£{cost_in:.1f}m) IN for GW{event_id}."
    )


@tool
def set_lineup(starting_players: str, captain_name: str, vice_captain_name: str, bench_order: str) -> str:
    """Set your FPL lineup, captain, vice-captain, and bench order.
    starting_players: comma-separated names of 11 starting players.
    captain_name: name of captain.
    vice_captain_name: name of vice-captain.
    bench_order: comma-separated names of bench players in desired order.
    """
    client = fpl.get_auth_client()
    manager_id = client.get_manager_id()

    # Get current squad
    team_data = client.get_my_team(manager_id)
    elements = _get_bootstrap_elements()
    id_to_player = {p['id']: p for p in elements}

    squad_picks = team_data.get('picks', [])
    squad_players = []
    for pick in squad_picks:
        p = id_to_player.get(pick['element'], {})
        squad_players.append({
            'id': p.get('id', pick['element']),
            'web_name': p.get('web_name', ''),
            'first_name': p.get('first_name', ''),
            'second_name': p.get('second_name', ''),
            'element_type': p.get('element_type', 0),
            'multiplier': pick.get('multiplier', 1),
        })

    # Parse names
    starting_names = [n.strip() for n in starting_players.split(',') if n.strip()]
    bench_names = [n.strip() for n in bench_order.split(',') if n.strip()]

    if len(starting_names) != 11:
        return f'Need exactly 11 starting players, got {len(starting_names)}.'

    # Match names to squad
    starting_matched = []
    for name in starting_names:
        matched = _fuzzy_match_player(name, squad_players)
        if not matched:
            return f"Could not find '{name}' in your squad."
        starting_matched.append(matched)

    bench_matched = []
    for name in bench_names:
        matched = _fuzzy_match_player(name, squad_players)
        if not matched:
            return f"Could not find '{name}' in your squad."
        bench_matched.append(matched)

    # Validate formation
    pos_counts = {}
    for p in starting_matched:
        pos = p['element_type']
        pos_counts[pos] = pos_counts.get(pos, 0) + 1

    gkp = pos_counts.get(1, 0)
    defs = pos_counts.get(2, 0)
    mids = pos_counts.get(3, 0)
    fwds = pos_counts.get(4, 0)

    if gkp != 1:
        return f'Invalid formation: need exactly 1 GKP, got {gkp}.'
    if defs < 3:
        return f'Invalid formation: need at least 3 DEF, got {defs}.'
    if mids < 2:
        return f'Invalid formation: need at least 2 MID, got {mids}.'
    if fwds < 1:
        return f'Invalid formation: need at least 1 FWD, got {fwds}.'

    # Match captain/vc
    captain = _fuzzy_match_player(captain_name, squad_players)
    vice_captain = _fuzzy_match_player(vice_captain_name, squad_players)
    if not captain:
        return f"Could not find captain '{captain_name}' in your squad."
    if not vice_captain:
        return f"Could not find vice-captain '{vice_captain_name}' in your squad."

    # Build picks payload
    picks_payload = []
    for i, p in enumerate(starting_matched, 1):
        pick = {
            'element': p['id'],
            'position': i,
            'is_captain': p['id'] == captain['id'],
            'is_vice_captain': p['id'] == vice_captain['id'],
        }
        picks_payload.append(pick)

    for i, p in enumerate(bench_matched, 12):
        pick = {
            'element': p['id'],
            'position': i,
            'is_captain': p['id'] == captain['id'],
            'is_vice_captain': p['id'] == vice_captain['id'],
        }
        picks_payload.append(pick)

    try:
        client.set_lineup(manager_id, picks_payload)
    except Exception as e:
        return f'Setting lineup failed: {e}'

    formation = f'{defs}-{mids}-{fwds}'
    return (
        f"Lineup set ({formation}). Captain: {captain['web_name']}, "
        f"Vice-captain: {vice_captain['web_name']}. "
        f"Bench: {', '.join(p['web_name'] for p in bench_matched)}."
    )
