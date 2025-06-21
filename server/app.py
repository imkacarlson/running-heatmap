import pickle
from flask import Flask, request, jsonify, send_from_directory
from shapely.geometry import LineString, box, mapping

# Load runs and build spatial index
with open('runs.pkl', 'rb') as f:
    runs = pickle.load(f)

from rtree import index
idx = index.Index()
for run in runs:
    idx.insert(run['id'], run['bbox'])

app = Flask(__name__, static_folder='../web', static_url_path='')

@app.route('/')
def root():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/runs')
def get_runs():
    minLat = float(request.args.get('minLat'))
    minLng = float(request.args.get('minLng'))
    maxLat = float(request.args.get('maxLat'))
    maxLng = float(request.args.get('maxLng'))
    zoom = int(request.args.get('zoom'))

    bbox = box(minLng, minLat, maxLng, maxLat)
    ids = list(idx.intersection((minLng, minLat, maxLng, maxLat)))

    print(f"🔍 Candidate run IDs for bbox ({minLat:.3f},{minLng:.3f})→({maxLat:.3f},{maxLng:.3f}): {ids}")

    features = []
    for rid in ids:
        run = next(r for r in runs if r['id'] == rid)
        line = LineString(run['coords'])
        clipped = line.intersection(bbox)
        if clipped.is_empty:
            continue
        # simplify based on zoom
        tol = 0.001 * (2 ** (12 - zoom))
        simp = clipped.simplify(tol, preserve_topology=False)
        features.append({
            'type': 'Feature',
            'geometry': mapping(simp),
            'properties': {}
        })

    print(f"→ Returning {len(features)} features")
    return jsonify({'type': 'FeatureCollection', 'features': features})

if __name__ == '__main__':
    app.run(debug=True)