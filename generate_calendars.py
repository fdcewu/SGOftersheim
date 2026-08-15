import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import json

def fetch_matches(team_url):
    """Liest alle Spiele einer Mannschaft aus der fussball.de-Mannschaftsseite."""

    # Hash-Fragment entfernen (#!/)
    if "#!" in team_url:
        team_url = team_url.split("#!")[0]

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

            # Beispiel:
            # "Mittwoch, 09.09.2026 - 19:30 Uhr"
            # oder:
            # "09.09.2026 - 19:30 Uhr"

            raw = date_part.replace("Uhr", "").strip()

            # Wochentag entfernen, falls vorhanden
            if "," in raw:
                raw = raw.split(",", 1)[1].strip()

            # Uhrzeit vorhanden?
            if "-" in raw:
                dt = datetime.strptime(raw, "%d.%m.%Y - %H:%M")
            else:
                dt = datetime.strptime(raw, "%d.%m.%Y")

            current_date = dt
            current_competition = comp_part
            continue

        # 2. echte Spielzeile → Teams
        if row.select_one
