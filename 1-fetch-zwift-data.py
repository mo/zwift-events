#!/usr/bin/env python3
import json
import urllib.request

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
