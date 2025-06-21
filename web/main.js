const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',
  center: [-98, 39],
  zoom: 4
});

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
  const url = `/api/runs?minLat=${b.getSouth()}&minLng=${b.getWest()}&maxLat=${b.getNorth()}&maxLng=${b.getEast()}&zoom=${z}`;
  fetch(url)
    .then(r => r.json())
    .then(data => map.getSource('runs').setData(data));
}

map.on('moveend', fetchAndUpdate);