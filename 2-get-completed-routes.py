#!/usr/bin/env python3
import json
import os

# Rider name -> Zwift user id (activity dump in ../zwift-data/<id>.json).
RIDERS = {
    'martin': 7971732,
    'nils': 8010919,
    'magnus': 6918489,
}

ZWIFT_DATA_DIR = os.environ.get('ZWIFT_DATA_DIR', '../zwift-data')

with open('game.json') as f:
    game = json.load(f)

route_by_sig = {r['signature']: r for r in game['ROUTES']['ROUTE']}
route_name_by_ach_id = {
    a['signature']: route_by_sig[a['routeSignature']]['name']
    for a in game['ACHIEVEMENTS']['ACHIEVEMENT']
    if a.get('imageName') == 'RouteComplete' and a.get('routeSignature') in route_by_sig
}


def completed_routes_for(activities):
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
            name = route_name_by_ach_id.get(str(aux.get('achievementId')))
            if name:
                completed.add(name)
    return sorted(completed)


for rider, user_id in RIDERS.items():
    with open(os.path.join(ZWIFT_DATA_DIR, f'{user_id}.json')) as f:
        activities = json.load(f)

    completed = completed_routes_for(activities)

    with open(f'completed-routes-{rider}.json', 'w') as f:
        json.dump(completed, f, indent=4, ensure_ascii=False)

    # completed-routes.json is kept as a legacy alias of martin's list.
    if rider == 'martin':
        with open('completed-routes.json', 'w') as f:
            json.dump(completed, f, indent=4, ensure_ascii=False)

    print(f'Found {len(completed)} completed routes for {rider}')
    for name in completed:
        print(f'  {name}')
