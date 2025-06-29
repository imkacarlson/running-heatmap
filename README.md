# Activity Heatmap

Visualize your entire GPS activity history on an interactive map.

This project processes raw GPS files (Strava export, Garmin Connect, etc.) and serves them with a lightweight Flask application. MapLibre GL JS renders a slippy map using OpenStreetMap tiles.

## Features

- Imports **FIT**, **GPX**, and **TCX** files as well as zipped Garmin exports
- Precomputes simplified geometries at multiple zoom levels for fast display
- R-tree spatial index and on-the-fly clipping for responsive panning/zooming
- Heatmap style polyline rendering on an OpenStreetMap basemap
- **Server–sent events** for progressive GeoJSON streaming with progress bars
- Draw a polygon to select an area and list all activities intersecting it
- Sidebar with activity metadata (type, date, distance, duration) and controls to show/hide activities
- Upload new **GPX** files directly from the browser
- Optional script to build an offline Android app (see **MOBILE_SETUP.md**)

## Prerequisites

- Linux/WSL with Python 3.10+
- System packages:

  ```bash
  sudo apt update
  sudo apt install python3-venv libspatialindex-dev
  ```

## Import your activities

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

## Selecting activities

Use the **⊙** button to draw a lasso polygon. The sidebar lists each activity in that area with distance and duration. You can toggle activities on/off or clear the selection to return to viewing everything.

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
- Activities are cached using `lru_cache` and responses include caching headers.

## Mobile app

Run `python build_mobile.py` inside the `server/` directory to generate an
Android APK with your activities bundled for offline viewing. The script will verify
prerequisites, build the assets and optionally package the app using Capacitor.
See **MOBILE_SETUP.md** for a detailed guide.

Enjoy exploring your activity history!
