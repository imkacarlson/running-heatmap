import os
import gzip
import pickle
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from shapely.geometry import LineString
import gpxpy
from fitdecode import FitReader, FitDataMessage
from tqdm import tqdm

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
OUTPUT_PKL = os.path.join(os.path.dirname(__file__), 'runs.pkl')


def _normalize_activity_type(raw_type):
    if not raw_type:
        return 'other'
    t = str(raw_type).lower()
    if 'run' in t or 'jog' in t:
        return 'run'
    if 'bike' in t or 'biking' in t or 'cycl' in t or 'ride' in t:
        return 'bike'
    if 'walk' in t:
        return 'walk'
    if 'hike' in t:
        return 'hike'
    return 'other'


def parse_gpx(path):
    with open(path, 'r') as f:
        gpx = gpxpy.parse(f)
    coords = []
    metadata = {
        'start_time': None,
        'end_time': None,
        'distance': 0,
        'duration': 0,
        'activity_type': 'other',
        'activity_raw': None
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
        metadata['duration'] = (points_with_time[-1].time - points_with_time[0].time).total_seconds()
        
    # Calculate distance from GPX
    if gpx.tracks:
        metadata['distance'] = gpx.length_3d() or gpx.length_2d() or 0

    metadata['activity_raw'] = raw_type
    metadata['activity_type'] = _normalize_activity_type(raw_type)

    return coords, metadata


def parse_fit(path):
    coords = []
    metadata = {
        'start_time': None,
        'end_time': None,
        'distance': 0,
        'duration': 0,
        'activity_type': 'other',
        'activity_raw': None
    }
    
    timestamps = []
    
    raw_type = None
    with FitReader(path) as fit:
        for frame in fit:
            if not isinstance(frame, FitDataMessage):
                continue

            # Extract session metadata
            if frame.name == 'session':
                try:
                    if frame.get_value('start_time'):
                        metadata['start_time'] = frame.get_value('start_time')
                    if frame.get_value('total_elapsed_time'):
                        metadata['duration'] = frame.get_value('total_elapsed_time')
                    if frame.get_value('total_distance'):
                        metadata['distance'] = frame.get_value('total_distance')
                    if frame.get_value('sport'):
                        raw_type = frame.get_value('sport')
                except KeyError:
                    pass
                    
            # Extract record data for coordinates
            elif frame.name == 'record':
                try:
                    raw_lat = frame.get_value('position_lat')
                    raw_lon = frame.get_value('position_long')
                    timestamp = frame.get_value('timestamp')
                except KeyError:
                    continue
                    
                if raw_lat is None or raw_lon is None:
                    continue
                    
                # convert semicircles → degrees
                lat = raw_lat * (180.0 / 2**31)
                lon = raw_lon * (180.0 / 2**31)
                coords.append((lon, lat))
                
                if timestamp:
                    timestamps.append(timestamp)
    
    # Fallback metadata from timestamps if session data not available
    if timestamps and not metadata['start_time']:
        metadata['start_time'] = timestamps[0]
        metadata['end_time'] = timestamps[-1]
        metadata['duration'] = (timestamps[-1] - timestamps[0]).total_seconds()

    metadata['activity_raw'] = raw_type
    metadata['activity_type'] = _normalize_activity_type(raw_type)

    return coords, metadata


def parse_tcx(path):
    coords = []
    metadata = {
        'start_time': None,
        'end_time': None,
        'distance': 0,
        'duration': 0,
        'activity_type': 'other',
        'activity_raw': None
    }
    
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        
        # TCX namespace
        ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        # Extract activity metadata
        activity = root.find('.//tcx:Activity', ns)
        if activity is not None:
            # Activity type attribute
            if 'Sport' in activity.attrib:
                metadata['activity_raw'] = activity.get('Sport')
            # Get activity ID (start time)
            activity_id = activity.get('Id')
            if activity_id:
                try:
                    metadata['start_time'] = datetime.fromisoformat(activity_id.replace('Z', '+00:00'))
                except ValueError:
                    pass
        
        # Extract lap data for distance and time
        for lap in root.findall('.//tcx:Lap', ns):
            try:
                total_time_elem = lap.find('tcx:TotalTimeSeconds', ns)
                distance_elem = lap.find('tcx:DistanceMeters', ns)
                
                if total_time_elem is not None:
                    metadata['duration'] += float(total_time_elem.text)
                if distance_elem is not None:
                    metadata['distance'] += float(distance_elem.text)
            except (ValueError, TypeError):
                pass
        
        # Find all trackpoints with position data
        timestamps = []
        for trackpoint in root.findall('.//tcx:Trackpoint[tcx:Position]', ns):
            pos = trackpoint.find('tcx:Position', ns)
            if pos is not None:
                lat_elem = pos.find('tcx:LatitudeDegrees', ns)
                lon_elem = pos.find('tcx:LongitudeDegrees', ns)
                time_elem = trackpoint.find('tcx:Time', ns)
                
                if lat_elem is not None and lon_elem is not None:
                    try:
                        lat = float(lat_elem.text)
                        lon = float(lon_elem.text)
                        coords.append((lon, lat))
                        
                        if time_elem is not None:
                            timestamp = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
                            timestamps.append(timestamp)
                    except (ValueError, TypeError):
                        continue
        
        # Set end time from last trackpoint if available
        if timestamps:
            if not metadata['start_time']:
                metadata['start_time'] = timestamps[0]
            metadata['end_time'] = timestamps[-1]
            
        metadata['activity_type'] = _normalize_activity_type(metadata['activity_raw'])

    except (ET.ParseError, FileNotFoundError):
        pass

    return coords, metadata


def process_file(file_path, file_name):
    """Process a single file and return coordinates and metadata if valid."""
    lower = file_name.lower()
    coords = []
    metadata = {
        'start_time': None,
        'end_time': None,
        'distance': 0,
        'duration': 0,
        'activity_type': 'other',
        'activity_raw': None
    }

    # handle .fit.gz and .gpx.gz
    if lower.endswith(('.fit.gz', '.gpx.gz')):
        inner_ext = lower[:-3].split('.')[-1]  # 'fit' or 'gpx'
        with gzip.open(file_path, 'rb') as f_in:
            tf = tempfile.NamedTemporaryFile(suffix='.' + inner_ext, delete=False)
            try:
                tf.write(f_in.read())
                tf.close()
                if inner_ext == 'fit':
                    coords, metadata = parse_fit(tf.name)
                else:
                    coords, metadata = parse_gpx(tf.name)
            finally:
                os.unlink(tf.name)

    # uncompressed .fit
    elif lower.endswith('.fit'):
        coords, metadata = parse_fit(file_path)

    # uncompressed .gpx
    elif lower.endswith('.gpx'):
        coords, metadata = parse_gpx(file_path)

    # TCX files (sometimes disguised as .txt)
    elif lower.endswith(('.tcx', '.txt')):
        coords, metadata = parse_tcx(file_path)

    return coords, metadata


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
                total += sum(1 for name in zf.namelist() 
                           if name.lower().endswith(('.fit', '.txt', '.tcx')))
        elif lower.endswith(('.fit.gz', '.gpx.gz', '.fit', '.gpx', '.tcx', '.txt')):
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
                    zip_lower = zip_fname.lower()
                    if zip_lower.endswith(('.fit', '.txt', '.tcx')):
                        with zf.open(zip_fname) as zf_file:
                            # Determine appropriate suffix and parser
                            if zip_lower.endswith('.fit'):
                                suffix = '.fit'
                                parser = parse_fit
                            elif zip_lower.endswith(('.txt', '.tcx')):
                                suffix = '.tcx'
                                parser = parse_tcx
                            else:
                                continue
                                
                            tf = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                            try:
                                tf.write(zf_file.read())
                                tf.close()
                                coords, metadata = parser(tf.name)
                                
                                if coords and len(coords) >= 2:
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
                                        },
                                        'metadata': {
                                            'start_time': metadata['start_time'],
                                            'end_time': metadata['end_time'],
                                            'distance': metadata['distance'],
                                            'duration': metadata['duration'],
                                            'activity_type': metadata['activity_type'],
                                            'activity_raw': metadata['activity_raw'],
                                            'source_file': zip_fname
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
            coords, metadata = process_file(path, fname)
            
            if coords and len(coords) >= 2:
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
                    },
                    'metadata': {
                        'start_time': metadata['start_time'],
                        'end_time': metadata['end_time'],
                        'distance': metadata['distance'],
                        'duration': metadata['duration'],
                        'activity_type': metadata['activity_type'],
                        'activity_raw': metadata['activity_raw'],
                        'source_file': fname
                    }
                }
            elif lower.endswith(('.fit.gz', '.gpx.gz', '.fit', '.gpx', '.tcx', '.txt')):
                skipped_count += 1
            # Update progress regardless of whether coords were found
            if lower.endswith(('.fit.gz', '.gpx.gz', '.fit', '.gpx', '.tcx', '.txt')):
                pbar.update(1)

    pbar.close()
    
    with open(OUTPUT_PKL, 'wb') as f:
        pickle.dump(runs, f)

    print(f"Imported {len(runs)} runs → {OUTPUT_PKL}")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} artifacts (no GPS coordinates found)")


if __name__ == '__main__':
    main()


