const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',
  center: [-98, 39],
  zoom: 4
});

let activeController = null;
let cachedBounds = null;
let cachedData = null;
let cachedZoom = null;

function withinBounds(outer, inner) {
  return (
    inner.getSouth() >= outer.getSouth() &&
    inner.getNorth() <= outer.getNorth() &&
    inner.getWest() >= outer.getWest() &&
    inner.getEast() <= outer.getEast()
  );
}

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
  const view = map.getBounds();
  const z = Math.floor(map.getZoom());

  if (cachedBounds && cachedZoom === z && withinBounds(cachedBounds, view)) {
    map.getSource('runs').setData(cachedData);
    return;
  }

  const margin = 0.25; // fetch 25% beyond current view
  const latExt = (view.getNorth() - view.getSouth()) * margin;
  const lngExt = (view.getEast() - view.getWest()) * margin;
  const minLat = view.getSouth() - latExt;
  const minLng = view.getWest() - lngExt;
  const maxLat = view.getNorth() + latExt;
  const maxLng = view.getEast() + lngExt;
  const url = `/api/runs?minLat=${minLat}&minLng=${minLng}&maxLat=${maxLat}&maxLng=${maxLng}&zoom=${z}`;

  if (activeController) {
    activeController.abort();
  }
  activeController = new AbortController();

  fetch(url, { signal: activeController.signal })
    .then(r => r.json())
    .then(data => {
      cachedBounds = new maplibregl.LngLatBounds([minLng, minLat], [maxLng, maxLat]);
      cachedData = data;
      cachedZoom = z;
      map.getSource('runs').setData(data);
    })
    .catch(err => {
      if (err.name !== 'AbortError') console.error(err);
    });
}

map.on('moveend', fetchAndUpdate);
