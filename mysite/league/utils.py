# league/utils.py

from .models import UserProfile  # Adjust model import if needed

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


# ==========================================
# NEW: USER LEADERBOARD SCORING ENGINE
# ==========================================

def evaluate_user_predictions_for_match(match):
    """
    Compares real finished match scorelines against submitted user predictions
    and updates global UserProfile leaderboard points.
    
    Rules:
    - Exact Score (e.g. Pred 2-1, Result 2-1): 3 Points
    - Correct Outcome (e.g. Pred 2-0, Result 3-1): 1 Point
    - Incorrect Outcome: 0 Points
    """
    if match.home_goals is None or match.away_goals is None:
        return

    actual_outcome, _, _ = compute_match_outcome(match.home_goals, match.away_goals)

    # Grab predictions associated with this match
    predictions = getattr(match, 'predictions', None) or getattr(match, 'prediction_set', None)
    if not predictions:
        return

    for pred in predictions.all():
        if getattr(pred, 'is_scored', False):
            continue

        pred_home = pred.home_goals
        pred_away = pred.away_goals

        if pred_home is None or pred_away is None:
            continue

        pred_outcome, _, _ = compute_match_outcome(pred_home, pred_away)
        points_awarded = 0

        # Exact Scoreline Bonus
        if pred_home == match.home_goals and pred_away == match.away_goals:
            points_awarded = 3
        # Correct Outcome Bonus
        elif pred_outcome == actual_outcome:
            points_awarded = 1

        # Award points to user profile
        profile, _ = UserProfile.objects.get_or_create(user=pred.user)
        current_pts = getattr(profile, 'points', 0) or 0
        profile.points = current_pts + points_awarded
        profile.save()

        # Mark prediction as scored
        if hasattr(pred, 'is_scored'):
            pred.is_scored = True
            pred.save()