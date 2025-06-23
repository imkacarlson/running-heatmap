import os
import gzip
import pickle
import tempfile
import zipfile
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


def process_file(file_path, file_name):
    """Process a single file and return coordinates if valid."""
    lower = file_name.lower()
    coords = []

    # handle .fit.gz and .gpx.gz
    if lower.endswith(('.fit.gz', '.gpx.gz')):
        inner_ext = lower[:-3].split('.')[-1]  # 'fit' or 'gpx'
        with gzip.open(file_path, 'rb') as f_in:
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

    # uncompressed .fit
    elif lower.endswith('.fit'):
        coords = parse_fit(file_path)

    # uncompressed .gpx
    elif lower.endswith('.gpx'):
        coords = parse_gpx(file_path)

    return coords


def count_total_artifacts(files):
    """Count total number of potential run artifacts across all files for progress tracking."""
    total = 0
    for fname in files:
        path = os.path.join(RAW_DIR, fname)
        if not os.path.isfile(path):
            continue
        
        lower = fname.lower()
        if lower.endswith('.zip'):
            with zipfile.ZipFile(path, 'r') as zf:
                total += sum(1 for name in zf.namelist() if name.lower().endswith('.fit'))
        elif lower.endswith(('.fit.gz', '.gpx.gz', '.fit', '.gpx')):
            total += 1
    return total


def main():
    runs = {}
    rid = 0
    skipped_count = 0

    files = [f for f in os.listdir(RAW_DIR)
             if os.path.isfile(os.path.join(RAW_DIR, f))]

    # Count total artifacts for progress tracking
    total_artifacts = count_total_artifacts(files)
    print(f"Found {total_artifacts} artifacts to process")
    
    # Create progress bar for individual artifacts
    pbar = tqdm(total=total_artifacts, desc="Processing artifacts", unit="artifact")

    for fname in files:
        path = os.path.join(RAW_DIR, fname)
        if not os.path.isfile(path):
            continue

        lower = fname.lower()

        # Handle zip files (Garmin Connect exports)
        if lower.endswith('.zip'):
            with zipfile.ZipFile(path, 'r') as zf:
                for zip_fname in zf.namelist():
                    if zip_fname.lower().endswith('.fit'):
                        with zf.open(zip_fname) as zf_file:
                            tf = tempfile.NamedTemporaryFile(suffix='.fit', delete=False)
                            try:
                                tf.write(zf_file.read())
                                tf.close()
                                coords = parse_fit(tf.name)
                                
                                if coords:
                                    rid += 1
                                    ls = LineString(coords)
                                    runs[rid] = {
                                        'bbox': ls.bounds,
                                        'geoms': {
                                            'full': ls,
                                            'high': ls.simplify(0.00005, preserve_topology=False),
                                            'mid': ls.simplify(0.0001, preserve_topology=False),
                                            'low': ls.simplify(0.0003, preserve_topology=False),
                                            'coarse': ls.simplify(0.0005, preserve_topology=False)
                                        }
                                    }
                                else:
                                    skipped_count += 1
                                # Update progress for each artifact processed from zip
                                pbar.update(1)
                            finally:
                                os.unlink(tf.name)
        else:
            # Handle individual files
            coords = process_file(path, fname)
            
            if coords:
                rid += 1
                ls = LineString(coords)
                runs[rid] = {
                    'bbox': ls.bounds,
                    'geoms': {
                        'full': ls,
                        'high': ls.simplify(0.00005, preserve_topology=False),
                        'mid': ls.simplify(0.0001, preserve_topology=False),
                        'low': ls.simplify(0.0003, preserve_topology=False),
                        'coarse': ls.simplify(0.0005, preserve_topology=False)
                    }
                }
            elif lower.endswith(('.fit.gz', '.gpx.gz', '.fit', '.gpx')):
                skipped_count += 1
            # Update progress regardless of whether coords were found
            if lower.endswith(('.fit.gz', '.gpx.gz', '.fit', '.gpx')):
                pbar.update(1)

    pbar.close()
    
    with open(OUTPUT_PKL, 'wb') as f:
        pickle.dump(runs, f)

    print(f"Imported {len(runs)} runs → {OUTPUT_PKL}")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} artifacts (no GPS coordinates found)")


if __name__ == '__main__':
    main()


