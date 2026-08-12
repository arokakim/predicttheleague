import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from league.models import Team, MatchPrediction

def run_seed():
    print("Clearing old data...")
    MatchPrediction.objects.all().delete()
    Team.objects.all().delete()

    # 20 Official 2026 Premier League Teams with Stadiums
    teams_data = [
        ("Arsenal", "Emirates Stadium"),
        ("Aston Villa", "Villa Park"),
        ("Bournemouth", "Vitality Stadium"),
        ("Brentford", "Gtech Community Stadium"),
        ("Brighton", "AMEX Stadium"),
        ("Chelsea", "Stamford Bridge"),
        ("Coventry City", "Coventry Building Society Arena"),
        ("Crystal Palace", "Selhurst Park"),
        ("Everton", "Goodison Park"),
        ("Fulham", "Craven Cottage"),
        ("Hull City", "MKM Stadium"),
        ("Ipswich Town", "Portman Road"),
        ("Leeds United", "Elland Road"),
        ("Liverpool", "Anfield"),
        ("Manchester City", "Etihad Stadium"),
        ("Manchester United", "Old Trafford"),
        ("Newcastle United", "St. James' Park"),
        ("Nottingham Forest", "City Ground"),
        ("Sunderland", "Stadium Of Light"),
        ("Tottenham", "Tottenham Hotspur Stadium"),
        
    ]

    print("Creating 20 teams...")
    created_teams = []
    for name, stadium in teams_data:
        team = Team.objects.create(
            name=name,
            stadium_name=stadium,
            logo_url=f"https://via.placeholder.com/50?text={name[:3].upper()}"  # Default placeholder logo
        )
        created_teams.append(team)

    print("Generating 380 round-robin fixtures into Unassigned Pool (GW 0)...")
    matches = []
    for home in created_teams:
        for away in created_teams:
            if home != away:
                matches.append(
                    MatchPrediction(
                        gameweek=0,
                        home_team=home,
                        away_team=away,
                        venue=home.stadium_name
                    )
                )

    MatchPrediction.objects.bulk_create(matches)
    print(f"SUCCESS: Created {Team.objects.count()} teams and {MatchPrediction.objects.count()} fixtures instantly!")

if __name__ == '__main__':
    run_seed()