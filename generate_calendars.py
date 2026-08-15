import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import json
import os

# ---------------------------------------------------------
# Unterverzeichnis für ICS-Dateien sicherstellen
# ---------------------------------------------------------
OUTPUT_DIR = "calendars"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# SPIELORT EXTRAKTION
# ---------------------------------------------------------
def fetch_venue(match_url):
    """Extrahiert den Spielort von der Spielseite (robust)."""
    if not match_url:
        return ""

    try:
        html = requests.get(match_url).text
        soup = BeautifulSoup(html, "html.parser")

        # Hauptselektor – funktioniert bei aktuellen fussball.de-Spielseiten
        loc = soup.select_one("a.location")
        if loc:
            return loc.get_text(strip=True)

        # Fallbacks für ältere oder mobile Seiten
        fallback_selectors = [
            ".venue-name",
            ".match-location",
            ".location-name",
            "div.venue",
            "span.venue",
            ".match-info-location"
        ]

        for sel in fallback_selectors:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text

    except Exception:
        pass

    return ""


# ---------------------------------------------------------
# SPIELE AUS MANNSCHAFTSSEITE LADEN
# ---------------------------------------------------------
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
        if row.select_one(".column-club"):
            clubs = row.select(".column-club .club-name")
            if len(clubs) < 2:
                continue

            home = clubs[0].get_text(strip=True)
            away = clubs[1].get_text(strip=True)

            # Link zur Spielseite → für Spielort
            score_link = row.select_one(".column-score a")
            match_url = score_link["href"] if score_link else ""

            venue = fetch_venue(match_url)

            matches.append({
                "title": f"{home} - {away}",
                "start": current_date,
                "end": current_date + timedelta(minutes=90),
                "league": current_competition,
                "location": venue
            })

    return matches


# ---------------------------------------------------------
# ICS ERZEUGEN
# ---------------------------------------------------------
def build_calendar(matches):
    cal = Calendar()
    for m in matches:
        e = Event()
        e.name = m["title"]
        e.begin = m["start"]
        e.end = m["end"]

        # WICHTIG: location darf NIE None sein
        e.location = m["location"] or ""

        # Liga als Beschreibung
        e.description = m["league"]

        cal.events.add(e)
    return cal


# ---------------------------------------------------------
# HAUPTPROGRAMM
# ---------------------------------------------------------
with open("teams.json", "r") as f:
    teams = json.load(f)

for team in teams:
    matches = fetch_matches(team["url"])
    print("Matches gefunden:", len(matches))

    cal = build_calendar(matches)

    filename = f"{OUTPUT_DIR}/{team['name']}.ics"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(cal.serialize())

    print(f"Erzeugt: {filename} (Events: {len(matches)})")
