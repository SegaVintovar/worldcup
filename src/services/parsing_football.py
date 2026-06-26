import requests
import re
from bs4 import BeautifulSoup

url = "https://api.foxsports.com/bifrost/v1/soccer/league/schedule-segment/2026-20260628?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq"

# param = {
# 	2026-20260628?groupId=12&apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq
# }

headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(
    url,
    headers=headers
)
print(r.text)
# soup = BeautifulSoup(r.text, "html.parser")
# print(soup.select_one(".pill-comp.selected").get_text(strip=True))

# tr = soup.find_all("tr", id=re.compile(r"^tbl-row-"))

# for el in tr:
# 	home_team = el.find("td", attrs={"data-index": "0"}).find("img")
# 	away_team = el.find("td", attrs={"data-index": "2"}).find("img")
# 	print(f'{home_team} vs {away_team}')
