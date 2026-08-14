# league/utils.py (or top of views.py)

def compute_match_outcome(home_goals, away_goals):
    """
    Evaluates goal inputs and returns (outcome, home_pts, away_pts).
    outcome: 'H', 'D', or 'A'
    """
    if home_goals is None or away_goals is None:
        return None, 0, 0
        
    if home_goals > away_goals:
        return 'H', 3, 0
    elif away_goals > home_goals:
        return 'A', 0, 3
    else:
        return 'D', 1, 1


def calculate_league_table(teams, matches):
    """
    Aggregates goals, points, and standings for all teams in memory.
    """
    # 1. Initialize empty stat record for every team
    table = {
        team.id: {
            'team': team,
            'played': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'gf': 0,       # Goals For
            'ga': 0,       # Goals Against
            'gd': 0,       # Goal Difference
            'points': 0,
        }
        for team in teams
    }

    # 2. Iterate through matches once (O(M) complexity)
    for m in matches:
        # Determine scoreline (check goal input first, fallback to basic H/D/A tag)
        h_g = m.home_goals
        a_g = m.away_goals

        if h_g is not None and a_g is not None:
            outcome, h_pts, a_pts = compute_match_outcome(h_g, a_g)
        elif m.prediction:
            outcome = m.prediction
            h_g, a_g = 0, 0  # Fallback default if goals aren't set yet
            if outcome == 'H':
                h_pts, a_pts = 3, 0
            elif outcome == 'A':
                h_pts, a_pts = 0, 3
            else:
                h_pts, a_pts = 1, 1
        else:
            continue  # Match unplayed/unpredicted

        # Update Home Team
        home_stat = table[m.home_team.id]
        home_stat['played'] += 1
        home_stat['gf'] += h_g
        home_stat['ga'] += a_g
        home_stat['gd'] += (h_g - a_g)
        home_stat['points'] += h_pts
        if outcome == 'H': home_stat['wins'] += 1
        elif outcome == 'D': home_stat['draws'] += 1
        elif outcome == 'A': home_stat['losses'] += 1

        # Update Away Team
        away_stat = table[m.away_team.id]
        away_stat['played'] += 1
        away_stat['gf'] += a_g
        away_stat['ga'] += h_g
        away_stat['gd'] += (a_g - h_g)
        away_stat['points'] += a_pts
        if outcome == 'A': away_stat['wins'] += 1
        elif outcome == 'D': away_stat['draws'] += 1
        elif outcome == 'H': away_stat['losses'] += 1

    # 3. Convert dict to list
    standings_list = list(table.values())

    # 4. Multi-key Premier League Tie-Breaker Sort:
    # 1st: Points (desc) -> 2nd: GD (desc) -> 3rd: Goals For (desc) -> 4th: Name (asc)
    standings_list.sort(key=lambda x: (
        -x['points'],
        -x['gd'],
        -x['gf'],
        x['team'].name.lower()
    ))

    return standings_list