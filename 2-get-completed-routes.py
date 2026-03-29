#!/usr/bin/env python3
import json
import re

with open('../zwift-data/7971732.json') as f:
    activities = json.load(f)

PACER_BOTS = {'Maria', 'Coco', 'Miguel', 'Yumi', 'Bernie', 'Diesel', 'Jacques', 'Constance',
              'Taylor', 'Bowie', 'Silvia', 'Oscar', 'Edith', 'Ines', 'Pedro', 'Sofia',
              'Kirt', 'Roxy', 'Gertrude', 'Genie'}
PACER_BOT_RE = re.compile(r'\s+with\s+(' + '|'.join(PACER_BOTS) + r')$')

# "Route Name in World Name"
ROUTE_IN_WORLD = re.compile(r'^(.+?) in (.+)$')

def parse_route_world(text):
    m = ROUTE_IN_WORLD.match(text.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, None

completed = {}  # world -> set of routes

for activity in activities:
    route, world = None, None

    desc = (activity.get('activityDetailsJson') or {}).get('description', '')
    if desc and desc.startswith('🗺️ '):
        route, world = parse_route_world(desc[len('🗺️ '):])
    else:
        name = PACER_BOT_RE.sub('', activity.get('name', ''))
        # skip pure pacer group rides that have no route of interest
        if re.match(r'^Zwift - Pacer Group Ride\s*$', name):
            continue
        # strip "Pacer Group Ride: " prefix so route name parses correctly
        name = re.sub(r'^(Zwift - )Pacer Group Ride:\s+', r'\1', name)
        # "Zwift - Group Ride: <something> on <Route> in <World>"
        on_match = re.search(r' on (.+?) in (.+)$', name)
        if on_match:
            route = on_match.group(1).strip()
            world = on_match.group(2).strip()
        else:
            # "Zwift - <Route> in <World>"
            prefix_match = re.match(r'^Zwift - (.+)$', name)
            if prefix_match:
                route, world = parse_route_world(prefix_match.group(1))

    if route and world:
        completed.setdefault(world, set()).add(route)

output = {world: sorted(routes) for world, routes in sorted(completed.items())}

with open('completed-routes.json', 'w') as f:
    json.dump(output, f, indent=4, ensure_ascii=False)

total = sum(len(v) for v in output.values())
print(f'Found {total} completed routes across {len(output)} worlds')
for world, routes in output.items():
    print(f'  {world} ({len(routes)}): {", ".join(routes)}')
