# Run Heatmap

Visualize your entire running history on an interactive map.

This project processes raw GPS files (Strava export, Garmin Connect, etc.) and serves them with a lightweight Flask application. MapLibre GL JS renders a slippy map using OpenStreetMap tiles.

## Features

- Imports **FIT**, **GPX**, and **TCX** files as well as zipped Garmin exports
- Precomputes simplified geometries at multiple zoom levels for fast display
- R-tree spatial index and on-the-fly clipping for responsive panning/zooming
- Heatmap style polyline rendering on an OpenStreetMap basemap
- **Server–sent events** for progressive GeoJSON streaming with progress bars
- Draw a polygon to select an area and list all runs intersecting it
- Sidebar with run metadata (date, distance, duration) and controls to show/hide runs

## Prerequisites

- Linux/WSL with Python 3.10+
- System packages:

  ```bash
  sudo apt update
  sudo apt install python3-venv libspatialindex-dev
  ```

## Import your runs

1. Put your raw GPS files under `data/raw/` (git ignored):
   - Strava exports: `.fit.gz`, `.gpx.gz`, `.fit`, `.gpx`
   - Garmin Connect exports: `.zip` containing `.fit` or `.txt`/`.tcx`
2. Build the processed dataset:

   ```bash
   cd server
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python import_runs.py
   ```

   The command writes `runs.pkl` and prints a summary.

## Run the server

```bash
cd server
flask run
```

Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser.  
Pan/zoom to your area and watch the heatmap stream in.

## Selecting runs

Use the **⊙** button to draw a lasso polygon. The sidebar lists each run in that area with distance and duration. You can toggle runs on/off or clear the selection to return to viewing everything.

## Customizing style

Edit `web/index.html` if you want different colors or line widths:

```js
map.addLayer({
  id: 'runs-layer',
  type: 'line',
  source: 'runs',
  paint: {
    'line-color': 'rgba(255,0,0,0.4)',
    'line-width': ['interpolate', ['linear'], ['zoom'], 0, 0.5, 14, 2]
  }
});
```

Increase the opacity or adjust the width stops for a bolder heatmap.

## Workflow tips

- Drop new GPS files into `data/raw/` and rerun `python import_runs.py`.
- The server streams GeoJSON on demand—no tile generation step.
- Runs are cached using `lru_cache` and responses include caching headers.

Enjoy exploring your run history!
