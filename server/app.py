import pickle
import json
import time
from functools import lru_cache
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from shapely.geometry import mapping, Polygon
from shapely import clip_by_rect
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
    ids = list(idx.intersection((minLng, minLat, maxLng, maxLat)))

    print(
        f"🔍 Candidate run IDs for bbox ({minLat:.3f},{minLng:.3f})→({maxLat:.3f},{maxLng:.3f}): {ids}"
    )
    print(f"↪ Processing {len(ids)} runs at zoom {zoom}")

    # choose pre-simplified geometry based on zoom level - more granular tiers
    if zoom >= 15:
        key = 'full'
    elif zoom >= 12:
        key = 'high'
    elif zoom >= 9:
        key = 'mid'
    elif zoom >= 6:
        key = 'low'
    else:
        key = 'coarse'

    features = []
    minx, miny, maxx, maxy = minLng, minLat, maxLng, maxLat
    total = len(ids)
    for i, rid in enumerate(tqdm(ids, desc="runs", unit="run"), 1):
        run = runs[rid]
        line = run['geoms'][key]
        rb = run['bbox']
        # if run is fully contained in the bbox, avoid expensive intersection
        if rb[0] >= minx and rb[1] >= miny and rb[2] <= maxx and rb[3] <= maxy:
            geom = line
        else:
            clipped = clip_by_rect(line, minx, miny, maxx, maxy)
            if clipped.is_empty:
                continue
            geom = clipped
        features.append({
            'type': 'Feature',
            'geometry': mapping(geom)
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
    
    # Add caching headers for better performance
    response = jsonify(data)
    response.headers['Cache-Control'] = 'public, max-age=300'  # Cache for 5 minutes
    response.headers['ETag'] = f'"{hash((minLat, minLng, maxLat, maxLng, zoom))}"'
    return response


@app.route('/api/stream_runs')
def stream_runs():
    minLat = quantize(float(request.args.get('minLat')))
    minLng = quantize(float(request.args.get('minLng')))
    maxLat = quantize(float(request.args.get('maxLat')))
    maxLng = quantize(float(request.args.get('maxLng')))
    zoom = int(request.args.get('zoom'))
    chunk_size = int(request.args.get('chunk_size', 50))  # Features per chunk
    
    # Get optional filter for selected runs
    filter_runs = request.args.get('filter_runs')
    selected_run_ids = None
    if filter_runs:
        try:
            selected_run_ids = set(map(int, filter_runs.split(',')))
        except ValueError:
            pass

    def generate():
        ids = list(idx.intersection((minLng, minLat, maxLng, maxLat)))
        
        # Filter by selected runs if provided
        if selected_run_ids:
            ids = [rid for rid in ids if rid in selected_run_ids]

        print(
            f"🔍 Candidate run IDs for bbox ({minLat:.3f},{minLng:.3f})→({maxLat:.3f},{maxLng:.3f}): {len(ids)} runs"
        )
        if selected_run_ids:
            print(f"↪ Filtered to {len(ids)} selected runs")
        print(f"↪ Processing {len(ids)} runs at zoom {zoom}, chunk_size={chunk_size}")

        if zoom >= 15:
            key = 'full'
        elif zoom >= 12:
            key = 'high'
        elif zoom >= 9:
            key = 'mid'
        elif zoom >= 6:
            key = 'low'
        else:
            key = 'coarse'

        features = []
        minx, miny, maxx, maxy = minLng, minLat, maxLng, maxLat
        total = len(ids)
        
        for i, rid in enumerate(tqdm(ids, desc="runs", unit="run"), 1):
            run = runs[rid]
            line = run['geoms'][key]
            rb = run['bbox']
            if rb[0] >= minx and rb[1] >= miny and rb[2] <= maxx and rb[3] <= maxy:
                geom = line
            else:
                clipped = clip_by_rect(line, minx, miny, maxx, maxy)
                if clipped.is_empty:
                    continue
                geom = clipped
            features.append({
                'type': 'Feature',
                'geometry': mapping(geom),
                'properties': {'run_id': rid}  # Add run ID for identification
            })

            # Send chunks of features as they're processed
            if len(features) >= chunk_size:
                chunk_data = {'type': 'FeatureCollection', 'features': features}
                yield f"event: chunk\ndata: {json.dumps(chunk_data)}\n\n"
                features = []  # Reset for next chunk

            yield f"event: progress\ndata: {int(i*100/total)}\n\n"

        # Send any remaining features
        if features:
            chunk_data = {'type': 'FeatureCollection', 'features': features}
            yield f"event: chunk\ndata: {json.dumps(chunk_data)}\n\n"

        print(f"→ Finished streaming features in chunks")
        yield f"event: complete\ndata: done\n\n"

    headers = {'Cache-Control': 'no-cache'}
    return Response(stream_with_context(generate()), headers=headers, mimetype='text/event-stream')


@app.route('/api/runs_in_area', methods=['POST'])
def get_runs_in_area():
    """Find runs that intersect with a user-drawn polygon."""
    try:
        data = request.get_json()
        if not data or 'polygon' not in data:
            return jsonify({'error': 'Missing polygon data'}), 400
        
        # Create polygon from coordinates
        polygon_coords = data['polygon']
        if len(polygon_coords) < 3:
            return jsonify({'error': 'Polygon must have at least 3 points'}), 400
        
        # Ensure polygon is closed
        if polygon_coords[0] != polygon_coords[-1]:
            polygon_coords.append(polygon_coords[0])
        
        selection_polygon = Polygon(polygon_coords)
        if not selection_polygon.is_valid:
            return jsonify({'error': 'Invalid polygon'}), 400
        
        # Get polygon bounding box for initial filtering
        minx, miny, maxx, maxy = selection_polygon.bounds
        candidate_ids = list(idx.intersection((minx, miny, maxx, maxy)))
        
        print(f"🔍 Checking {len(candidate_ids)} candidate runs for polygon intersection")
        
        intersecting_runs = []
        
        for rid in candidate_ids:
            run = runs[rid]
            
            # Check if run geometry intersects with selection polygon
            line_geom = run['geoms']['full']  # Use full resolution for accurate intersection
            
            if line_geom.intersects(selection_polygon):
                # Prepare run data with metadata
                run_data = {
                    'id': rid,
                    'geometry': mapping(line_geom),
                    'metadata': run.get('metadata', {
                        'start_time': None,
                        'end_time': None,
                        'distance': 0,
                        'duration': 0,
                        'source_file': 'unknown'
                    })
                }
                intersecting_runs.append(run_data)
        
        print(f"→ Found {len(intersecting_runs)} runs intersecting with selection")
        
        return jsonify({
            'runs': intersecting_runs,
            'total': len(intersecting_runs)
        })
        
    except Exception as e:
        print(f"Error in runs_in_area: {e}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True)
