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

with open('completed-routes.json') as f:
    completed_routes = json.load(f)

all_completed = {route for routes in completed_routes.values() for route in routes}

def is_completed(route_name):
    return route_name in all_completed

route_map = {r['signature']: r for r in game['ROUTES']['ROUTE']}

EVENT_TYPE_LABELS = {
    'GROUP_RIDE': 'RIDE',
    'GROUP_WORKOUT': 'WORKOUT',
}

FIELDS = ['start', 'eventName', 'eventType', 'routeName', 'routeBadge', 'routeMap', 'duration',
          'length', 'routeLength', 'routeElevation', 'laps', 'ruleSet']

with open('site/data.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for event in events:
        if event.get('sport') != 'CYCLING':
            continue
        if 'TEST_BIT_10' not in event.get('rulesSet', []):
            continue
        if 'LADIES_ONLY' in event.get('rulesSet', []):
            continue
        route = route_map.get(str(event.get('routeId', '')), {})
        rules = '|'.join(event.get('rulesSet', []))
        raw_type = event.get('eventType', '')
        event_type = EVENT_TYPE_LABELS.get(raw_type, raw_type)
        writer.writerow([
            fmt_time(event.get('eventStart', '')),
            event.get('name', ''),
            event_type,
            route.get('name', ''),
            '' if is_completed(route.get('name', '')) else 'NEEDED',
            route.get('map', ''),
            event.get('durationInSeconds', 0) // 60,
            round(event.get('distanceInMeters', 0) / 1000, 1),
            round(float(route.get('distanceInMeters', 0)) / 1000, 1),
            round(float(route.get('ascentInMeters', 0))),
            event.get('laps', ''),
            rules,
        ])

print(f'Wrote {len(events)} rows to site/data.csv')
