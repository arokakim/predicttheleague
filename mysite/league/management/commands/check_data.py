import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps

class Command(BaseCommand):
    help = 'Validates database records for teams, badges, matches, and user profiles.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== PREMIER LEAGUE DATA VERIFICATION ===\n'))

        # Fetch models dynamically to avoid import name mismatches
        Team = apps.get_model('league', 'Team')
        
        # Try finding the match/fixture model dynamically
        MatchModel = None
        for model_name in ['Match', 'Fixture', 'Game', 'SingleMatch']:
            try:
                MatchModel = apps.get_model('league', model_name)
                break
            except LookupError:
                continue

        # Try finding the profile model dynamically
        ProfileModel = None
        for model_name in ['UserProfile', 'Profile', 'UserAccount']:
            try:
                ProfileModel = apps.get_model('league', model_name)
                break
            except LookupError:
                continue

        # 1. Validate Teams & Badges
        if Team:
            teams = Team.objects.all()
            team_count = teams.count()
            self.stdout.write(f"[*] Teams Found: {team_count}/20")
            
            missing_logos = 0
            for team in teams:
                logo_attr = getattr(team, 'logo_url', getattr(team, 'badge', None))
                if logo_attr:
                    logo_path = os.path.join(settings.BASE_DIR, 'static', str(logo_attr).lstrip('/'))
                    if not os.path.exists(logo_path):
                        self.stdout.write(self.style.WARNING(f"   [!] Missing logo file for {team.name}: {logo_attr}"))
                        missing_logos += 1

            if missing_logos == 0 and team_count > 0:
                self.stdout.write(self.style.SUCCESS("   [OK] All team logos exist in static files!"))
        else:
            self.stdout.write(self.style.ERROR("   [X] Team model not found."))

        # 2. Validate Fixtures / Matches
        if MatchModel:
            matches_count = MatchModel.objects.count()
            self.stdout.write(f"\n[*] Total Fixtures Logged ({MatchModel.__name__}): {matches_count}")
            if matches_count == 380:
                self.stdout.write(self.style.SUCCESS("   [OK] Complete 380-match season loaded!"))
            elif matches_count > 0:
                self.stdout.write(self.style.WARNING(f"   [!] Partial season loaded ({matches_count}/380 matches)."))
            else:
                self.stdout.write(self.style.ERROR("   [X] No matches found in database."))
        else:
            self.stdout.write(f"\n[*] Match/Fixture Model: Not detected under standard names.")

        # 3. Validate User Profiles
        if ProfileModel:
            profiles_count = ProfileModel.objects.count()
            self.stdout.write(f"\n[*] User Profiles Found ({ProfileModel.__name__}): {profiles_count}")
            for profile in ProfileModel.objects.all():
                user_obj = getattr(profile, 'user', profile)
                fav_team = getattr(getattr(profile, 'favorite_team', None), 'name', 'None')
                self.stdout.write(f"   - User: {getattr(user_obj, 'username', 'Unknown')} | Fav Team: {fav_team}")

        self.stdout.write(self.style.MIGRATE_HEADING('\n=== VERIFICATION COMPLETE ==='))