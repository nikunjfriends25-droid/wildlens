"""
Reads gold_standard_annotations.csv and applies corrected lat/lon/place_name
back to docs/news.json for any article where location_correct == NO
and the correct location differs meaningfully from v1.
Skips rows where correct_* == v1_* (still unresolved / VALIDATE cases).
"""
import json, csv

with open('docs/news.json', encoding='utf-8') as f:
    articles = json.load(f)

url_to_article = {a['url']: a for a in articles}

with open('v2/data/gold_standard_annotations.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

fixes_applied = 0
skipped_validate = 0
not_in_json = 0

for row in rows:
    if row['valid_wildlife_article'] == 'NO':
        continue
    if row['location_correct'] != 'NO':
        continue

    url = row['url']
    if url not in url_to_article:
        not_in_json += 1
        continue

    try:
        correct_lat = float(row['correct_lat'])
        correct_lon = float(row['correct_lon'])
        v1_lat = float(row['v1_lat'])
        v1_lon = float(row['v1_lon'])
    except (ValueError, TypeError):
        skipped_validate += 1
        continue

    # Skip if correct == v1 (VALIDATE cases where I didn't have a better answer)
    if abs(correct_lat - v1_lat) < 0.01 and abs(correct_lon - v1_lon) < 0.01:
        skipped_validate += 1
        continue

    article = url_to_article[url]
    old = f"{article['place_name']} ({article['lat']},{article['lon']})"
    article['lat'] = correct_lat
    article['lon'] = correct_lon
    article['place_name'] = row['correct_place_name']
    new = f"{article['place_name']} ({article['lat']},{article['lon']})"
    print(f"{row['event_id']} {row['location_error_type']}: {old} -> {new}")
    fixes_applied += 1

with open('docs/news.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)

print(f"\nFixes applied: {fixes_applied}")
print(f"Skipped (VALIDATE / no better answer): {skipped_validate}")
print(f"Not in news.json (older articles): {not_in_json}")
