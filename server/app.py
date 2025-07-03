import pickle
import json
from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory,
)
from shapely.geometry import mapping, Polygon, LineString
import gpxpy
from rtree import index


# Load runs and build spatial index
with open('runs.pkl', 'rb') as f:
    runs = pickle.load(f)

idx = index.Index()
for rid, run in runs.items():
    idx.insert(rid, run['bbox'])

app = Flask(__name__, static_folder='../web', static_url_path='')

@app.route('/')
def root():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/runs.pmtiles')
def pmtiles():
    return send_from_directory('.', 'runs.pmtiles')


def quantize(val, digits=3):
    """Round coordinate for caching stability."""
    return round(val, digits)


def _normalize_activity_type(raw_type):
    """Convert various activity descriptors to standard categories."""
    if not raw_type:
        return 'other'
    t = raw_type.lower()
    if 'run' in t or 'jog' in t:
        return 'run'
    if 'bike' in t or 'biking' in t or 'cycl' in t or 'ride' in t:
        return 'bike'
    if 'walk' in t:
        return 'walk'
    if 'hike' in t:
        return 'hike'
    return 'other'


def parse_gpx_fileobj(file_obj):
    """Parse a GPX file-like object and return coordinates and metadata."""
    gpx = gpxpy.parse(file_obj)
    coords = []
    metadata = {
        'start_time': None,
        'end_time': None,
        'distance': 0,
        'duration': 0,
        'activity_type': 'other',
        'activity_raw': None,
    }

    points_with_time = []
    raw_type = None
    for track in gpx.tracks:
        if hasattr(track, 'type') and track.type:
            raw_type = track.type
        if not raw_type:
            for ext in getattr(track, 'extensions', []) or []:
                tag = getattr(ext, 'tag', '').lower()
                if 'type' in tag or 'activity' in tag:
                    raw_type = ext.text
                    break
        for segment in track.segments:
            for p in segment.points:
                coords.append((p.longitude, p.latitude))
                if p.time:
                    points_with_time.append(p)

    if points_with_time:
        metadata['start_time'] = points_with_time[0].time
        metadata['end_time'] = points_with_time[-1].time
        metadata['duration'] = (
            points_with_time[-1].time - points_with_time[0].time
        ).total_seconds()

    if gpx.tracks:
        metadata['distance'] = gpx.length_3d() or gpx.length_2d() or 0

    metadata['activity_raw'] = raw_type
    metadata['activity_type'] = _normalize_activity_type(raw_type)

    return coords, metadata


def add_run(coords, metadata, source_name='upload'):
    """Add a new run to the dataset and persist it."""
    global runs
    rid = max(runs.keys(), default=0) + 1
    ls = LineString(coords)
    runs[rid] = {
        'bbox': ls.bounds,
        'geoms': {
            'full': ls,
            'high': ls.simplify(0.0001, preserve_topology=False),
            'mid': ls.simplify(0.0005, preserve_topology=False),
            'low': ls.simplify(0.001, preserve_topology=False),
            'coarse': ls.simplify(0.002, preserve_topology=False),
        },
        'metadata': {
            'start_time': metadata.get('start_time'),
            'end_time': metadata.get('end_time'),
            'distance': metadata.get('distance'),
            'duration': metadata.get('duration'),
            'activity_type': metadata.get('activity_type', 'other'),
            'activity_raw': metadata.get('activity_raw'),
            'source_file': source_name,
        },
    }
    idx.insert(rid, runs[rid]['bbox'])
    with open('runs.pkl', 'wb') as f:
        pickle.dump(runs, f)
    return rid




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
        
        # Validate coordinate format
        for i, coord in enumerate(polygon_coords):
            if not isinstance(coord, list) or len(coord) != 2:
                return jsonify({'error': f'Invalid coordinate format at index {i}'}), 400
            if not all(isinstance(x, (int, float)) for x in coord):
                return jsonify({'error': f'Non-numeric coordinate at index {i}'}), 400
        
        selection_polygon = Polygon(polygon_coords)
        if not selection_polygon.is_valid:
            # Try to fix the polygon using buffer(0) which can resolve self-intersections
            try:
                fixed_polygon = selection_polygon.buffer(0)
                if fixed_polygon.is_valid and not fixed_polygon.is_empty:
                    selection_polygon = fixed_polygon
                else:
                    return jsonify({'error': 'Invalid polygon geometry - please try drawing again'}), 400
            except Exception as e:
                return jsonify({'error': 'Invalid polygon geometry - please try drawing again'}), 400
        
        # Get polygon bounding box for initial filtering
        minx, miny, maxx, maxy = selection_polygon.bounds
        candidate_ids = list(idx.intersection((minx, miny, maxx, maxy)))
        
        intersecting_runs = []
        
        for rid in candidate_ids:
            run = runs[rid]
            
            # Check if run geometry intersects with selection polygon
            line_geom = run['geoms']['full']  # Use full resolution for accurate intersection
            
            if line_geom.intersects(selection_polygon):
                # Prepare run data with metadata, converting datetimes to strings for JSON
                metadata = run.get('metadata', {}).copy()
                if metadata.get('start_time') and hasattr(metadata['start_time'], 'isoformat'):
                    metadata['start_time'] = metadata['start_time'].isoformat()
                if metadata.get('end_time') and hasattr(metadata['end_time'], 'isoformat'):
                    metadata['end_time'] = metadata['end_time'].isoformat()

                run_data = {
                    'id': rid,
                    'geometry': mapping(line_geom),
                    'metadata': metadata
                }
                intersecting_runs.append(run_data)
        
        
        return jsonify({
            'runs': intersecting_runs,
            'total': len(intersecting_runs)
        })
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/upload', methods=['POST'])
def upload_gpx():
    """Upload one or more GPX files and persist them as runs."""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    added = []
    features = []
    for f in request.files.getlist('files'):
        if not f.filename:
            continue
        try:
            coords, meta = parse_gpx_fileobj(f.stream)
        except Exception as e:
            return jsonify({'error': f'Failed to parse {f.filename}: {e}'}), 400

        if len(coords) >= 2:
            rid = add_run(coords, meta, f.filename)
            added.append(rid)
            features.append({
                'type': 'Feature',
                'geometry': mapping(LineString(coords)),
                'properties': {'id': rid}
            })

    return jsonify({'added': added, 'features': features})


if __name__ == '__main__':
    app.run(debug=True)
