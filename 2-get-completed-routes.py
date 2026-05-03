#!/usr/bin/env python3
import json

with open('../zwift-data/7971732.json') as f:
    activities = json.load(f)

with open('game.json') as f:
    game = json.load(f)

route_by_sig = {r['signature']: r for r in game['ROUTES']['ROUTE']}
route_name_by_ach_id = {
    a['signature']: route_by_sig[a['routeSignature']]['name']
    for a in game['ACHIEVEMENTS']['ACHIEVEMENT']
    if a.get('imageName') == 'RouteComplete' and a.get('routeSignature') in route_by_sig
}

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

with open('completed-routes.json', 'w') as f:
    json.dump(sorted(completed), f, indent=4, ensure_ascii=False)

print(f'Found {len(completed)} completed routes')
for name in sorted(completed):
    print(f'  {name}')
