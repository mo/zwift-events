#!/usr/bin/env python3
import csv
import json

with open('events.json') as f:
    events = json.load(f)

with open('game.json') as f:
    game = json.load(f)

route_map = {r['signature']: r for r in game['ROUTES']['ROUTE']}

FIELDS = ['map', 'name', 'eventStart', 'durationInSeconds',
          'distanceInMeters', 'laps', 'ruleSet', 'sport', 'routeName']

with open('data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for event in events:
        route = route_map.get(str(event.get('routeId', '')), {})
        route_name = route.get('name', '')
        map_name = route.get('map', '')
        rules = '|'.join(event.get('rulesSet', []))
        writer.writerow([
            map_name,
            event.get('name', ''),
            event.get('eventStart', ''),
            event.get('durationInSeconds', ''),
            event.get('distanceInMeters', ''),
            event.get('laps', ''),
            rules,
            event.get('sport', ''),
            route_name,
        ])

print(f'Wrote {len(events)} rows to data.csv')
