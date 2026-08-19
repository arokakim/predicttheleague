import requests
from django.core.management.base import BaseCommand
from league.models import MatchPrediction
from league.utils import evaluate_user_predictions_for_match

class Command(BaseCommand):
    help = "Fetches live score updates from Football-Data.org API"

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, required=True, help='Your Football-Data.org API Token')

    def handle(self, *args, **options):
        api_key = options['api_key']
        
        # 1. Target live/in-play games specifically
        url = "https://api.football-data.org/v4/matches?status=IN_PLAY,PAUSED"
        headers = {"X-Auth-Token": api_key}

        self.stdout.write("Polling Football API for active live games...")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('matches', [])

                if not matches:
                    self.stdout.write(self.style.WARNING("No active matches in progress right now. Kickoff is scheduled for 5:00 PM EAT."))
                    return

                for match_data in matches:
                    home_name = match_data.get('homeTeam', {}).get('name', '')
                    away_name = match_data.get('awayTeam', {}).get('name', '')
                    status = match_data.get('status')

                    match = MatchPrediction.objects.filter(
                        home_team__name__icontains="Arsenal",
                        away_team__name__icontains="Manchester City"
                    ).first()

                    if match:
                        full_time = match_data.get('score', {}).get('fullTime', {})
                        home_goals = full_time.get('home')
                        away_goals = full_time.get('away')

                        if home_goals is not None and away_goals is not None:
                            match.home_goals = home_goals
                            match.away_goals = away_goals
                            match.is_live = (status in ['IN_PLAY', 'PAUSED'])
                            match.save()

                            self.stdout.write(self.style.SUCCESS(
                                f"Updated Live Score: {match.home_team.name} {home_goals} - {away_goals} {match.away_team.name} [{status}]"
                            ))

                        if status == 'FINISHED':
                            evaluate_user_predictions_for_match(match)
                            self.stdout.write(self.style.SUCCESS("Match finished! Calculated user prediction points."))

            else:
                self.stdout.write(self.style.ERROR(f"API Error ({response.status_code}): {response.text}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Connection failed: {e}"))