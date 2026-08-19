from django.core.management.base import BaseCommand
from league.models import MatchPrediction
from league.utils import evaluate_user_predictions_for_match

class Command(BaseCommand):
    help = "Simulates an API score update for Arsenal vs Manchester City and evaluates predictions."

    def add_arguments(self, parser):
        parser.add_argument('--home', type=int, default=2, help='Arsenal goals')
        parser.add_argument('--away', type=int, default=1, help='Man City goals')

    def handle(self, *args, **options):
        home_score = options['home']
        away_score = options['away']

        # Find the specific match record
        match = MatchPrediction.objects.filter(
            home_team__name__icontains="Arsenal",
            away_team__name__icontains="Manchester City"
        ).first()

        if not match:
            self.stdout.write(self.style.ERROR("Arsenal vs Manchester City match record not found!"))
            return

        # 1. Update Match Scores (Simulating API response)
        match.home_goals = home_score
        match.away_goals = away_score
        match.is_live = False
        match.save()

        self.stdout.write(self.style.SUCCESS(f"Updated Match #{match.id}: Arsenal {home_score} - {away_score} Man City"))

        # 2. Trigger Scorer Logic
        evaluate_user_predictions_for_match(match)
        self.stdout.write(self.style.SUCCESS("Evaluated all user predictions! Check the Leaderboard."))