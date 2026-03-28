#!/usr/bin/env python3
import csv
import json

with open('events.json') as f:
    events = json.load(f)

with open('game.json') as f:
    game = json.load(f)

route_map = {r['signature']: r for r in game['ROUTES']['ROUTE']}

FIELDS = ['eventName', 'routeName', 'routeMap', 'eventStart', 'durationInSeconds',
          'distanceInMeters', 'laps', 'ruleSet', 'sport']

with open('data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for event in events:
        route = route_map.get(str(event.get('routeId', '')), {})
        rules = '|'.join(event.get('rulesSet', []))
        writer.writerow([
            event.get('name', ''),
            route.get('name', ''),
            route.get('map', ''),
            event.get('eventStart', ''),
            event.get('durationInSeconds', ''),
            event.get('distanceInMeters', ''),
            event.get('laps', ''),
            rules,
            event.get('sport', ''),
        ])

print(f'Wrote {len(events)} rows to data.csv')
