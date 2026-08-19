from bs4 import BeautifulSoup
import requests

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .models import (
    MatchCommentary,
    MatchPrediction,
    Prediction,
    Team,
    UserProfile,
)
from .utils import calculate_league_table


def home_view(request):
    """
    Dashboard view showing live match info, upcoming fixtures, and user predictions.
    """
    if request.method == 'POST' and request.user.is_authenticated:
        match_id = request.POST.get('match_id')
        home_goals = request.POST.get('home_goals')
        away_goals = request.POST.get('away_goals')

        if match_id and home_goals != '' and away_goals != '' and home_goals is not None and away_goals is not None:
            match_obj = MatchPrediction.objects.filter(id=match_id).first()
            if match_obj and not getattr(match_obj, 'is_completed', False):
                Prediction.objects.update_or_create(
                    user=request.user,
                    match=match_obj,
                    defaults={
                        'home_goals': int(home_goals),
                        'away_goals': int(away_goals),
                    },
                )
                messages.success(
                    request,
                    f"Saved prediction for {match_obj.home_team.name} vs {match_obj.away_team.name}!",
                )
                return redirect('home')

    featured_match = (
        MatchPrediction.objects.filter(
            home_team__name__icontains="Arsenal",
            away_team__name__icontains="Manchester City",
        )
        .select_related('home_team', 'away_team')
        .first()
    )

    live_match = (
        MatchPrediction.objects.filter(is_live=True).first() or featured_match
    )

    live_commentary = []
    if live_match:
        live_commentary = MatchCommentary.objects.filter(
            match=live_match
        ).order_by('-minute')

    all_unplayed = MatchPrediction.objects.filter(
        home_goals__isnull=True
    ).select_related('home_team', 'away_team')
    
    first_unplayed = all_unplayed.first()
    current_gw = (
        getattr(first_unplayed, 'gameweek', 1) if first_unplayed else 1
    )

    upcoming_matches = all_unplayed.filter(gameweek=current_gw) if current_gw else all_unplayed[:6]

    teams = Team.objects.all()
    all_matches = MatchPrediction.objects.all().select_related('home_team', 'away_team')
    
    # Pass request.user if calculate_league_table supports user-specific predictions
    full_table = calculate_league_table(teams, all_matches) if teams and all_matches else []
    top_4_table = full_table[:4]

    user_predictions = []
    if request.user.is_authenticated:
        user_predictions = Prediction.objects.filter(
            user=request.user
        ).select_related('match__home_team', 'match__away_team')

    return render(
        request,
        'league/home.html',
        {
            'featured_match': featured_match,
            'live_match': live_match,
            'live_commentary': live_commentary,
            'upcoming_matches': upcoming_matches,
            'top_4_table': top_4_table,
            'user_predictions': user_predictions,
        },
    )


@login_required
def standings(request):
    """
    Renders the league table based on the logged-in user's predictions.
    """
    teams = Team.objects.all()
    matches = MatchPrediction.objects.select_related(
        'home_team',
        'away_team'
    ).all()

    standings_data = (
        calculate_league_table(teams, matches, request.user)
        if teams else []
    )

    return render(
        request,
        'league/standings.html',
        {'standings': standings_data}
    )

@login_required
def match_focus(request, match_id):
  match_obj = get_object_or_404(MatchPrediction, id=match_id)

  if request.method == 'POST':
    home_goals = request.POST.get('home_goals')
    away_goals = request.POST.get('away_goals')

    if home_goals != '' and away_goals != '':
        Prediction.objects.update_or_create(
            user=request.user,
            match=match_obj,
            defaults={
                'home_goals': int(home_goals),
                'away_goals': int(away_goals),
            }
        )

        messages.success(request, 'Prediction updated!')
        return redirect('match_focus', match_id=match_id)

  prev_match = (
      MatchPrediction.objects.filter(
          gameweek=match_obj.gameweek, id__lt=match_obj.id
      )
      .order_by('-id')
      .first()
  )
  next_match = (
      MatchPrediction.objects.filter(
          gameweek=match_obj.gameweek, id__gt=match_obj.id
      )
      .order_by('id')
      .first()
  )

  context = {
      'match': match_obj,
      'prev_match_id': prev_match.id if prev_match else None,
      'next_match_id': next_match.id if next_match else None,
  }
  return render(request, 'league/match_focus.html', context)


