import requests
from ics import Calendar, Event
from datetime import datetime
import json

def fetch_matches(team_id):
    api_url = f"https://www.fussball.de/api/team-matches/{team_id}"
    response = requests.get(api_url)
    response.raise_for_status()

    data = response.json()
    matches = []

    for m in data.get("matches", []):
        dt = datetime.fromisoformat(m["matchDate"])

        event = {
            "title": f"{m['teamNameHome']} - {m['teamNameAway']}",
            "start": dt,
            "location": m.get("venue", "Unbekannt"),
            "league": m.get("competitionName", "")
        }
        matches.append(event)

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
    matches = fetch_matches(team["team_id"])
    cal = build_calendar(matches)

    filename = f"{team['name']}.ics"
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(cal)

    print(f"Erzeugt: {filename}")
