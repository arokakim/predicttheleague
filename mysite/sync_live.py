import os
import django
import requests
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from league.models import MatchPrediction, MatchCommentary
from league.models import MatchCommentary, MatchPrediction
from league.utils import (
    evaluate_user_predictions_for_match,
    normalize_team_name,
)


API_KEY = "8b1766b449cf44bab312de53c7128a7e"
HEADERS = {'X-Auth-Token': API_KEY}

def normalize_team_name(name):
    cleaned = re.sub(r'\b(FC|F\.C\.|AFC|A\.F\.C\.)\b', '', name or "", flags=re.IGNORECASE)
    return cleaned.strip().lower()

def sync_completed_or_live_data():
    match_obj = MatchPrediction.objects.filter(is_live=True).first()
    if not match_obj:
        print("No active match marked as is_live=True in local database.")
        return

    # Check live matches first; fallback to today's finished matches
    url = "https://api.football-data.org/v4/matches?status=IN_PLAY"
    try:
        response = requests.get(url, headers=HEADERS)
        matches_data = response.json().get('matches', []) if response.status_code == 200 else []
    except Exception as e:
        print("Network error on IN_PLAY endpoint:", e)
        matches_data = []

    # If no live matches found or API rate-limited, query finished matches feed
    if not matches_data:
        url_finished = "https://api.football-data.org/v4/matches?status=FINISHED"
        try:
            res_fin = requests.get(url_finished, headers=HEADERS)
            if res_fin.status_code == 200:
                matches_data = res_fin.json().get('matches', [])
        except Exception as e:
            print("Network error on FINISHED endpoint:", e)

    local_home_norm = normalize_team_name(match_obj.home_team.name)
    local_away_norm = normalize_team_name(match_obj.away_team.name)

    matched_fixture = None
    for fixture in matches_data:
        api_home_norm = normalize_team_name(fixture['homeTeam']['name'])
        api_away_norm = normalize_team_name(fixture['awayTeam']['name'])

        # Check normalized substring overlap
        if (local_home_norm in api_home_norm or api_home_norm in local_home_norm) or \
           (local_away_norm in api_away_norm or api_away_norm in local_away_norm):
            matched_fixture = fixture
            break

    if matched_fixture:
        score_data = matched_fixture.get('score', {})
        full_time = score_data.get('fullTime', {})
        
        home_g = full_time.get('home', 0) if full_time.get('home') is not None else 0
        away_g = full_time.get('away', 0) if full_time.get('away') is not None else 0
        status = matched_fixture.get('status')

        match_obj.home_goals = home_g
        match_obj.away_goals = away_g

        if status == 'FINISHED':
            match_obj.minute = 90
            match_obj.is_live = False
            match_obj.is_completed = True
            match_obj.save()

            # Record final whistle commentary
            MatchCommentary.objects.get_or_create(
                match=match_obj,
                minute=90,
                event_type='FULL_TIME',
                defaults={'description': f"FULL TIME: {match_obj.home_team.name} {home_g} - {away_g} {match_obj.away_team.name}"}
            )
            print(f"\n[MATCH FINISHED]: Updated DB -> {match_obj.home_team.name} {home_g} - {away_g} {match_obj.away_team.name} (Final Score)")
        else:
            match_obj.minute = matched_fixture.get('minute', 1)
            match_obj.save()
            print(f"\n[LIVE SYNCED]: {match_obj.home_team.name} {home_g} - {away_g} {match_obj.away_team.name} ({match_obj.minute}')")
    else:
        print(f"\n[INFO] No match found matching local normalized names '{local_home_norm}' / '{local_away_norm}'.")

if __name__ == "__main__":
    sync_completed_or_live_data()