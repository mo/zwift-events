#!/usr/bin/env python3
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from collections import defaultdict
from zoneinfo import ZoneInfo

# Rider name -> Zwift user id (activity dump in ~/dv/zwift-data/<id>.json).
RIDERS = {
    'martin': 7971732,
    'nils': 8010919,
    'magnus': 6918489,
}

ZWIFT_DATA_DIR = os.path.expanduser('~/dv/zwift-data')
HISTORY_TIMEZONE = ZoneInfo('Europe/Stockholm')

URL_SLUG_OVERRIDES = {
    'London PRL Full': 'the-prl-full',
    'London PRL Half': 'the-prl-half',
    'Watopia Figure 8': 'figure-8',
    'Watopia Flat Route': 'flat-route',
    'Watopia Hilly Route': 'hilly-route',
    'Watopia Mountain 8': 'mountain-8',
    'Watopia Mountain Route': 'mountain-route',
    'Watopia Pretzel': 'the-pretzel',
}

def route_url(name):
    if not name:
        return None
    # Climb Portal is a label, not part of the ZwiftInsider route slug.
    slug_name = re.sub(r'^Climb Portal:\s*', '', name)
    if slug_name in URL_SLUG_OVERRIDES:
        slug = URL_SLUG_OVERRIDES[slug_name]
    else:
        slug = unicodedata.normalize('NFKD', slug_name).encode('ascii', 'ignore').decode().lower()
        slug = re.sub(r'[^a-z0-9 -]', '', slug)
        slug = re.sub(r' +', '-', slug.strip())
    return f'https://zwiftinsider.com/route/{slug}/'

with open('game.json') as f:
    game = json.load(f)

route_by_sig = {r['signature']: r for r in game['ROUTES']['ROUTE']}
route_name_by_ach_id = {
    a['signature']: route_by_sig[a['routeSignature']]['name']
    for a in game['ACHIEVEMENTS']['ACHIEVEMENT']
    if a.get('imageName') == 'RouteComplete' and a.get('routeSignature') in route_by_sig
}

def canonical_route_name(route_name):
    """Normalize the two route names Zwift sometimes reports with a world prefix."""
    if route_name == "Watopia Flat Route":
        return "Flat Route"
    if route_name == "Watopia Hilly Route":
        return "Hilly Route"
    return route_name

def get_route_from_activity_name(activity_name):
    """Find a known route in Zwift's varied activity-name formats.

    Examples include ``Zwift - Route in World``,
    ``Zwift - Workout on Route in World``, and group/pacer rides where
    those labels precede the route. Match against game.json names, longest
    first, so names containing other route names resolve to the full route.
    """
    if not activity_name:
        return None

    # The name field is a title, not a canonical route field. Search only
    # route-sized tokens; case-insensitive matching handles title variants.
    title = re.sub(r'^\s*Zwift\s*[-:]\s*', '', str(activity_name), flags=re.IGNORECASE)
    climb_portal_prefix = re.search(r'(?i)\bClimb Portal\s*[:-]\s*', title)
    for route in sorted(game['ROUTES']['ROUTE'], key=lambda r: len(r.get('name', '')), reverse=True):
        name = route.get('name', '')
        if not name:
            continue
        if re.search(r'(?<![\w])' + re.escape(name) + r'(?![\w])', title, flags=re.IGNORECASE):
            return f'Climb Portal: {name}' if climb_portal_prefix else name

    # Common title aliases omit the world-qualified form stored in game.json.
    lowered = title.casefold()
    if re.search(r'(?<![\w])flat route(?![\w])', lowered):
        return 'Watopia Flat Route'
    if re.search(r'(?<![\w])hilly route(?![\w])', lowered):
        return 'Watopia Hilly Route'
    return None

def format_duration_ms(ms):
    """Format milliseconds as HH:MM:SS"""
    seconds = ms // 1000
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def get_route_from_activity(activity):
    """Extract route name from activity description or route completion achievement"""
    activity_details = activity.get('activityDetailsJson', {})
    description = activity_details.get('description', '')

    # Route name is in format "🗺️ {route name} in {world}" (for event rides)
    match = re.search(r'🗺️\s*([^\n]+)\s+in\s+', description)
    if match:
        return match.group(1).strip()

    # For non-event rides, look for route completion in notable moments
    moments = activity_details.get('notableMoments', [])
    for moment in moments:
        if moment.get('notableMomentTypeId') == 2:  # Route completion
            try:
                aux = json.loads(moment.get('aux1', '{}'))
            except (json.JSONDecodeError, TypeError):
                continue
            achievement_id = str(aux.get('achievementId'))
            route_name = route_name_by_ach_id.get(achievement_id)
            if route_name:
                if re.search(r'(?i)\bClimb Portal\s*[:-]\s*', activity.get('name', '')):
                    return f'Climb Portal: {route_name}'
                return route_name

    # Non-event rides often omit route-completion moments. Zwift's activity
    # title still names the route, with the world suffix and ride/workout
    # label varying by activity type.
    route_name = get_route_from_activity_name(activity.get('name'))
    if route_name:
        return route_name

    return None

