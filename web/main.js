const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',
  center: [-98, 39],
  zoom: 4
});

let activeController = null;

map.on('load', () => {
  map.addSource('runs', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  map.addLayer({
    id: 'runs-layer',
    type: 'line',
    source: 'runs',
    paint: {
      'line-color': 'rgba(255,0,0,0.15)',
      'line-width': ['interpolate', ['linear'], ['zoom'], 0, 1, 14, 5]
    }
  });
  fetchAndUpdate();
});

function fetchAndUpdate() {
  const b = map.getBounds();
  const z = Math.floor(map.getZoom());

  if (window.spatialIndex) {
    const data = window.spatialIndex.getRunsForBounds(b.getSouth(), b.getWest(), b.getNorth(), b.getEast(), z);
    map.getSource('runs').setData(data);
    return;
  }

  const url = `/api/runs?minLat=${b.getSouth()}&minLng=${b.getWest()}&maxLat=${b.getNorth()}&maxLng=${b.getEast()}&zoom=${z}`;

  if (activeController) {
    activeController.abort();
  }
  activeController = new AbortController();

  fetch(url, { signal: activeController.signal })
    .then(r => r.json())
    .then(data => map.getSource('runs').setData(data))
    .catch(err => {
      if (err.name !== 'AbortError') console.error(err);
    });
}

map.on('moveend', fetchAndUpdate);
