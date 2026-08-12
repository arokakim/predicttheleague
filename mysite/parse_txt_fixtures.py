import os
import django
import re
from datetime import datetime
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from league.models import Team, MatchPrediction

TEAM_ALIASES = {
    "Tottenham Hotspur": "Tottenham",
    "Tottenham Hotspur FC": "Tottenham",
    "Brighton & Hove Albion": "Brighton",
    "Brighton & Hove Albion FC": "Brighton",
    "Manchester City FC": "Manchester City",
    "Manchester United FC": "Manchester United",
    "Newcastle United FC": "Newcastle United",
    "Nottingham Forest FC": "Nottingham Forest",
    "Coventry City FC": "Coventry City",
    "Hull City FC": "Hull City",
    "Ipswich Town FC": "Ipswich Town",
    "Leicester City FC": "Leicester City",
    "Crystal Palace FC": "Crystal Palace",
    "Aston Villa FC": "Aston Villa",
    "Everton FC": "Everton",
    "Fulham FC": "Fulham",
    "Liverpool FC": "Liverpool",
    "Arsenal FC": "Arsenal",
    "Chelsea FC": "Chelsea",
    "Brentford FC": "Brentford",
    "Bournemouth FC": "Bournemouth",
    "Southampton FC": "Southampton",
    "West Ham FC": "West Ham",
    "Wolves FC": "Wolves",
    "Wolverhampton Wanderers": "Wolves",
    "AFC Bournemouth": "Bournemouth",
}

# Exact mapping to your static folder filenames inside static/league/logos/
LOCAL_LOGOS = {
    "Arsenal": "league/logos/arsenal-FC-v2002.png",
    "Aston Villa": "league/logos/aston-Villa-Football-Club-v2024.png",
    "Bournemouth": "league/logos/bournemouth-v2013.png",
    "Brentford": "league/logos/brentford-Football-Club-v2017.png",
    "Brighton": "league/logos/brighton-Hove-Albion-v2011.png",
    "Chelsea": "league/logos/chelsea-football-club-v2026.png",
    "Coventry City": "league/logos/coventry-city-football-club-v2012.png",
    "Crystal Palace": "league/logos/crystal-Palace-Football-Club-v2022.png",
    "Everton": "league/logos/everton-Football-Club-v2014.png",
    "Fulham": "league/logos/fulham-Football-Club-v2001.png",
    "Hull City": "league/logos/hull-city-association-football-club-v2014.png",
    "Ipswich Town": "league/logos/ipswich-Town-Football-Club-v1995.png",
    "Leeds United": "league/logos/leeds-United-v2002.png",
    "Liverpool": "league/logos/liverpool-Football-Club-v2024-minor.png",
    "Manchester City": "league/logos/manchester-City-v2016.png",
    "Manchester United": "league/logos/manchester-United-Football-Club-v1998.png",
    "Newcastle United": "league/logos/newcastle-United-Football-Club-v1988.png",
    "Nottingham Forest": "league/logos/nottingham-Forest-Football-Club-v2010.png",
    "Sunderland": "league/logos/sunderland-AFC-v1997.png",
    "Tottenham": "league/logos/tottenham-Hotspur-Football-Club-v2024.png",
}

def clean_team_name(name):
    name = name.strip()
    if name in TEAM_ALIASES:
        return TEAM_ALIASES[name]
    name = re.sub(r'\b(FC|AFC)\b', '', name).strip()
    return name

def get_team_logo(clean_name):
    # Returns relative path for Django static files tag
    return LOCAL_LOGOS.get(clean_name, "league/logos/default.png")

def parse_openfootball_txt(file_path='1-premierleague.txt'):
    print("Clearing old data and resetting primary key IDs to 1...")
    MatchPrediction.objects.all().delete()
    Team.objects.all().delete()

    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='league_team';")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='league_matchprediction';")

    print(f"Parsing raw text file: {file_path}...")
    
    current_matchday = 0
    current_date_str = None
    processed_count = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            matchday_match = re.search(r'Matchday\s+(\d+)', line, re.IGNORECASE)
            if matchday_match:
                current_matchday = int(matchday_match.group(1))
                continue

            date_match = re.search(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Za-z]{3})\s+(\d+)(?:\s+(\d{4}))?', line)
            if date_match:
                month_str = date_match.group(2)
                day_num = date_match.group(3)
                year_num = date_match.group(4) if date_match.group(4) else "2026"
                
                parsed_dt = datetime.strptime(f"{month_str} {day_num} {year_num}", "%b %d %Y")
                current_date_str = parsed_dt.strftime("%Y-%m-%d")
                continue

            if ' v ' in line:
                parts = line.split(' v ')
                left_part = parts[0].strip()
                away_raw = parts[1].strip()

                time_match = re.match(r'^(\d{1,2}:\d{2})\s+(.+)$', left_part)
                if time_match:
                    kickoff_time = time_match.group(1)
                    home_raw = time_match.group(2)
                else:
                    kickoff_time = None
                    home_raw = left_part

                home_name = clean_team_name(home_raw)
                away_name = clean_team_name(away_raw)

                home_team, _ = Team.objects.get_or_create(
                    name=home_name,
                    defaults={'logo_url': get_team_logo(home_name)}
                )
                away_team, _ = Team.objects.get_or_create(
                    name=away_name,
                    defaults={'logo_url': get_team_logo(away_name)}
                )

                MatchPrediction.objects.create(
                    gameweek=current_matchday,
                    home_team=home_team,
                    away_team=away_team,
                    match_date=current_date_str,
                    kickoff_time=kickoff_time
                )
                processed_count += 1

    print(f"SUCCESS: Seeding complete with local PNG paths!")

if __name__ == '__main__':
    parse_openfootball_txt()