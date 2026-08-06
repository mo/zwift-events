def is_interesting(event):
    if event.get('sport') != 'CYCLING':
        return False
    if 'LADIES_ONLY' in event.get('rulesSet', []):
        return False
    # You always ride *in* a subgroup, and the subgroup's rules are what the game
    # applies, so the subgroups decide when they exist. The top-level flag can
    # disagree with them (e.g. event 5663089, Team Italy Fat Burn Ride on
    # 2026-08-06: banded at the top level, unbanded on its only subgroup).
    subgroups = event.get('eventSubgroups', [])
    if subgroups:
        return all('TEST_BIT_10' in sg.get('rulesSet', []) for sg in subgroups)
    return 'TEST_BIT_10' in event.get('rulesSet', [])
