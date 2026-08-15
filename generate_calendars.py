import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import json

def fetch_matches(team_url):
    html = requests.get(team_url).text
    soup = BeautifulSoup(html, "html.parser")

    matches = []

    # Neue fussball.de Struktur: Spiele stehen in div.match
    rows = soup.select("div.match")

    for row in rows:
        try:
            # Teamnamen
            teams = row.select(".team-name")
            if len(teams) < 2:
                continue
            home = teams[0].get_text(strip=True)
            away = teams[1].get_text(strip=True)

            # Datum + Uhrzeit
            date_el = row.select_one(".match-date")
            time_el = row.select_one(".match-time")

            if not date_el or not time_el:
                continue

            date_text = date_el.get_text(strip=True)
            time_text = time_el.get_text(strip=True)

            dt = datetime.strptime(f"{date_text} {time_text}", "%d.%m.%Y %H:%M")

            # Spielort
            venue_el = row.select_one(".venue")
            venue = venue_el.get_text(strip=True) if venue_el else "Unbekannt"

            # Liga / Wettbewerb
            league_el = row.select_one(".competition-name")
            league = league_el.get_text(strip=True) if league_el else ""

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