def get_notable_moments(activity):
    """Extract notable moments from activity"""
    activity_details = activity.get('activityDetailsJson', {})
    moments = activity_details.get('notableMoments', [])

    notable = []
    for moment in moments:
        moment_type = moment.get('notableMomentTypeId')
        try:
            aux = json.loads(moment.get('aux1', '{}'))
        except (json.JSONDecodeError, TypeError):
            aux = {}

        if moment_type == 2:  # Route completion
            achievement_id = str(aux.get('achievementId'))
            route_name = route_name_by_ach_id.get(achievement_id)
            if route_name:
                notable.append({'type': 'route', 'text': route_name})
        elif moment_type == 4:  # Unlock/item
            unlock_name = aux.get('unlockName')
            if unlock_name:
                notable.append({'type': 'unlock', 'text': f"Unlock: {unlock_name}"})
        elif moment_type == 5:  # Level up
            new_level = aux.get('newLevel')
            if new_level:
                notable.append({'type': 'level', 'text': f"Level {new_level}"})

    # Keep the route completion first so it remains the primary moment shown
    # for a ride, even when Zwift returns unlocks or level-ups before it.
    notable.sort(key=lambda moment: moment['type'] != 'route')
    return notable

def build_ride_history(activities):
    """Build daily ride history from activities"""
    daily_history = defaultdict(list)

    for activity in activities:
        if activity.get('sport') != 'CYCLING':
            continue

        start_date = activity.get('startDate', '')
        if not start_date:
            continue

        # Parse date and extract date part (YYYY-MM-DD)
        try:
            dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            date_key = dt.astimezone(HISTORY_TIMEZONE).strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            continue

        # Extract event name if it's an event
        event_info = activity.get('activityDetailsJson', {}).get('eventInfo')
        event_name = event_info.get('name') if event_info else None

        # Extract route name
        route_name = get_route_from_activity(activity)

        # Get route details - either from route name or fall back to activity data
        route_length_km = None
        route_elevation_m = None
        if route_name and not route_name.startswith('Climb Portal: '):
            # Find route in game.json
            for route in game['ROUTES']['ROUTE']:
                if route.get('name') == route_name:
                    route_length_km = round(float(route.get('distanceInMeters', 0)) / 1000, 1)
                    route_elevation_m = round(float(route.get('ascentInMeters', 0)))
                    break

        # Fall back to activity-level distance and elevation if route not found
        if route_length_km is None:
            route_length_km = round(float(activity.get('distanceInMeters', 0)) / 1000, 1) if activity.get('distanceInMeters') else None
        if route_elevation_m is None:
            route_elevation_m = round(float(activity.get('totalElevation', 0))) if activity.get('totalElevation') else None

        # Get notable moments
        notable_moments = get_notable_moments(activity)

        # Get time biked
        moving_time_ms = activity.get('movingTimeInMs', 0)
        time_biked = format_duration_ms(moving_time_ms)

        # Add to daily history
        daily_history[date_key].append({
            'eventName': event_name,
            'routeName': route_name,
            'routeUrl': route_url(route_name),
            'routeLengthKm': route_length_km,
            'routeElevationM': route_elevation_m,
            'timeBiked': time_biked,
            'timeBikedSeconds': moving_time_ms // 1000,
            'notableMoments': notable_moments
        })

    # Convert to sorted list of dates
    history = []
    for date in sorted(daily_history.keys(), reverse=True):
        rides = daily_history[date]
        # Sort rides by time (assuming they're in order in the original data)
        history.append({
            'date': date,
            'rides': rides
        })

    return history

for rider, user_id in RIDERS.items():
    activity_file = os.path.join(ZWIFT_DATA_DIR, f'{user_id}.json')

    if not os.path.exists(activity_file):
        print(f'Activity file not found for {rider}: {activity_file}')
        continue

    with open(activity_file) as f:
        activities = json.load(f)

    history = build_ride_history(activities)

    with open(f'ride-history-{rider}.json', 'w') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    total_rides = sum(len(day['rides']) for day in history)
    print(f'Built ride-history-{rider}.json with {len(history)} days and {total_rides} total rides')
