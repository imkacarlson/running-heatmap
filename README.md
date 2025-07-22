# Running Heatmap

Visualize your entire GPS activity history on an interactive map.

This project processes raw GPS files (Strava export, Garmin Connect, etc.) and serves them with a lightweight Flask application. MapLibre GL JS renders a slippy map using OpenStreetMap tiles.

## Features

- Import **FIT**, **GPX**, and **TCX** files (Garmin archives are handled automatically)
- Precompute simplified geometries at several zoom levels for fast drawing
- R-tree spatial index for quick bounding-box and lasso queries
- Optional **PMTiles** vector tiles for smooth offline rendering
- Heatmap style polylines on an OpenStreetMap basemap
- Draw a polygon to select an area and list the intersecting activities
- Sidebar shows metadata (type, date, distance, duration) and lets you toggle individual runs
- Upload new **GPX** files right in the browser—they are stored locally and persist between sessions
- Extras panel with last uploaded activity and more tools
- `build_mobile.py` packages an offline Android app (see **MOBILE_SETUP.md**)

## Prerequisites

- Linux/WSL with Python 3.10+
- System packages:

  ```bash
  sudo apt update
  sudo apt install python3-venv libspatialindex-dev
  sudo apt install tippecanoe
  ```

## Import your activities

1. Put your raw GPS files under `data/raw/` (git ignored):
   - Strava exports: `.fit.gz`, `.gpx.gz`, `.fit`, `.gpx`
   - Garmin Connect exports: `.zip` containing `.fit` or `.txt`/`.tcx`
     - After requesting a Garmin export at https://www.garmin.com/en-US/account/datamanagement/exportdata/, look under
       `DI_CONNECT/DI-Connect-Fitness-Uploaded-Files/` for many
       `UploadedFiles*.zip` archives. Drop these zip files into
       `data/raw/` to import them.
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
- For even faster loading, run `python make_pmtiles.py` to generate `runs.pmtiles` (requires Tippecanoe). The mobile and web apps automatically use this file and prefetch nearby map tiles for smoother panning.
- A dataset of ~5k runs fits in a `runs.pmtiles` file around 40&nbsp;MB while keeping lasso queries fast offline.

## Mobile app

Run `python build_mobile.py` inside the `server/` directory to generate an
Android APK with your activities bundled for offline viewing. The script will verify
prerequisites, build the assets and optionally package the app using Capacitor.
For a faster rebuild when only templates or JavaScript change, pass
`--quick` to reuse the existing data and skip the conversion step.

After the build finishes you can install the APK directly from WSL:
```
APK=mobile/android/app/build/outputs/apk/debug/app-debug.apk
adb install -r $(wslpath -w "$APK")
```
See **MOBILE_SETUP.md** for a detailed guide on setting up the Windows `adb` server and debugging with Chrome DevTools.

Enjoy exploring your activity history!
