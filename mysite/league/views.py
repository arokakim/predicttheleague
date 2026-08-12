from django.shortcuts import render, redirect, get_object_or_404
from .models import Team, MatchPrediction

def gameweek_builder(request, gw=1):
    """
    Displays matches for a specific Gameweek (1-38) and saves predictions.
    """
    # Ensure GW stays within valid Premier League bounds (1 to 38)
    gw = max(1, min(38, int(gw)))

    if request.method == "POST":
        # Handle saving predictions submitted from the form
        for key, value in request.POST.items():
            if key.startswith("prediction_"):
                match_id = key.split("_")[1]
                prediction_val = value if value in ['H', 'D', 'A'] else None
                
                MatchPrediction.objects.filter(id=match_id).update(prediction=prediction_val)
        
        # Redirect back to the same Gameweek page after saving
        return redirect('gameweek_builder_gw', gw=gw)

    # Fetch all 10 fixtures for the selected Gameweek
    matches = MatchPrediction.objects.filter(gameweek=gw).select_related('home_team', 'away_team')

    context = {
        'matches': matches,
        'current_gw': gw,
        'prev_gw': gw - 1 if gw > 1 else None,
        'next_gw': gw + 1 if gw < 38 else None,
        'all_gameweeks': range(1, 39),
    }
    return render(request, 'league/gameweek_builder.html', context)


def standings(request):
    """
    Calculates live standings based on saved predictions.
    Sorts by Points (Desc), then Team Name (A-Z).
    """
    teams = Team.objects.all()
    standings_data = []

    for team in teams:
        # Fetch all home and away matches where a prediction has been made
        home_matches = MatchPrediction.objects.filter(home_team=team).exclude(prediction__isnull=True).exclude(prediction='')
        away_matches = MatchPrediction.objects.filter(away_team=team).exclude(prediction__isnull=True).exclude(prediction='')

        played = home_matches.count() + away_matches.count()
        wins = 0
        draws = 0
        losses = 0
        points = 0

        # Calculate home performance
        for m in home_matches:
            if m.prediction == 'H':
                wins += 1
                points += 3
            elif m.prediction == 'D':
                draws += 1
                points += 1
            elif m.prediction == 'A':
                losses += 1

        # Calculate away performance
        for m in away_matches:
            if m.prediction == 'A':
                wins += 1
                points += 3
            elif m.prediction == 'D':
                draws += 1
                points += 1
            elif m.prediction == 'H':
                losses += 1

        standings_data.append({
            'team': team,
            'played': played,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'points': points,
        })

    # Primary sort: Points (descending), Secondary sort: Team Name (alphabetical A-Z)
    standings_data.sort(key=lambda x: (-x['points'], x['team'].name.lower()))

    return render(request, 'league/standings.html', {'standings': standings_data})


def match_focus(request, match_id):
    """
    Focus view for a single match fixture.
    """
    # Added .objects right before .select_related!
    match = get_object_or_404(
        MatchPrediction.objects.select_related('home_team', 'away_team'), 
        id=match_id
    )

    if request.method == "POST":
        prediction_val = request.POST.get('prediction')
        if prediction_val in ['H', 'D', 'A', '']:
            match.prediction = prediction_val if prediction_val != '' else None
            match.save()
        return redirect('match_focus', match_id=match.id)

    # Calculate surrounding context (Next match / Prev match in the same gameweek)
    same_gw_matches = list(MatchPrediction.objects.filter(gameweek=match.gameweek).values_list('id', flat=True))
    current_index = same_gw_matches.index(match.id)
    
    prev_match_id = same_gw_matches[current_index - 1] if current_index > 0 else None
    next_match_id = same_gw_matches[current_index + 1] if current_index < len(same_gw_matches) - 1 else None

    context = {
        'match': match,
        'prev_match_id': prev_match_id,
        'next_match_id': next_match_id,
    }
    return render(request, 'league/match_focus.html', context)