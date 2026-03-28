#!/usr/bin/env python3
import csv
import json
from datetime import datetime
from zoneinfo import ZoneInfo

CET = ZoneInfo('Europe/Paris')

def fmt_time(iso):
    dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return dt.astimezone(CET).strftime('%Y-%m-%d %H:%M')

with open('events.json') as f:
    events = json.load(f)

with open('game.json') as f:
    game = json.load(f)

route_map = {r['signature']: r for r in game['ROUTES']['ROUTE']}

FIELDS = ['eventName', 'routeName', 'routeMap', 'eventStart', 'duration',
          'length', 'laps', 'ruleSet', 'sport']

with open('data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for event in events:
        route = route_map.get(str(event.get('routeId', '')), {})
        rules = '|'.join(event.get('rulesSet', []))
        writer.writerow([
            event.get('name', ''),
            route.get('name', ''),
            route.get('map', ''),
            fmt_time(event.get('eventStart', '')),
            event.get('durationInSeconds', 0) // 60,
            round(event.get('distanceInMeters', 0) / 1000, 1),
            event.get('laps', ''),
            rules,
            event.get('sport', ''),
        ])

print(f'Wrote {len(events)} rows to data.csv')
