#!/usr/bin/env python3
import csv
import json
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from shared import is_interesting

CET = ZoneInfo('Europe/Paris')

# ZwiftInsider drops the "Watopia " prefix from route slugs
URL_SLUG_OVERRIDES = {
    'London PRL Full':        'the-prl-full',
    'London PRL Half':        'the-prl-half',
    'Watopia Figure 8':       'figure-8',
    'Watopia Flat Route':     'flat-route',
    'Watopia Hilly Route':    'hilly-route',
    'Watopia Mountain 8':     'mountain-8',
    'Watopia Mountain Route': 'mountain-route',
    'Watopia Pretzel':        'the-pretzel',
}

def route_url(name):
    if name in URL_SLUG_OVERRIDES:
        return f'https://zwiftinsider.com/route/{URL_SLUG_OVERRIDES[name]}/'
    slug = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r"[^a-z0-9 -]", '', slug)  # strip apostrophes, etc.
    slug = re.sub(r' +', '-', slug.strip())
    return f'https://zwiftinsider.com/route/{slug}/'

def fmt_time(iso):
    dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
    return dt.astimezone(CET).strftime('%Y-%m-%d %H:%M')

with open('events.json') as f:
    events = json.load(f)

with open('game.json') as f:
    game = json.load(f)

RIDERS = ['martin', 'nils', 'magnus']

completed_by_rider = {}
for rider in RIDERS:
    try:
        with open(f'completed-routes-{rider}.json') as f:
            completed_by_rider[rider] = json.load(f)
    except FileNotFoundError:
        # Fall back to the legacy single-rider file (martin's list).
        with open('completed-routes.json') as f:
            completed_by_rider[rider] = json.load(f)

try:
    with open('route-events.json') as f:
        route_events = json.load(f)
except FileNotFoundError:
    route_events = {}

three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)

def recent_event_count(route_name):
    entries = route_events.get(route_name, [])
    return sum(
        1 for e in entries
        if datetime.fromisoformat(e['eventStart'].replace('Z', '+00:00')) >= three_months_ago
    )

all_completed_by_rider = {rider: set(routes) for rider, routes in completed_by_rider.items()}

def canonical_route_name(route_name):
    if route_name == "Watopia Flat Route":
        return "Flat Route"
    if route_name == "Watopia Hilly Route":
        return "Hilly Route"
    return route_name

def is_completed(route_name, all_completed):
    return route_name in all_completed

route_map = {r['signature']: r for r in game['ROUTES']['ROUTE']}

EVENT_TYPE_LABELS = {
    'GROUP_RIDE': 'RIDE',
    'GROUP_WORKOUT': 'WRKO',
}

FIELDS = ['start', 'eventName', 'routeName', 'routeLength', 'routeElevation', 'routeBadge', 'eventType',
          'routeMap', 'duration', 'length', 'elevPerKm', 'recentEvents', 'laps', 'ruleSet', 'routeUrl',
          'eventOnly', 'xp', 'hasRouteBadge']

# note that "Repack Rush" is a very special route that you can get an achievement for even though it doesn't really
# have a normal route badge. Also there is a special case for "Handful of Gravel" vs "Handful of Gravel (cycling)".
def has_route_badge(route):
    loc_key = route.get('locKey', '')
    return (
        'xp' in route
        and int(route.get('sports', '0')) & 1
        and route.get('zwiftEventOnly') != '1'
        and loc_key.startswith('LOC_ROUTE_')
        and 'PORTAL' not in loc_key
    )

MAP_TO_WORLD = {
    'WATOPIA': 'Watopia',
    'LONDON': 'London',
    'RICHMOND': 'Richmond',
    'NEWYORK': 'New York',
    'INNSBRUCK': 'Innsbruck',
    'FRANCE': 'France',
    'PARIS': 'Paris',
    'MAKURIISLANDS': 'Makuri Islands',
    'SCOTLAND': 'Scotland',
    'YORKSHIRE': 'Yorkshire',
    'CRITCITY': 'Crit City',
    'BOLOGNATT': 'Bologna TT',
    'GRAVEL MOUNTAIN': 'Gravel Mountain',
}

for rider in RIDERS:
    all_completed = all_completed_by_rider[rider]
    out_dir = os.path.join('site', rider)
    os.makedirs(out_dir, exist_ok=True)

    rows_written = 0
    with open(os.path.join(out_dir, 'upcoming-banded.csv'), 'w', newline='') as f:
        writer = csv.writer(f)
        for event in events:
            if not is_interesting(event):
                continue
            route = route_map.get(str(event.get('routeId', '')), {})
            route_name = route.get('name', '')
            subgroups = event.get('eventSubgroups', [])
            all_rules = set(event.get('rulesSet', []))
            for sg in subgroups:
                all_rules.update(sg.get('rulesSet', []))
            rules = '|'.join(sorted(all_rules))
            raw_type = event.get('eventType', '')
            event_type = EVENT_TYPE_LABELS.get(raw_type, raw_type)
            route_length_km = round(float(route.get('distanceInMeters', 0)) / 1000, 1)
            route_elev_m = round(float(route.get('ascentInMeters', 0)))
            elev_per_km = round(route_elev_m / route_length_km, 1) if route_length_km else ''
            writer.writerow([
                fmt_time(event.get('eventStart', '')),
                event.get('name', ''),
                route_name,
                route_length_km,
                route_elev_m,
                '' if is_completed(route_name, all_completed) else 'n/a' if not has_route_badge(route) else 'NEED',
                event_type,
                route.get('map', ''),
                event.get('durationInSeconds', 0) // 60,
                round(event.get('distanceInMeters', 0) / 1000, 1),
                elev_per_km,
                recent_event_count(route_name),
                event.get('laps', ''),
                rules,
                route_url(route_name),
                'yes' if route.get('eventOnly') == '1' else '',
                route.get('xp', ''),
                'yes' if has_route_badge(route) else '',
            ])
            rows_written += 1

    print(f'Wrote {rows_written} rows to {out_dir}/upcoming-banded.csv')

    # --- badges.json ---

    worlds = {}
    for r in game['ROUTES']['ROUTE']:
        if not has_route_badge(r):
            continue
        map_key = r.get('map', '')
        world = MAP_TO_WORLD.get(map_key, map_key)
        if not world:
            continue
        route_name = r['name']
        worlds.setdefault(world, []).append({
            'name': route_name,
            'completed': route_name in all_completed,
            'distanceKm': round(float(r.get('distanceInMeters', 0)) / 1000, 1),
            'elevationM': round(float(r.get('ascentInMeters', 0))),
            'url': route_url(route_name),
        })

    badges = []
    for world, routes in worlds.items():
        routes_sorted = sorted(routes, key=lambda r: r['name'])
        completed_count = sum(1 for r in routes_sorted if r['completed'])
        badges.append({
            'world': world,
            'completedCount': completed_count,
            'totalCount': len(routes_sorted),
            'routes': routes_sorted,
        })

    badges.sort(key=lambda w: w['completedCount'], reverse=True)

    with open(os.path.join(out_dir, 'badges.json'), 'w') as f:
        json.dump(badges, f, indent=2, ensure_ascii=False)

    print(f'Wrote {out_dir}/badges.json ({len(badges)} worlds)')

    # --- per-rider pages (identical copies rendered from templates) ---
    shutil.copy('templates/upcoming.html', os.path.join(out_dir, 'index.html'))
    shutil.copy('templates/badges.html', os.path.join(out_dir, 'badges.html'))
    print(f'Rendered {out_dir}/index.html + {out_dir}/badges.html from templates/')
