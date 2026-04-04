def is_interesting(event):
    if event.get('sport') != 'CYCLING':
        return False
    if 'LADIES_ONLY' in event.get('rulesSet', []):
        return False
    subgroups = event.get('eventSubgroups', [])
    top_level_banded = 'TEST_BIT_10' in event.get('rulesSet', [])
    all_subgroups_banded = bool(subgroups) and all('TEST_BIT_10' in sg.get('rulesSet', []) for sg in subgroups)
    return top_level_banded or all_subgroups_banded
