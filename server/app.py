import pickle
import json
import time
from functools import lru_cache
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
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


def quantize(val, digits=3):
    """Round coordinate for caching stability."""
    return round(val, digits)


def _compute_runs(minLat, minLng, maxLat, maxLng, zoom, progress_cb=None):
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
    total = len(ids)
    for i, rid in enumerate(tqdm(ids, desc="runs", unit="run"), 1):
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
        if progress_cb:
            progress_cb(int(i * 100 / total))

    print(f"→ Returning {len(features)} features")
    return {'type': 'FeatureCollection', 'features': features}


@lru_cache(maxsize=2048)
def _runs_for_bbox(minLat, minLng, maxLat, maxLng, zoom):
    return _compute_runs(minLat, minLng, maxLat, maxLng, zoom)

@app.route('/api/runs')
def get_runs():
    minLat = quantize(float(request.args.get('minLat')))
    minLng = quantize(float(request.args.get('minLng')))
    maxLat = quantize(float(request.args.get('maxLat')))
    maxLng = quantize(float(request.args.get('maxLng')))
    zoom = int(request.args.get('zoom'))

    data = _runs_for_bbox(minLat, minLng, maxLat, maxLng, zoom)
    return jsonify(data)


@app.route('/api/stream_runs')
def stream_runs():
    minLat = quantize(float(request.args.get('minLat')))
    minLng = quantize(float(request.args.get('minLng')))
    maxLat = quantize(float(request.args.get('maxLat')))
    maxLng = quantize(float(request.args.get('maxLng')))
    zoom = int(request.args.get('zoom'))

    def generate():
        bbox = box(minLng, minLat, maxLng, maxLat)
        ids = list(idx.intersection((minLng, minLat, maxLng, maxLat)))

        print(
            f"🔍 Candidate run IDs for bbox ({minLat:.3f},{minLng:.3f})→({maxLat:.3f},{maxLng:.3f}): {ids}"
        )
        print(f"↪ Processing {len(ids)} runs at zoom {zoom}")

        if zoom >= 13:
            key = 'full'
        elif zoom >= 10:
            key = 'mid'
        else:
            key = 'coarse'

        features = []
        minx, miny, maxx, maxy = bbox.bounds
        total = len(ids)
        for i, rid in enumerate(tqdm(ids, desc="runs", unit="run"), 1):
            run = runs[rid]
            line = run['geoms'][key]
            rb = run['bbox']
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

            yield f"event: progress\ndata: {int(i*100/total)}\n\n"

        print(f"→ Returning {len(features)} features")
        data = {'type': 'FeatureCollection', 'features': features}
        yield f"event: data\ndata: {json.dumps(data)}\n\n"

    headers = {'Cache-Control': 'no-cache'}
    return Response(stream_with_context(generate()), headers=headers, mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