@login_required
def gameweek_builder(request, gw=1):
    # 1. Fetch all match fixtures for the current gameweek
    matches = MatchPrediction.objects.filter(gameweek=gw)

    # 2. Handle POST Request (Saving Predictions)
    if request.method == 'POST':
        for match in matches:
            home_val = request.POST.get(f'home_goals_{match.id}')
            away_val = request.POST.get(f'away_goals_{match.id}')

            # Only save/update if both fields have input values
            if home_val is not None and away_val is not None and home_val != '' and away_val != '':
                Prediction.objects.update_or_create(
                    user=request.user,
                    match=match,
                    defaults={
                        'home_goals': int(home_val),
                        'away_goals': int(away_val),
                    }
                )
        return redirect('gameweek_builder_gw', gw=gw)

    # 3. Fetch Existing Predictions for the Current User & Gameweek
    user_preds = Prediction.objects.filter(user=request.user, match__in=matches)
    predictions_map = {pred.match_id: pred for pred in user_preds}

    # 4. Pack Match + User Prediction into a single object for template loop
    match_data = [
        {
            'match': match,
            'prediction': predictions_map.get(match.id)
        }
        for match in matches
    ]

    # 5. Gameweek Navigation Bounds (1 to 38)
    context = {
        'current_gw': gw,
        'prev_gw': gw - 1 if gw > 1 else None,
        'next_gw': gw + 1 if gw < 38 else None,
        'match_data': match_data,
    }

    return render(request, 'league/gameweek_builder.html', context)

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        team_id = request.POST.get("favorite_team")

        if username and password:
            user = User.objects.create_user(username=username, password=password)
            fav_team = Team.objects.filter(id=team_id).first() if team_id else None
            UserProfile.objects.create(user=user, favorite_team=fav_team)

            login(request, user)
            return redirect('standings')

    teams = Team.objects.all().order_by('name')
    return render(request, 'league/register.html', {'teams': teams})


def leaderboard(request):
    profiles = UserProfile.objects.all()
    if hasattr(UserProfile, 'points'):
        profiles = profiles.order_by('-points')
    elif hasattr(UserProfile, 'total_points'):
        profiles = profiles.order_by('-total_points')

    return render(request, 'league/leaderboard.html', {'profiles': profiles})


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    teams = Team.objects.all().order_by('name')

    if request.method == 'POST':
        favorite_team_id = request.POST.get('favorite_team')
        password_hint = request.POST.get('password_hint', '')

        if favorite_team_id:
            profile.favorite_team = Team.objects.filter(id=favorite_team_id).first()

        if hasattr(profile, 'password_hint'):
            profile.password_hint = password_hint

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'league/profile.html', {'profile': profile, 'teams': teams})


def official_standings(request):
    """
    Fetches real-world Premier League standings via BBC web scraping with a fallback static dataset.
    """
    url = "https://www.bbc.com/sport/football/tables"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    table_data = []
    try:
        response = requests.get(url, headers=headers, timeout=4)
        soup = BeautifulSoup(response.content, 'html.parser')
        rows = soup.find_all('tr')[1:21]
        
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all(['th', 'td'])]
            if len(cols) >= 10:
                table_data.append({
                    'rank': cols[0],
                    'team': cols[1],
                    'mp': cols[2],
                    'w': cols[3],
                    'd': cols[4],
                    'l': cols[5],
                    'gf': cols[6],
                    'ga': cols[7],
                    'gd': cols[8],
                    'pts': cols[9],
                })
    except Exception as e:
        print(f"Scraper error: {e}")

    if not table_data:
        table_data = [
            {'rank': 1, 'team': 'Manchester City', 'mp': 38, 'w': 28, 'd': 7, 'l': 3, 'gf': 96, 'ga': 34, 'gd': 62, 'pts': 91},
            {'rank': 2, 'team': 'Arsenal', 'mp': 38, 'w': 28, 'd': 5, 'l': 5, 'gf': 91, 'ga': 29, 'gd': 62, 'pts': 89},
            {'rank': 3, 'team': 'Liverpool', 'mp': 38, 'w': 24, 'd': 10, 'l': 4, 'gf': 86, 'ga': 41, 'gd': 45, 'pts': 82},
            {'rank': 4, 'team': 'Aston Villa', 'mp': 38, 'w': 20, 'd': 8, 'l': 10, 'gf': 76, 'ga': 61, 'gd': 15, 'pts': 68},
        ]

    return render(request, 'league/official_standings.html', {'table': table_data})