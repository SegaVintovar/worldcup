import requests
from datetime import datetime
from src.services.database import Match, SessionLocal

COUNTRY = {
    "Mexico": "Mexico",
    "South Korea": "South Korea",
    "Czechia": "Czech Republic",
    "South Africa": "South Africa",
    "Switzerland": "Switzerland",
    "Canada": "Canada",
    "Qatar": "Qatar",
    "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Brazil": "Brazil",
    "Morocco": "Morocco",
    "Scotland": "Scotland",
    "Haiti": "Haiti",
    "United States": "USA",
    "Turkey": "Turkey",
    "Australia": "Australia",
    "Paraguay": "Paraguay",
    "Germany": "Germany",
    "Ecuador": "Ecuador",
    "Ivory Coast": "Ivory Coast",
    "Curaçao": "Curaçao",
    "Netherlands": "Netherlands",
    "Japan": "Japan",
    "Sweden": "Sweden",
    "Tunisia": "Tunisia",
    "Belgium": "Belgium",
    "Iran": "Iran",
    "Egypt": "Egypt",
    "New Zealand": "New Zealand",
    "Spain": "Spain",
    "Uruguay": "Uruguay",
    "Saudi Arabia": "Saudi Arabia",
    "Cape Verde": "Cape Verde",
    "France": "France",
    "Senegal": "Senegal",
    "Norway": "Norway",
    "Iraq": "Iraq",
    "Argentina": "Argentina",
    "Austria": "Austria",
    "Algeria": "Algeria",
    "Jordan": "Jordan",
    "Portugal": "Portugal",
    "Colombia": "Colombia",
    "Congo DR": "DR Congo",
    "Uzbekistan": "Uzbekistan",
    "England": "England",
    "Croatia": "Croatia",
    "Panama": "Panama",
    "Ghana": "Ghana",

    # playoff shorthand mappings
    "3CEFHI": "3C/E/F/H/I",
    "3AEHIJ": "3A/E/H/I/J",
    "3BEFIJ": "3B/E/F/I/J",
    "3CEFGHI": "3C/E/F/G/H/I",
    "3EFGIJ": "3E/F/G/I/J",

    "1I": "1I",
    "1L": "1L",
    "1G": "1G",
    "2J": "2J",
    "2K": "2K",
    "2L": "2L",
    "2I": "2I",
    "2G": "2G"
}

URLS = ["https://api.foxsports.com/bifrost/v1/soccer/league/schedule-segment/2026-20260628?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq",
        "https://api.foxsports.com/bifrost/v1/soccer/league/schedule-segment/2026-20260704?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq",
        "https://api.foxsports.com/bifrost/v1/soccer/league/schedule-segment/2026-20260709?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq",
        "https://api.foxsports.com/bifrost/v1/soccer/league/schedule-segment/2026-20260714?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq",
        "https://api.foxsports.com/bifrost/v1/soccer/league/schedule-segment/2026-20260718?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq",
        "https://api.foxsports.com/bifrost/v1/soccer/league/schedule-segment/2026-20260719?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq"]


def getting_data() -> list[tuple]:
    res: list[tuple] = []
    football_match: list[dict] = []
    headers: dict = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    for url in URLS:
        football_match = requests.get(
            url,
            headers=headers).json()

        for table in football_match['tables']:
            for row in table['rows']:
                home_team = row['columns'][0]['imageAltText'] if row['columns'][0]['imageAltText'].strip() != "Default Logo" else row['columns'][0]['text']
                away_team = row['columns'][2]['imageAltText'] if row['columns'][2]['imageAltText'].strip() != "Default Logo" else row['columns'][2]['text']
                time = row['columns'][3]['text']
                time = datetime.fromisoformat(time.replace("Z", "+00:00"))
                res.append((home_team.strip(),
                            away_team.strip(),
                            time))
    return res


def match_the_data(db):
    matches: list[Match]
    current_data = getting_data()
    for h, a, t in current_data:
        matches = db.query(Match).filter(Match.match_date == t).all()
        for m in matches:
            if (m.home_team.lower().strip() != COUNTRY[h].lower().strip() or
                m.away_team.lower().strip() != COUNTRY[a].lower().strip()):
                print(f"{m.home_team} vs {m.away_team} -> {h} vs {a}")
