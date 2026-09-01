import csv
import json
from collections import defaultdict
import statistics

def time_to_minutes(time_str):
    try:
        # GTFS pozwala na godziny > 24 (np. 25:12 to 1:12 w nocy)
        h, m, s = map(int, time_str.strip().split(':'))
        return h * 60 + m + s / 60.0
    except:
        return 0

def wyciagnij_cyfry(text):
    # Wyciąga same cyfry i usuwa zera wiodące (np. "B01026" -> "1026")
    return ''.join(c for c in str(text) if c.isdigit()).lstrip('0')

def generuj():
    print("Wczytywanie routes.txt...")
    routes = {}
    with open("routes.txt", 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            routes[row['route_id']] = row['route_short_name'].strip()

    print("Wczytywanie trips.txt...")
    trips = {}
    with open("trips.txt", 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            trips[row['trip_id']] = routes.get(row['route_id'], 'UNKNOWN')

    print("Wczytywanie stop_times.txt (to potrwa chwilę)...")
    stop_times = defaultdict(list)
    with open("stop_times.txt", 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            stop_times[row['trip_id']].append({
                'stop_id': wyciagnij_cyfry(row['stop_id']),
                'time': time_to_minutes(row['departure_time']),
                'seq': int(row['stop_sequence'])
            })

    print("Obliczanie czasów przejazdów...")
    travel_times = defaultdict(lambda: defaultdict(list))
    global_times = defaultdict(list)

    for trip_id, stops in stop_times.items():
        line = trips.get(trip_id)
        if not line or line == 'UNKNOWN':
            continue

        # Sortujemy przystanki zgodnie z kolejnością na trasie
        stops.sort(key=lambda x: x['seq'])

        for i in range(len(stops) - 1):
            id_a = stops[i]['stop_id']
            id_b = stops[i+1]['stop_id']
            if not id_a or not id_b:
                continue

            diff = max(0, stops[i+1]['time'] - stops[i]['time'])
            
            # Zabezpieczenie przed błędami w GTFS (np. przerwa w kursie > 40 min)
            if diff < 40:
                segment_key = f"{id_a}-{id_b}"
                travel_times[line][segment_key].append(diff)
                global_times[segment_key].append(diff)

    print("Zapisywanie wyników do czasy_odcinkow.json...")
    final_times = {}

    # Średnie czasy per konkretna linia
    for line, segments in travel_times.items():
        final_times[line] = {}
        for segment, times in segments.items():
            if times:
                final_times[line][segment] = round(statistics.median(times))

    # Czas zapasowy dla wszystkich odcinków (gdyby skrypt nie znalazł linii)
    final_times['GLOBAL'] = {}
    for segment, times in global_times.items():
        if times:
            final_times['GLOBAL'][segment] = round(statistics.median(times))

    with open('czasy_odcinkow.json', 'w', encoding='utf-8') as f:
        json.dump(final_times, f, ensure_ascii=False, separators=(',', ':'))
        
    print("Gotowe! Przenieś plik czasy_odcinkow.json do folderu swojej aplikacji.")

if __name__ == '__main__':
    generuj()