from django.shortcuts import render, redirect, get_object_or_404
from .models import Team, MatchPrediction
from .utils import calculate_league_table  # Import modular logic helper
from django.contrib.auth import login
from django.contrib.auth.models import User
from .models import Team, UserProfile


def standings(request):
    """
    Renders live standings with full PL tie-breakers (Points -> GD -> GF -> Name).
    Runs in 2 lightweight DB queries total.
    """
    teams = Team.objects.all()
    # Pre-fetch home and away teams in 1 query
    matches = MatchPrediction.objects.select_related('home_team', 'away_team').all()

    # Delegate all stats processing & tie-breaker sorting to utils
    standings_data = calculate_league_table(teams, matches)

    return render(request, 'league/standings.html', {'standings': standings_data})


def gameweek_builder(request, gw=1):
    """
    Handles score input (Home/Away goals) and prediction form submissions.
    """
    gw = max(1, min(38, int(gw)))

    if request.method == "POST":
        for key, value in request.POST.items():
            if value != '' and value is not None:
                # Handle numeric goal updates (e.g. home_goals_12 or away_goals_12)
                if key.startswith("home_goals_"):
                    m_id = key.split("_")[2]
                    MatchPrediction.objects.filter(id=m_id).update(home_goals=int(value))
                elif key.startswith("away_goals_"):
                    m_id = key.split("_")[2]
                    MatchPrediction.objects.filter(id=m_id).update(away_goals=int(value))
                # Fallback H/D/A radios
                elif key.startswith("prediction_"):
                    m_id = key.split("_")[1]
                    if value in ['H', 'D', 'A']:
                        MatchPrediction.objects.filter(id=m_id).update(prediction=value)

        return redirect('gameweek_builder_gw', gw=gw)

    matches = MatchPrediction.objects.filter(gameweek=gw).select_related('home_team', 'away_team')

    context = {
        'matches': matches,
        'current_gw': gw,
        'prev_gw': gw - 1 if gw > 1 else None,
        'next_gw': gw + 1 if gw < 38 else None,
        'all_gameweeks': range(1, 39),
    }
    return render(request, 'league/gameweek_builder.html', context)


def match_focus(request, match_id):
    """
    Focus view for an individual match fixture.
    """
    match = get_object_or_404(
        MatchPrediction.objects.select_related('home_team', 'away_team'), 
        id=match_id
    )

    if request.method == "POST":
        h_goals = request.POST.get('home_goals')
        a_goals = request.POST.get('away_goals')

        if h_goals is not None and a_goals is not None and h_goals != '' and a_goals != '':
            match.home_goals = int(h_goals)
            match.away_goals = int(a_goals)
            # Auto-assign prediction tag based on score
            if match.home_goals > match.away_goals:
                match.prediction = 'H'
            elif match.away_goals > match.home_goals:
                match.prediction = 'A'
            else:
                match.prediction = 'D'
            match.save()

        return redirect('match_focus', match_id=match.id)

    same_gw_matches = list(MatchPrediction.objects.filter(gameweek=match.gameweek).values_list('id', flat=True))
    current_index = same_gw_matches.index(match.id)

    context = {
        'match': match,
        'prev_match_id': same_gw_matches[current_index - 1] if current_index > 0 else None,
        'next_match_id': same_gw_matches[current_index + 1] if current_index < len(same_gw_matches) - 1 else None,
    }
    return render(request, 'league/match_focus.html', context)

def register(request):
    """
    Simple, anonymous sign-up requiring only username, password, and favorite team.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        team_id = request.POST.get("favorite_team")

        if username and password:
            # 1. Create standard Django User (No email required)
            user = User.objects.create_user(username=username, password=password)
            
            # 2. Attach Favorite Team Badge Profile
            fav_team = Team.objects.filter(id=team_id).first() if team_id else None
            UserProfile.objects.create(user=user, favorite_team=fav_team)

            # 3. Log the user in immediately
            login(request, user)
            return redirect('standings')

    teams = Team.objects.all().order_by('name')
    return render(request, 'league/register.html', {'teams': teams})