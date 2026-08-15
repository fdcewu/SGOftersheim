import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import json

def fetch_matches(team_url):
    html = requests.get(team_url).text
    soup = BeautifulSoup(html, "html.parser")

    matches = []

    # Neue fussball.de Struktur: Spiele stehen in div.match-row
    rows = soup.select("div.match-row")

    for row in rows:
        try:
            home = row.select_one(".team-home .team-name").get_text(strip=True)
            away = row.select_one(".team-away .team-name").get_text(strip=True)

            date_text = row.select_one(".match-date").get_text(strip=True)
            time_text = row.select_one(".match-time").get_text(strip=True)

            dt = datetime.strptime(f"{date_text} {time_text}", "%d.%m.%Y %H:%M")

            venue = row.select_one(".match-venue")
            venue = venue.get_text(strip=True) if venue else "Unbekannt"

            league = row.select_one(".match-league")
            league = league.get_text(strip=True) if league else ""

            matches.append({
                "title": f"{home} - {away}",
                "start": dt,
                "location": venue,
                "league": league
            })
        except Exception:
            continue

    return matches


def build_calendar(matches):
    cal = Calendar()
    for m in matches:
        e = Event()
        e.name = m["title"]
        e.begin = m["start"]
        e.location = m["location"]
        e.description = m["league"]
        cal.events.add(e)
    return cal


with open("teams.json", "r") as f:
    teams = json.load(f)

for team in teams:
    matches = fetch_matches(team["url"])
    cal = build_calendar(matches)

    filename = f"{team['name']}.ics"
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(cal)

    print(f"Erzeugt: {filename}")
