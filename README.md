# Run Heatmap

A local, interactive heatmap of your GPS runs—powered by Flask, MapLibre GL JS, and OpenStreetMap.

## Prerequisites

- WSL Ubuntu (or any Linux) with Python 3.10+  
- System packages:
  ```bash
  sudo apt update
  sudo apt install python3-venv libspatialindex-dev

* Place your raw GPX/FIT(.gz) files under `data/raw/` (this folder is git-ignored).

## Setup & Run

1. **Import runs**
   Generates `server/runs.pkl` from your raw files with pre-simplified geometries:

   ```bash
   cd server
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python import_runs.py
   ```

  The script shows a progress bar while processing files. When finished you should see:

   ```
   Imported <N> runs → runs.pkl
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

* **Adding new runs**: Drop new `.gpx`/`.fit.gz` files into `data/raw/` then re-run step 1.
* **Rebuilding data**: No external tile build—server streams GeoJSON slices on demand.
* **Performance**: The importer precomputes simplified geometries for multiple zoom levels. The server uses these along with an R-tree spatial index so panning and zooming stay responsive. The front-end caches data for a slightly larger area than is visible and refreshes it whenever the zoom level changes, so panning around nearby remains instant without sacrificing detail when zooming.

Enjoy exploring your run history!
