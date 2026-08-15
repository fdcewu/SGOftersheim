import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import json

def fetch_matches(team_url):
    html = requests.get(team_url).text
    soup = BeautifulSoup(html, "html.parser")

    matches = []

    # JSON aus Script-Tag extrahieren
    for script in soup.find_all("script"):
        if "matchList" in script.text:
            data = script.text
            break

    start = data.find("{")
    end = data.rfind("}") + 1
    json_data = json.loads(data[start:end])

    for m in json_data["matchList"]:
        dt = datetime.fromisoformat(m["matchDate"])
        event = {
            "title": m["teamNameHome"] + " - " + m["teamNameAway"],
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

# Mannschaften laden
with open("teams.json", "r") as f:
    teams = json.load(f)

# Für jede Mannschaft eine ICS erzeugen
for team in teams:
    matches = fetch_matches(team["url"])
    cal = build_calendar(matches)

    filename = f"{team['name']}.ics"
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(cal)

    print(f"Erzeugt: {filename}")
