#!/usr/bin/env python3
import json

with open('../zwift-data/7971732.json') as f:
    activities = json.load(f)

with open('game.json') as f:
    game = json.load(f)

# Build case-insensitive lookup: uppercase name -> canonical route name
route_lookup = {}
for r in game['ROUTES']['ROUTE']:
    route_lookup[r['name'].upper()] = r['name']

# Achievement names that don't match game.json names exactly
ALIASES = {
    'FLAT ROUTE':  'Watopia Flat Route',
    'HILLY ROUTE': 'Watopia Hilly Route',
    'PEAKY PAVE':  'Peaky Pavé',
}
route_lookup.update(ALIASES)

completed = set()

for activity in activities:
    moments = (activity.get('activityDetailsJson') or {}).get('notableMoments', [])
    for moment in moments:
        if moment.get('notableMomentTypeId') != 2:
            continue
        try:
            aux = json.loads(moment.get('aux1', '{}'))
        except (json.JSONDecodeError, TypeError):
            continue
        if aux.get('description') != 'Great work! Keep exploring!':
            continue
        name_upper = aux.get('name', '').upper()
        canonical = route_lookup.get(name_upper)
        if canonical:
            completed.add(canonical)

with open('completed-routes.json', 'w') as f:
    json.dump(sorted(completed), f, indent=4, ensure_ascii=False)

print(f'Found {len(completed)} completed routes')
for name in sorted(completed):
    print(f'  {name}')
