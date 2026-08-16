import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import json
import os
import time

OUTPUT_DIR = "calendars"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# Geocoding: Adresse → GPS Koordinaten (OpenStreetMap)
# ---------------------------------------------------------
def geocode(address):
    if not address:
        return None, None

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }

    try:
        r = requests.get(url, params=params, headers={"User-Agent": "SGO-CalendarBot"}).json()
        if r:
            return r[0]["lat"], r[0]["lon"]
    except Exception:
        pass

    return None, None

# ---------------------------------------------------------
# Spielort extrahieren
# ---------------------------------------------------------
def fetch_venue(match_url):
    if not match_url:
        return ""

    try:
        html = requests.get(match_url).text
        soup = BeautifulSoup(html, "html.parser")

        loc = soup.select_one("a.location")
        if loc:
            return loc.get_text(strip=True)

        fallback = [
            ".venue-name",
            ".match-location",
            ".location-name",
            "div.venue",
            "span.venue",
            ".match-info-location"
        ]

        for sel in fallback:
            el = soup.select_one(sel)
            if el:
                return el.get_text(strip=True)

    except Exception:
        pass

    return ""

# ---------------------------------------------------------
# Platzname + Adresse automatisch trennen
# ---------------------------------------------------------
def split_venue(venue):
    if not venue:
        return "", ""

    parts = [p.strip() for p in venue.split(",")]

    # Adresse beginnt dort, wo eine Zahl vorkommt
    for i, p in enumerate(parts):
        if any(char.isdigit() for char in p):
            name = ", ".join(parts[:i])
            address = ", ".join(parts[i:])
            return name, address

    return venue, ""

# ---------------------------------------------------------
# Spiele laden
# ---------------------------------------------------------
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
# ICS erzeugen
# ---------------------------------------------------------
def build_calendar(matches):
    cal = Calendar()
    for m in matches:
        e = Event()
        e.name = m["title"]
        e.begin = m["start"]
        e.end = m["end"]

        venue_name, venue_address = split_venue(m["location"])

        # GPS Koordinaten holen
        lat, lon = geocode(venue_address)
        time.sleep(1)  # Nominatim Rate Limit

        # LOCATION = nur Adresse (Apple Maps kompatibel)
        e.location = venue_address

        # DESCRIPTION = Liga + Platzname + Adresse + GPS + Links
        desc = m["league"]

        if venue_name:
            desc += f" – {venue_name}"

        if venue_address:
            desc += f"\nAdresse: {venue_address}"

        if lat and lon:
            desc += f"\nGPS: {lat}, {lon}"
            desc += f"\nGoogle Maps: https://maps.google.com/?q={lat},{lon}"
            desc += f"\nApple Maps: https://maps.apple.com/?q={lat},{lon}"

        e.description = desc

        cal.events.add(e)
    return cal

# ---------------------------------------------------------
# Hauptprogramm
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
