import json
import urllib.request
import urllib.parse
import sys

def fetch_live_events():
    url = "https://api.infersports.dev/v1/events?sport=football"
    req = urllib.request.Request(url, headers={'User-Agent': 'infersports-skill/python'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())['data']
    except Exception as e:
        print(f"Error fetching events from InferSports: {e}")
        return []

def fetch_event_odds(event_id):
    url = f"https://api.infersports.dev/v1/events/{event_id}/odds"
    req = urllib.request.Request(url, headers={'User-Agent': 'infersports-skill/python'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())['odds']
    except Exception as e:
        print(f"Error fetching odds for {event_id}: {e}")
        return []

def main():
    print("🔄 InferSports Real-time Odds Sync Utility")
    events = fetch_live_events()
    print(f"Found {len(events)} active events on InferSports.")
    
    # We can match these against matches.json to sync odds automatically
    # This utility demonstrates the connection and mapping layer.
    for ev in events[:5]:
        home = ev['home_team']['name']
        away = ev['away_team']['name']
        eid = ev['id']
        print(f"Event {eid}: {home} vs {away}")
        odds = fetch_event_odds(eid)
        # Group by bookmakers
        books = set(o['bookmaker'] for o in odds)
        print(f"  Available books: {', '.join(books)}")

if __name__ == "__main__":
    main()
