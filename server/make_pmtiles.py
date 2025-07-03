#!/usr/bin/env python3
import pickle
import json
import subprocess
import sys
from shapely.geometry import mapping
from tqdm import tqdm

def main():
    print("🔍 Loading runs data...")
    with open('runs.pkl','rb') as f:
        runs = pickle.load(f)
    
    print(f"📊 Processing {len(runs)} runs...")
    feats = []
    for rid, run in tqdm(runs.items(), desc="Converting runs", unit="run"):
        # Use only one feature per run with the highest detail
        # Let tippecanoe handle the simplification automatically
        geom = run['geoms']['full']  # Always use full resolution
        feats.append({
            'type': 'Feature',
            'geometry': mapping(geom),
            'properties': {'id': rid}  # Simple properties
        })
    
    print("💾 Writing GeoJSON file...")
    fc = {'type': 'FeatureCollection', 'features': feats}
    with open('runs.geojson', 'w') as f:
        json.dump(fc, f)
    
    # Check if PMTiles file exists and remove it
    import os
    if os.path.exists('runs.pmtiles'):
        print("🗑️  Removing existing runs.pmtiles...")
        os.remove('runs.pmtiles')
    
    print("🗜️  Running tippecanoe to generate PMTiles directly...")
    # Generate PMTiles directly with latest tippecanoe (v2.78.0+)
    result = subprocess.run([
        'tippecanoe',
        '-o', 'runs.pmtiles',
        '-l', 'runs',
        '-Z', '5',          # Min zoom
        '-z', '16',         # Max zoom (higher for more detail)
        '--simplification=2',  # Aggressive simplification for speed
        '--no-tile-size-limit',
        '--drop-densest-as-needed',  # Auto-drop features when too dense
        '--extend-zooms-if-still-dropping',  # Keep trying to fit data
        '--progress-interval=1',  # Show progress every second
        'runs.geojson'
    ], check=True)
    
    print("✅ PMTiles generation complete!")
    
    # Show file sizes
    import os
    geojson_size = os.path.getsize('runs.geojson') / (1024*1024)
    pmtiles_size = os.path.getsize('runs.pmtiles') / (1024*1024)
    print(f"📈 GeoJSON: {geojson_size:.1f}MB → PMTiles: {pmtiles_size:.1f}MB")
    print(f"🎯 Compression ratio: {geojson_size/pmtiles_size:.1f}x")

if __name__ == '__main__':
    main()
