import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import json

def fetch_venue(match_url):
    """Extrahiert den Spielort von der Spielseite (robust)."""
    try:
        html = requests.get(match_url).text
        soup = BeautifulSoup(html, "html.parser")

        # Hauptselektor – funktioniert bei allen aktuellen fussball.de-Spielseiten
        loc = soup.select_one("a.location")
        if loc:
            text = loc.get_text(strip=True)
            if text:
                return text

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

            # Beispiel: "Mittwoch, 09.09.2026 - 19:30 Uhr"
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
            score_link = row.select_one(".column
