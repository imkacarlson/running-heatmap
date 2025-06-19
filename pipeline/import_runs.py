#!/usr/bin/env python3
"""
import_runs.py

Parse GPX and FIT (including .fit.gz) files in data/raw, extract runs as GeoJSON.
"""

import os
import argparse
import json
from glob import glob
from datetime import datetime
import math
import gzip

import gpxpy
import fitdecode
from fitdecode.records import FitDataMessage


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat/lon points in meters."""
    R = 6371000  # Earth radius
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def parse_gpx(filepath):
    """Return (run_id, coords, date, distance_m) for a GPX file."""
    with open(filepath, 'r') as f:
        gpx = gpxpy.parse(f)
    coords = []
    for track in gpx.tracks:
        for seg in track.segments:
            for pt in seg.points:
                coords.append((pt.longitude, pt.latitude))
    if not coords:
        return None
    date = None
    try:
        date = gpx.tracks[0].segments[0].points[0].time
    except Exception:
        pass
    distance = gpx.length_2d()
    run_id = os.path.splitext(os.path.basename(filepath))[0]
    return run_id, coords, date, distance


def parse_fit(filepath):
    """Return (run_id, coords, date, distance_m) for a FIT or FIT.GZ file."""
    coords = []
    timestamps = []
    total_d = 0.0
    prev_lat = prev_lon = None
    # support gzipped FIT files
    opener = gzip.open if filepath.lower().endswith('.gz') else open
    with opener(filepath, 'rb') as fh:
        with fitdecode.FitReader(fh) as fit:
            for frame in fit:
                if isinstance(frame, FitDataMessage) and frame.name == 'record':
                    lat_sem = frame.get_value('position_lat')
                    lon_sem = frame.get_value('position_long')
                    ts = frame.get_value('timestamp')
                    if lat_sem is None or lon_sem is None:
                        continue
                    # semicircle → degrees
                    lat = lat_sem * (180.0 / 2**31)
                    lon = lon_sem * (180.0 / 2**31)
                    coords.append((lon, lat))
                    timestamps.append(ts)
                    if prev_lat is not None:
                        total_d += haversine(prev_lat, prev_lon, lat, lon)
                    prev_lat, prev_lon = lat, lon
    if not coords:
        return None
    date = timestamps[0] if timestamps else None
    # strip .gz if present
    base = os.path.basename(filepath)
    run_id = base[:-7] if base.lower().endswith('.fit.gz') else os.path.splitext(base)[0]
    return run_id, coords, date, total_d


def main():
    parser = argparse.ArgumentParser(description="Import GPX/FIT runs and output GeoJSON")
    parser.add_argument('-i', '--input-dir', default='data/raw', help='Raw GPX/FIT input directory')
    parser.add_argument('-o', '--output', default='data/processed/all_runs.geojson', help='GeoJSON output file')
    args = parser.parse_args()

    features = []
    patterns = ['*.gpx', '*.fit', '*.fit.gz']
    for pat in patterns:
        for path in glob(os.path.join(args.input_dir, pat)):
            print(f"Processing {path}...")
            try:
                if path.lower().endswith('.gpx'):
                    res = parse_gpx(path)
                else:
                    res = parse_fit(path)
            except Exception as e:
                print(f"  Error parsing {path}: {e}")
                continue
            if res is None:
                print(f"  Skipping {path}: no track points")
                continue
            run_id, coords, date, dist_m = res
            feat = {
                'type': 'Feature',
                'properties': {
                    'run_id': run_id,
                    'date': date.isoformat() if isinstance(date, datetime) else str(date),
                    'distance_m': dist_m,
                },
                'geometry': {'type': 'LineString', 'coordinates': coords}
            }
            features.append(feat)

    coll = {'type': 'FeatureCollection', 'features': features}
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as fw:
        json.dump(coll, fw, indent=2)
    print(f"Wrote {len(features)} runs to {args.output}")


if __name__ == '__main__':
    main()
