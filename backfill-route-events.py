#!/usr/bin/env python3
"""Backfill route-events.json from all historical versions of events.json in git."""
import json
import subprocess
from shared import is_interesting

with open('game.json') as f:
    game_data = json.load(f)

route_map = {r['signature']: r for r in game_data['ROUTES']['ROUTE']}

try:
    with open('route-events.json') as f:
        route_events = json.load(f)
except FileNotFoundError:
    route_events = {}

commits = subprocess.check_output(
    ['git', 'log', '--format=%H', '--', 'events.json'],
    text=True
).splitlines()

print(f'Found {len(commits)} commits touching events.json')

all_events_by_id = {}
for commit in commits:
    blob = subprocess.check_output(['git', 'show', f'{commit}:events.json'])
    events = json.loads(blob)
    for event in events:
        eid = event.get('id')
        if eid and eid not in all_events_by_id:
            all_events_by_id[eid] = event

print(f'Found {len(all_events_by_id)} unique events across all versions')

added = 0
for event in all_events_by_id.values():
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

print(f'Updated route-events.json ({added} new entries, {sum(len(v) for v in route_events.values())} total)')
