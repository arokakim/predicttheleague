import requests
from django.core.management.base import BaseCommand
from league.models import Match
from league.utils import evaluate_user_predictions_for_match

class Command(BaseCommand):
    help = "Fetches finished match scores from the Football-Data API and triggers user prediction scoring."

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, help='Football-Data.org API Key')

    def handle(self, *args, **options):
        api_key = options.get('api_key')

        if not api_key:
            self.stdout.write(self.style.WARNING("No API key provided. Running mock calculation scan on existing completed matches..."))
            completed_matches = Match.objects.filter(home_goals__isnull=False, away_goals__isnull=False)
            count = 0
            for match in completed_matches:
                evaluate_user_predictions_for_match(match)
                count += 1
            self.stdout.write(self.style.SUCCESS(f"Successfully evaluated prediction points for {count} completed matches!"))
            return

        # Live API Call (Football-Data.org Premier League ID: 2021)
        url = "https://api.football-data.org/v4/competitions/PL/matches?status=FINISHED"
        headers = {"X-Auth-Token": api_key}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                updated_count = 0

                for api_match in data.get('matches', []):
                    home_score = api_match['score']['fullTime']['home']
                    away_score = api_match['score']['fullTime']['away']
                    
                    # Match by team names or external ID
                    match_obj = Match.objects.filter(
                        home_team__name__icontains=api_match['homeTeam']['shortName'],
                        away_team__name__icontains=api_match['awayTeam']['shortName']
                    ).first()

                    if match_obj and (match_obj.home_goals != home_score or match_obj.away_goals != away_score):
                        match_obj.home_goals = home_score
                        match_obj.away_goals = away_score
                        match_obj.save()

                        # Evaluate user points immediately upon match update
                        evaluate_user_predictions_for_match(match_obj)
                        updated_count += 1

                self.stdout.write(self.style.SUCCESS(f"Updated and scored {updated_count} matches from API!"))
            else:
                self.stdout.write(self.style.ERROR(f"API Error {response.status_code}: {response.text}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch scores: {str(e)}"))