# Run Heatmap

A local, interactive heatmap of your GPS runs—powered by Flask, MapLibre GL JS, and OpenStreetMap. Supports data from Strava, Garmin Connect, and other GPS devices.

## Prerequisites

- WSL Ubuntu (or any Linux) with Python 3.10+  
- System packages:
  ```bash
  sudo apt update
  sudo apt install python3-venv libspatialindex-dev

* Place your raw GPS files under `data/raw/` (this folder is git-ignored):
  - **Strava exports**: `.fit.gz`, `.gpx.gz`, `.fit`, `.gpx` files
  - **Garmin Connect exports**: `.zip` files containing `.fit` or `.txt` (TCX) files

## Setup & Run

1. **Import runs**
   Generates `server/runs.pkl` from your raw GPS files with pre-simplified geometries. Supports multiple formats including FIT, GPX, and TCX:

   ```bash
   cd server
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python import_runs.py
   ```

  The script shows progress while processing artifacts and reports results:

   ```
   Found 628 artifacts to process
   Processing artifacts: 100%|████████████| 628/628 [01:32<00:00,  6.81artifact/s]
   Imported 245 runs → runs.pkl
   Skipped 383 artifacts (no GPS coordinates found)
   ```

2. **Start the server**
   Serves the API and front-end:

   ```bash
   cd server
   flask run
   ```

   By default, it runs at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

3. **View in browser**
   Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

   * The OpenStreetMap basemap (roads, trails, state lines) will load automatically.
   * Pan & zoom into your running area (e.g. Washington, D.C. at zoom 10–12).
   * Your runs appear as thin, semi-transparent red lines that stack into a heatmap.

## Styling & Tuning

Adjust line thickness and opacity in **web/index.html**:

```js
map.addLayer({
  id: 'runs-layer',
  type: 'line',
  source: 'runs',
  paint: {
    'line-color': 'rgba(255,0,0,0.4)', // change 0.4 → 1.0 for bolder
    'line-width': [
      'interpolate', ['linear'], ['zoom'],
      0,  0.5,  // 0.5px at zoom 0
      14, 2     // 2px at zoom 14
    ]
  }
});
```

* **Opacity**: Increase the last number in `rgba(...)` up to `1.0` for stronger color.
* **Width stops**: Tweak the `0.5` and `2` values to make lines thinner or thicker.

## Workflow

* **Adding new runs**: Drop new GPS files (individual `.fit`/`.gpx` files or Garmin Connect `.zip` exports) into `data/raw/` then re-run step 1.
* **Rebuilding data**: No external tile build—server streams GeoJSON slices on demand.
* **Performance**: The importer precomputes simplified geometries for multiple zoom levels. The server uses these along with an R-tree spatial index and fast bounding box clipping so panning and zooming stay responsive even with dense data.

Enjoy exploring your run history!
