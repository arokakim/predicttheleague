import re
from .models import UserProfile, Prediction


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


def calculate_league_table(teams, matches, user=None):
    """
    Aggregates goals, points, and standings for all teams in memory.
    Supports user-specific predictions if a user is passed.
    """
    table = {
        team.id: {
            'team': team,
            'played': 0,
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'gf': 0,
            'ga': 0,
            'gd': 0,
            'points': 0,
        }
        for team in teams
    }

    # Fetch user-specific predictions if user is logged in
    user_preds = {}
    if user and getattr(user, 'is_authenticated', False):
        user_preds = {
            p.match_id: p
            for p in Prediction.objects.filter(user=user).select_related('match')
        }

    for m in matches:
        h_g, a_g = None, None

        # Priority 1: Logged-in user's saved prediction
        if m.id in user_preds:
            h_g = user_preds[m.id].home_goals
            a_g = user_preds[m.id].away_goals

        # Priority 2: Direct goals on MatchPrediction model
        elif m.home_goals is not None and m.away_goals is not None:
            h_g = m.home_goals
            a_g = m.away_goals

        # Evaluate outcome if valid scores exist
        if h_g is not None and a_g is not None:
            outcome, h_pts, a_pts = compute_match_outcome(h_g, a_g)
        else:
            continue  # Skip unplayed and unpredicted matches

        # Safety check for valid team IDs
        if m.home_team_id not in table or m.away_team_id not in table:
            continue

        # Update Home Team
        home_stat = table[m.home_team_id]
        home_stat['played'] += 1
        home_stat['gf'] += h_g
        home_stat['ga'] += a_g
        home_stat['gd'] += (h_g - a_g)
        home_stat['points'] += h_pts
        if outcome == 'H':
            home_stat['wins'] += 1
        elif outcome == 'D':
            home_stat['draws'] += 1
        elif outcome == 'A':
            home_stat['losses'] += 1

        # Update Away Team
        away_stat = table[m.away_team_id]
        away_stat['played'] += 1
        away_stat['gf'] += a_g
        away_stat['ga'] += h_g
        away_stat['gd'] += (a_g - h_g)
        away_stat['points'] += a_pts
        if outcome == 'A':
            away_stat['wins'] += 1
        elif outcome == 'D':
            away_stat['draws'] += 1
        elif outcome == 'H':
            away_stat['losses'] += 1

    standings_list = list(table.values())

    # Multi-key Premier League Tie-Breaker Sort: Points -> GD -> GF -> Name
    standings_list.sort(key=lambda x: (
        -x['points'],
        -x['gd'],
        -x['gf'],
        x['team'].name.lower()
    ))

    return standings_list


def evaluate_user_predictions_for_match(match):
    """
    Compares real finished match scorelines against submitted user predictions
    and updates global UserProfile leaderboard points.
    """
    if match.home_goals is None or match.away_goals is None:
        return

    actual_outcome, _, _ = compute_match_outcome(match.home_goals, match.away_goals)

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

        if pred_home == match.home_goals and pred_away == match.away_goals:
            points_awarded = 3
        elif pred_outcome == actual_outcome:
            points_awarded = 1

        profile, _ = UserProfile.objects.get_or_create(user=pred.user)
        current_pts = getattr(profile, 'points', 0) or 0
        profile.points = current_pts + points_awarded
        profile.save()

        if hasattr(pred, 'is_scored'):
            pred.is_scored = True
            pred.save()


def normalize_team_name(name: str) -> str:
    """
    Cleans team names by removing common suffixes, punctuation, and extra whitespace.
    """
    if not name:
        return ""
    cleaned = re.sub(r'\b(FC|F\.C\.|AFC|A\.F\.C\.)\b', '', name, flags=re.IGNORECASE)
    return cleaned.strip().lower()