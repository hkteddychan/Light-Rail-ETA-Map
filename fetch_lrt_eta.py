#!/usr/bin/env python3
"""Fetch MTR Light Rail ETA for all stations and save as JSON."""
import urllib.request
import json
import csv
import time
from datetime import datetime

LR_STOPS_CSV = "light_rail_stops.csv"
OUTPUT_FILE = "lrt_eta_data.json"

def fetch_light_rail_stops():
    """Fetch Light Rail stops list from MTR open data."""
    url = "https://opendata.mtr.com.hk/data/light_rail_routes_and_stops.csv"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        content = response.read().decode('utf-8-sig')  # handle BOM
    
    # Parse CSV - extract unique stop codes
    stops = set()
    lines = content.strip().split('\n')
    reader = csv.DictReader(lines)
    for row in reader:
        stop_code = row.get('Stop Code', '').strip()
        if stop_code:
            stops.add(stop_code)
    
    return sorted(stops)

def fetch_eta_for_station(station_code):
    """Fetch ETA for a single station from rt.data.gov.hk."""
    # The API uses numeric station IDs, try Stop ID first (numeric)
    url = f"https://rt.data.gov.hk/v1/transport/mtr/lrt/getSchedule?station_id={station_code}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except Exception as e:
        return {"error": str(e), "station_code": station_code}

def main():
    print(f"[{datetime.now().isoformat()}] Fetching Light Rail ETA data...")
    
    # Get all unique stop codes
    stop_codes = fetch_light_rail_stops()
    print(f"Found {len(stop_codes)} unique stop codes: {stop_codes[:10]}...")
    
    # Save stops CSV for reference
    with open(LR_STOPS_CSV, 'w') as f:
        import urllib.request as req2
        url = "https://opendata.mtr.com.hk/data/light_rail_routes_and_stops.csv"
        req = req2.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with req2.urlopen(req, timeout=30) as response:
            f.write(response.read().decode('utf-8-sig'))
    
    # Fetch ETA for each station (with rate limiting)
    all_eta = {}
    for i, code in enumerate(stop_codes):
        print(f"  Fetching station {code} ({i+1}/{len(stop_codes)})...")
        eta_data = fetch_eta_for_station(code)
        all_eta[code] = eta_data
        time.sleep(0.3)  # be polite
    
    result = {
        "updated": datetime.utcnow().isoformat(),
        "station_count": len(all_eta),
        "stations": all_eta
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Updated {len(all_eta)} stations -> {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
