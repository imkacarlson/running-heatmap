import os
import gzip
import pickle
import tempfile
from concurrent.futures import ProcessPoolExecutor
from shapely.geometry import LineString
import gpxpy
from fitdecode import FitReader, FitDataMessage
from tqdm import tqdm

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_PKL = os.path.join(os.path.dirname(__file__), 'runs.pkl')


def parse_gpx(path):
    with open(path, 'r') as f:
        gpx = gpxpy.parse(f)
    coords = []
    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                coords.append((p.longitude, p.latitude))
    return coords


def parse_fit(path):
    coords = []
    # Only process FitDataMessage frames of type 'record'
    with FitReader(path) as fit:
        for frame in fit:
            if not isinstance(frame, FitDataMessage) or frame.name != 'record':
                continue
            try:
                raw_lat = frame.get_value('position_lat')
                raw_lon = frame.get_value('position_long')
            except KeyError:
                # Skip records that don't include position fields
                continue
            if raw_lat is None or raw_lon is None:
                continue
            # convert semicircles → degrees
            lat = raw_lat * (180.0 / 2**31)
            lon = raw_lon * (180.0 / 2**31)
            coords.append((lon, lat))
    return coords


def _process_file(args):
    path, fname, mtime = args
    lower = fname.lower()
    coords = []

    if lower.endswith(('.fit.gz', '.gpx.gz')):
        inner_ext = lower[:-3].split('.')[-1]
        with gzip.open(path, 'rb') as f_in:
            tf = tempfile.NamedTemporaryFile(suffix='.' + inner_ext, delete=False)
            try:
                tf.write(f_in.read())
                tf.close()
                if inner_ext == 'fit':
                    coords = parse_fit(tf.name)
                else:
                    coords = parse_gpx(tf.name)
            finally:
                os.unlink(tf.name)
    elif lower.endswith('.fit'):
        coords = parse_fit(path)
    elif lower.endswith('.gpx'):
        coords = parse_gpx(path)

    if not coords:
        return None

    ls = LineString(coords)
    return {
        'src': fname,
        'mtime': mtime,
        'bbox': ls.bounds,
        'geoms': {
            'full': ls,
            'mid': ls.simplify(0.0001, preserve_topology=False),
            'coarse': ls.simplify(0.0005, preserve_topology=False)
        }
    }


def main():
    runs = {}
    rid = 0

    existing = {}
    if os.path.exists(OUTPUT_PKL):
        with open(OUTPUT_PKL, 'rb') as f:
            existing = pickle.load(f)

    cached = { (r.get('src'), r.get('mtime')): r for r in existing.values() }

    files = [f for f in os.listdir(RAW_DIR)
             if os.path.isfile(os.path.join(RAW_DIR, f))]

    tasks = []
    for fname in files:
        path = os.path.join(RAW_DIR, fname)
        mtime = os.path.getmtime(path)
        key = (fname, mtime)
        if key in cached:
            rid += 1
            runs[rid] = cached[key]
        else:
            tasks.append((path, fname, mtime))

    if tasks:
        with ProcessPoolExecutor() as exe:
            for result in tqdm(exe.map(_process_file, tasks),
                               total=len(tasks), desc="Processing", unit="file"):
                if result is None:
                    continue
                rid += 1
                runs[rid] = result

    with open(OUTPUT_PKL, 'wb') as f:
        pickle.dump(runs, f)

    print(f"Imported {len(runs)} runs → {OUTPUT_PKL}")


if __name__ == '__main__':
    main()


