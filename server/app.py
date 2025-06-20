import pickle
from functools import lru_cache
from flask import Flask, request, jsonify, send_from_directory
from shapely.geometry import box, mapping
from tqdm import tqdm

# Load runs and build spatial index
with open('runs.pkl', 'rb') as f:
    runs = pickle.load(f)

from rtree import index
idx = index.Index()
for rid, run in runs.items():
    idx.insert(rid, run['bbox'])

app = Flask(__name__, static_folder='../web', static_url_path='')

@app.route('/')
def root():
    return send_from_directory(app.static_folder, 'index.html')


def quantize(val, digits=4):
    """Round coordinate for caching stability."""
    return round(val, digits)


@lru_cache(maxsize=512)
def _runs_for_bbox(minLat, minLng, maxLat, maxLng, zoom):
    bbox = box(minLng, minLat, maxLng, maxLat)
    ids = list(idx.intersection((minLng, minLat, maxLng, maxLat)))

    print(
        f"🔍 Candidate run IDs for bbox ({minLat:.3f},{minLng:.3f})→({maxLat:.3f},{maxLng:.3f}): {ids}"
    )
    print(f"↪ Processing {len(ids)} runs at zoom {zoom}")

    # choose pre-simplified geometry based on zoom level
    if zoom >= 13:
        key = 'full'
    elif zoom >= 10:
        key = 'mid'
    else:
        key = 'coarse'

    features = []
    minx, miny, maxx, maxy = bbox.bounds
    for rid in tqdm(ids, desc="runs", unit="run"):
        run = runs[rid]
        line = run['geoms'][key]
        rb = run['bbox']
        # if run is fully contained in the bbox, avoid expensive intersection
        if rb[0] >= minx and rb[1] >= miny and rb[2] <= maxx and rb[3] <= maxy:
            geom = line
        else:
            clipped = line.intersection(bbox)
            if clipped.is_empty:
                continue
            geom = clipped
        features.append({
            'type': 'Feature',
            'geometry': mapping(geom),
            'properties': {}
        })

    print(f"→ Returning {len(features)} features")
    return {'type': 'FeatureCollection', 'features': features}

@app.route('/api/runs')
def get_runs():
    minLat = quantize(float(request.args.get('minLat')))
    minLng = quantize(float(request.args.get('minLng')))
    maxLat = quantize(float(request.args.get('maxLat')))
    maxLng = quantize(float(request.args.get('maxLng')))
    zoom = int(request.args.get('zoom'))

    data = _runs_for_bbox(minLat, minLng, maxLat, maxLng, zoom)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
