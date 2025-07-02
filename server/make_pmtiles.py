#!/usr/bin/env python3
import pickle
import json
import subprocess
from shapely.geometry import mapping

LEVELS = {
    'high': (13,14),
    'mid': (10,12),
    'low': (5,9)
}

def main():
    with open('runs.pkl','rb') as f:
        runs = pickle.load(f)
    feats=[]
    for rid,run in runs.items():
        for lvl,(zmin,zmax) in LEVELS.items():
            geom = run['geoms'][lvl]
            feats.append({
                'type':'Feature',
                'geometry': mapping(geom),
                'properties': {'id':rid,'zmin':zmin,'zmax':zmax}
            })
    fc={'type':'FeatureCollection','features':feats}
    with open('runs.geojson','w') as f:
        json.dump(fc,f)
    subprocess.run(['tippecanoe','-o','runs.pmtiles','-l','runs','-Z5','-z14','--no-tile-size-limit','runs.geojson'],check=True)

if __name__=='__main__':
    main()
