import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import json

def fetch_venue(match_url):
    """Extrahiert den Spielort von der Spielseite."""
    try:
        html = requests.get(match_url).text
        soup = BeautifulSoup(html, "html.parser")
        venue_el = soup.select_one(".venue-name")
        if venue_el:
            return venue_el.get_text(strip=True)
    except:
        pass
    return "Unbekannt"


def fetch_matches(team_url):
    html = requests.get(team_url).text
    soup = BeautifulSoup(html, "html.parser")

    matches = []
    current_date = None
    current_competition = None

    for row in soup.select("tr"):
        # 1. row-headline → Datum + Uhrzeit + Wettbewerb
        if "row-headline" in row.get("class", []):
            headline = row.get_text(" ", strip=True)
            parts = headline.split("|")
            date_part = parts[0].strip()
            comp_part = parts[1].strip() if len(parts) > 1 else ""

            date_text = date_part.split(",")[1].strip()
            date_text = date_text.replace("Uhr", "").strip()
            dt = datetime.strptime(date_text, "%d.%m.%Y - %H:%M")

            current_date = dt
            current_competition = comp_part
            continue

        # 2. echte Spielzeile → Teams + Spiel-URL
        if row.select_one(".column-club"):
            clubs = row.select(".column-club .club-name")
            if len(clubs) < 2:
                continue

            home = clubs[0].get_text(strip=True)
            away = clubs[1].get_text(strip=True)

            # Spiel-URL
            score_link = row.select_one(".column-score a")
            match_url = score_link["href"] if score_link else ""

            # Spielort extrahieren
            venue = fetch_venue(match_url)

            matches.append({
                "title": f"{home} - {away}",
                "start": current_date,
                "end": current_date + timedelta(minutes=90),
                "location": venue,
                "league": current_competition,
                "url": match_url
            })

    return matches


def build_calendar(matches):
    cal = Calendar()
    for m in matches:
        e = Event()
        e.name = m["title"]
        e.begin = m["start"]
        e.end = m["end"]
        e.location = m["location"]
        e.description = f"{m['league']}\n{m['url']}"
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
