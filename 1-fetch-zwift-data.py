#!/usr/bin/env python3
import json
import urllib.request
from shared import is_interesting

BASE_URL = 'https://us-or-rly101.zwift.com/api/public/events/upcoming'
LIMIT = 200

all_events = []
start = 0

while True:
    url = f'{BASE_URL}?limit={LIMIT}&start={start}'
    print(f'Fetching {url}')
    with urllib.request.urlopen(url) as response:
        page = json.loads(response.read())
    if not page:
        break
    all_events.extend(page)
    if len(page) < LIMIT:
        break
    start += LIMIT

with open('events.json', 'w') as f:
    json.dump(all_events, f, indent=2)

print(f'Saved {len(all_events)} events to events.json')

GAME_DICT_URL = 'https://www.zwift.com/zwift-web-pages/gamedictionaryextended'
print(f'Fetching {GAME_DICT_URL}')
with urllib.request.urlopen(GAME_DICT_URL) as response:
    game_data = json.loads(response.read())

with open('game.json', 'w') as f:
    json.dump(game_data, f, indent=2)

print('Saved game.json')

# --- update route-events.json ---

route_map = {r['signature']: r for r in game_data['ROUTES']['ROUTE']}

try:
    with open('route-events.json') as f:
        route_events = json.load(f)
except FileNotFoundError:
    route_events = {}

added = 0
for event in all_events:
    if not is_interesting(event):
        continue
    route = route_map.get(str(event.get('routeId', '')), {})
    route_name = route.get('name', '')
    if not route_name:
        continue
    event_id = event.get('id')
    event_start = event.get('eventStart', '')
    entries = route_events.setdefault(route_name, [])
    existing_ids = {e['eventId'] for e in entries}
    if event_id not in existing_ids:
        entries.append({'eventId': event_id, 'eventStart': event_start})
        added += 1

with open('route-events.json', 'w') as f:
    json.dump(route_events, f, indent=2)

print(f'Updated route-events.json ({added} new entries)')
