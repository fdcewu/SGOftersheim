import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import json

def fetch_matches(team_url):
    if "#!" in team_url:
        team_url = team_url.split("#!")[0]

    html = requests.get(team_url).text
    soup = BeautifulSoup(html, "html.parser")

    matches = []
    current_date = None
    current_competition = None

    for row in soup.select("tr"):
        if "row-headline" in row.get("class", []):
            headline = row.get_text(" ", strip=True)
            parts = headline.split("|")

            date_part = parts[0].strip()
            comp_part = parts[1].strip() if len(parts) > 1 else ""

            raw = date_part.replace("Uhr", "").strip()

            if "," in raw:
                raw = raw.split(",", 1)[1].strip()

            if "-" in raw:
                dt = datetime.strptime(raw, "%d.%m.%Y - %H:%M")
            else:
                dt = datetime.strptime(raw, "%d.%m.%Y")

            current_date = dt
            current_competition = comp_part
            continue

        if row.select_one(".column-club"):
            clubs = row.select(".column-club .club-name")
            if len(clubs) < 2:
                continue

            home = clubs[0].get_text(strip=True)
            away = clubs[1].get_text(strip=True)

            matches.append({
                "title": f"{home} - {away}",
                "start": current_date,
                "end": current_date + timedelta(minutes=90),
                "league": current_competition
            })

    return matches


def build_calendar(matches):
    cal = Calendar()
    for m in matches:
        e = Event()
        e.name = m["title"]
        e.begin = m["start"]
        e.end = m["end"]
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
        f.write(cal.serialize())

    print(f"Erzeugt: {filename} (Events: {len(matches)})")
