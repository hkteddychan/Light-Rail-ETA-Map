#!/usr/bin/env python3
"""Fetch MTR Light Rail ETA for all stations + build static data for GitHub Pages.
Outputs:
  lrt_eta_data.json — live arrivals per station
  stations.geojson  — station points with coords + names
"""
import urllib.request, json, csv, time, os, urllib.parse
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
UA = 'Mozilla/5.0 (LRT-ETA-Map; hkteddychan; +hk)'

STOP_CSV = f"{BASE}/light_rail_stops.csv"
OUT_ETA = f"{BASE}/lrt_eta_data.json"
OUT_GEO = f"{BASE}/stations.geojson"


def fetch_stops_csv():
    url = "https://opendata.mtr.com.hk/data/light_rail_routes_and_stops.csv"
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        content = r.read().decode('utf-8-sig')
    with open(STOP_CSV, 'w', encoding='utf-8') as f:
        f.write(content)
    reader = csv.DictReader(content.strip().split('\n'))
    d = {}
    for row in reader:
        code = row.get('Stop Code', '').strip()
        if code and code not in d:
            d[code] = {
                'stop_id': row.get('Stop ID', '').strip(),
                'zh': row.get('Chinese Name', '').strip(),
                'en': row.get('English Name', '').strip(),
                'line': row.get('Line Code', '').strip(),
            }
    return d


def fetch_eta(stop_id):
    url = f"https://rt.data.gov.hk/v1/transport/mtr/lrt/getSchedule?station_id={stop_id}"
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))


def geocode(name_en, name_zh):
    """Best-effort geocode via Nominatim; returns [lng,lat] or None."""
    # Try "{en} {zh} Hong Kong" first (verified working), then en+HK fallback
    for q in [f"{name_en} {name_zh} Hong Kong", f"{name_en} Hong Kong", f"{name_zh} Hong Kong 輕鐵"]:
        url = f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + urllib.parse.quote(q)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=12) as r:
                res = json.loads(r.read().decode('utf-8'))
            if res:
                return [float(res[0]['lon']), float(res[0]['lat'])]
        except Exception:
            pass
        time.sleep(1.0)
    return None


def main():
    print("Fetching stops...")
    stops = fetch_stops_csv()
    print(f"  {len(stops)} stops")

    etas = {}
    for i, (code, s) in enumerate(stops.items()):
        try:
            etas[code] = fetch_eta(s['stop_id'])
        except Exception as e:
            etas[code] = {"error": str(e)}
        time.sleep(0.2)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(stops)}")

    updated = datetime.now(timezone.utc).isoformat()
    json.dump({"updated": updated, "station_count": len(etas), "stations": etas},
              open(OUT_ETA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # Geocode (cache to avoid hammering Nominatim)
    cache_f = f"{BASE}/.stations_geo.json"
    cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
    feats = []
    for code, s in stops.items():
        if code not in cache:
            cache[code] = geocode(s['en'] or '', s['zh'] or '')
            time.sleep(1.0)
        coord = cache.get(code) or [114.09, 22.39]  # fallback near Tuen Mun
        feats.append({
            "type": "Feature",
            "properties": {**s, "code": code},
            "geometry": {"type": "Point", "coordinates": coord},
        })
    json.dump(cache, open(cache_f, 'w'), ensure_ascii=False)
    json.dump({"type": "FeatureCollection", "features": feats, "updated": updated},
              open(OUT_GEO, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"Done. updated={updated}  stations={len(stops)}")


if __name__ == "__main__":
    main()