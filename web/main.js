const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',
  center: [-98, 39],
  zoom: 4
});

let activeController = null;
const caches = {}; // zoom -> {bounds, data}
const cacheOrder = [];
const MAX_CACHES = 3;
let lastCenter = null;
let lastZoom = null;

function withinBounds(outer, inner) {
  return (
    inner.getSouth() >= outer.getSouth() &&
    inner.getNorth() <= outer.getNorth() &&
    inner.getWest() >= outer.getWest() &&
    inner.getEast() <= outer.getEast()
  );
}

function getCached(view, zoom) {
  const levels = Object.keys(caches)
    .map((z) => parseInt(z, 10))
    .sort((a, b) => b - a);
  for (const z of levels) {
    const entry = caches[z];
    if (z >= zoom && withinBounds(entry.bounds, view)) {
      return entry.data;
    }
  }
  return null;
}

function storeCache(zoom, bounds, data) {
  caches[zoom] = { bounds, data };
  const idx = cacheOrder.indexOf(zoom);
  if (idx !== -1) cacheOrder.splice(idx, 1);
  cacheOrder.unshift(zoom);
  if (cacheOrder.length > MAX_CACHES) {
    const old = cacheOrder.pop();
    delete caches[old];
  }
}

function marginForZoom(z) {
  if (z >= 15) return 4.0;
  if (z >= 13) return 2.0;
  if (z >= 11) return 0.5;
  return 0.25;
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
  const center = map.getCenter();

  const cached = getCached(view, z);
  if (cached) {
    map.getSource('runs').setData(cached);
  }

  const latSpan = view.getNorth() - view.getSouth();
  const lngSpan = view.getEast() - view.getWest();
  const centerMoved =
    !lastCenter ||
    Math.abs(center.lat - lastCenter.lat) > latSpan * 0.2 ||
    Math.abs(center.lng - lastCenter.lng) > lngSpan * 0.2 ||
    z !== lastZoom;

  if (!centerMoved && cached) {
    return;
  }

  const margin = marginForZoom(z);
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
      const bounds = new maplibregl.LngLatBounds([minLng, minLat], [maxLng, maxLat]);
      storeCache(z, bounds, data);
      map.getSource('runs').setData(data);
      lastCenter = center;
      lastZoom = z;
    })
    .catch(err => {
      if (err.name !== 'AbortError') console.error(err);
    });
}

map.on('moveend', fetchAndUpdate);
