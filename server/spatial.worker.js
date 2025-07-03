// Web worker for spatial queries
self.importScripts('rbush.min.js');

let runs = null;
let tree = null;

async function fetchJson(base) {
  const gzUrl = base + '.gz';
  try {
    const resp = await fetch(gzUrl);
    if (resp.ok) {
      if (resp.headers.get('content-encoding') === 'gzip') {
        return resp.json();
      }
      const ds = new DecompressionStream('gzip');
      const decompressed = resp.body.pipeThrough(ds);
      const text = await new Response(decompressed).text();
      return JSON.parse(text);
    }
  } catch (e) {}
  const resp = await fetch(base);
  if (!resp.ok) throw new Error('failed fetch');
  return resp.json();
}

function bboxIntersects(b1, b2) {
  return !(b1[2] < b2[0] || b1[0] > b2[2] || b1[3] < b2[1] || b1[1] > b2[3]);
}

function getZoomLevel(z) {
  if (z >= 15) return 'full';
  if (z >= 13) return 'high';
  if (z >= 10) return 'mid';
  return 'low';
}

async function load() {
  runs = await fetchJson('data/runs.json');
  const index = await fetchJson('data/spatial_index.json');
  tree = new RBush();
  tree.load(index.map(i => ({minX: i.bbox[0], minY: i.bbox[1], maxX: i.bbox[2], maxY: i.bbox[3], id: i.id})));
  postMessage({type: 'ready'});
}

load();

self.onmessage = async e => {
  if (e.data.type === 'add') {
    const r = e.data.run;
    runs[r.id] = {geoms: r.geoms, bbox: r.bbox};
    tree.insert({minX:r.bbox[0],minY:r.bbox[1],maxX:r.bbox[2],maxY:r.bbox[3],id:r.id});
    return;
  }
  if (!runs || !tree) return;
  const {bbox, zoom, filterIds, batch} = e.data;
  const ids = tree.search({minX: bbox[0], minY: bbox[1], maxX: bbox[2], maxY: bbox[3]}).map(i => i.id);
  let filtered = ids;
  if (filterIds) {
    const set = new Set(filterIds);
    filtered = ids.filter(id => set.has(id));
  }
  const features = [];
  for (let i = 0; i < filtered.length; i++) {
    const id = filtered[i];
    const run = runs[id];
    if (!run) continue;
    const zoomLevel = getZoomLevel(zoom);
    let geom = run.geoms[zoomLevel] || run.geoms.mid || run.geoms.low || run.geoms.high || run.geoms.full;
    if (!geom || !geom.coordinates || geom.coordinates.length === 0) continue;
    if (!bboxIntersects(run.bbox, bbox)) continue;
    features.push({type:'Feature', id, geometry: geom, properties:{id}});
    if (features.length >= batch) {
      postMessage({type:'chunk', features});
      features.length = 0;
    }
    postMessage({type:'progress', value: Math.floor((i+1)*100/filtered.length)});
  }
  if (features.length)
    postMessage({type:'chunk', features});
  postMessage({type:'complete'});
};
