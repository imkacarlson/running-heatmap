// Mobile spatial index and data management
class SpatialIndex {
  constructor() {
    this.loaded = false;
    this.spatialIndex = [];
    this.userRuns = [];
    this.nextId = 1;
    this.worker = null;
  }

  _handleWorkerMessage(e) {
    if (!this._pending) return;
    if (e.data.type === 'chunk') {
      this._features.push(...e.data.features);
    } else if (e.data.type === 'progress') {
      if (this._progress) this._progress(e.data.value);
    } else if (e.data.type === 'complete') {
      this._pending.resolve({type:'FeatureCollection', features:this._features});
      this._pending = null;
      this._features = [];
    }
  }

  _queryWorker(bbox, zoom, ids, progress) {
    return new Promise(resolve => {
      this._pending = {resolve};
      this._features = [];
      this._progress = progress;
      this.worker.postMessage({bbox, zoom, filterIds: ids, batch:500});
    });
  }

  async loadData() {
    try {
      console.log('[HEATMAP-DEBUG] Initializing SpatialIndex.loadData');
      this.spatialIndex = [];
      this.loadUserRuns();

      this.nextId = this.userRuns.reduce((m, r) => Math.max(m, parseInt(r.id)), 0) + 1;

      this.loaded = true;
      console.log(`[HEATMAP-DEBUG] SpatialIndex.loadData complete. Found ${this.userRuns.length} user runs.`);

      // Show user feedback
      if (window.showStatusForDebug) {
        window.showStatusForDebug(`Loaded ${this.userRuns.length} runs`, 1500);
      }

    } catch (error) {
      console.error('[HEATMAP-DEBUG] Fatal error in SpatialIndex.loadData:', error);
      if (window.showStatusForDebug) {
        window.showStatusForDebug(`Error loading data: ${error.message}`, 5000);
      }
      throw error;
    }
  }

  loadUserRuns() {
    console.log('[HEATMAP-DEBUG] Checking for locally stored runs...');
    const stored = localStorage.getItem('userRuns');
    if (!stored) {
      console.log('[HEATMAP-DEBUG] No stored runs found.');
      return;
    }
    try {
      const arr = JSON.parse(stored);
      arr.forEach(run => {
        const id = run.id.toString();
        this.spatialIndex.push({ id: parseInt(id), bbox: run.bbox });
        this.userRuns.push(run);
        const num = parseInt(id);
        if (num >= this.nextId) this.nextId = num + 1;
      });
      console.log(`[HEATMAP-DEBUG] Loaded ${arr.length} user runs from localStorage.`);
    } catch (e) {
      console.error('[HEATMAP-DEBUG] Failed to parse stored runs:', e);
      if (window.showStatusForDebug) {
        window.showStatusForDebug(`Error parsing stored runs: ${e.message}`, 3000);
      }
    }
  }

  saveUserRuns() {
    try {
      localStorage.setItem('userRuns', JSON.stringify(this.userRuns));
    } catch (e) {
      console.error('Failed to save user runs', e);
    }
  }

  async updateServerData(newRuns) {
    const response = await fetch('/update_runs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ runs: newRuns })
    });

    if (!response.ok) {
      throw new Error('Failed to update server data');
    }

    return response.json();
  }

  async reloadPMTiles() {
    console.log('[HEATMAP-HTTP] Starting reloadPMTiles with HTTP Range Server...');
    try {
      // Remove existing layers and sources
      if (map.getLayer('runsVec')) {
        console.log('[HEATMAP-HTTP] Removing existing layer: runsVec');
        map.removeLayer('runsVec');
      }
      if (map.getSource('runsVec')) {
        console.log('[HEATMAP-HTTP] Removing existing source: runsVec');
        map.removeSource('runsVec');
      }

      // Clear PMTiles protocol to force cache refresh
      if (maplibregl.removeProtocol) {
        console.log('[HEATMAP-HTTP] Clearing pmtiles protocol cache.');
        maplibregl.removeProtocol('pmtiles');
      }

      // Wait a moment for cleanup
      await new Promise(resolve => setTimeout(resolve, 100));

      // Re-register protocol
      console.log('[HEATMAP-HTTP] Re-registering pmtiles protocol.');
      const protocol = new pmtiles.Protocol();
      maplibregl.addProtocol('pmtiles', protocol.tile.bind(protocol));
      
      // Get server URL (should already be running)
      let serverUrl = 'http://localhost:8080';
      if (window.HttpRangeServer) {
        try {
          const serverStatus = await window.HttpRangeServer.getServerStatus();
          if (serverStatus.running) {
            serverUrl = `http://localhost:${serverStatus.port}`;
          }
        } catch (serverError) {
          console.warn('[HEATMAP-HTTP] Could not get server status:', serverError);
        }
      }

      // Configure PMTiles to use HTTP range requests  
      const timestamp = Date.now();
      const pmtilesUrl = `${serverUrl}/data/runs.pmtiles?t=${timestamp}`;
      console.log(`[HEATMAP-HTTP] Using PMTiles URL: ${pmtilesUrl}`);

      // Create PMTiles source from HTTP URL
      const pmtilesSource = new pmtiles.PMTiles(pmtilesUrl);
      protocol.add(pmtilesSource);
      console.log('[HEATMAP-HTTP] Successfully registered PMTiles instance.');

      // Add the map source using the pmtiles protocol
      const mapSourceUrl = `pmtiles://${pmtilesUrl}`;
      console.log(`[HEATMAP-HTTP] Adding map source with URL: ${mapSourceUrl}`);
      
      map.addSource('runsVec', {
        type: 'vector',
        url: mapSourceUrl,
        buffer: 128,
        maxzoom: 16,
        minzoom: 5
      });

      map.addLayer({
        id: 'runsVec',
        source: 'runsVec',
        'source-layer': 'runs',
        type: 'line',
        paint: {
          'line-color': 'rgba(255,0,0,0.5)',
          'line-width': ['interpolate', ['linear'], ['zoom'], 0, 1, 14, 3]
        },
        maxzoom: 24
      });

      console.log('[HEATMAP-HTTP] PMTiles source and layer added to map.');

      // Force map refresh
      map.panBy([1, 1]);
      setTimeout(() => map.panBy([-1, -1]), 200);

    } catch (error) {
      console.error('[HEATMAP-HTTP] Error in reloadPMTiles:', error);
      if (window.showStatusForDebug) {
        window.showStatusForDebug(`Error reloading tiles: ${error.message}`, 5000);
      }
    }
  }


  simplify(coords, tolerance) {
    if (coords.length <= 2) return coords;
    const simplified = [coords[0]];
    let last = coords[0];
    for (let i = 1; i < coords.length - 1; i++) {
      const c = coords[i];
      const dx = c[0] - last[0];
      const dy = c[1] - last[1];
      if (Math.sqrt(dx * dx + dy * dy) > tolerance) {
        simplified.push(c);
        last = c;
      }
    }
    simplified.push(coords[coords.length - 1]);
    return simplified;
  }

  async addRun(coords, metadata) {
    const id = this.nextId++;
    const bbox = this.getPolygonBbox(coords);
    const geoms = {
      full: { type: 'LineString', coordinates: coords },
      high: { type: 'LineString', coordinates: this.simplify(coords, 0.0001) },
      mid: { type: 'LineString', coordinates: this.simplify(coords, 0.0005) },
      low: { type: 'LineString', coordinates: this.simplify(coords, 0.001) }
    };

    const run = { id: id.toString(), geoms, bbox, metadata };
    
    // Add to both spatial index and user runs for immediate display
    this.spatialIndex.push({ id: parseInt(id), bbox: bbox });
    this.userRuns.push(run);

    try {
      await this.updateServerData([
        { id: id, coords: coords, metadata: metadata }
      ]);

      // Try to reload PMTiles to show server-side data
      try {
        await this.reloadPMTiles();
        
        // Only clear local data if PMTiles reload succeeds
        localStorage.removeItem('userRuns');
        
        // Remove the uploaded run from local storage since it's now in PMTiles
        const indexToRemove = this.spatialIndex.findIndex(entry => entry.id === parseInt(id));
        if (indexToRemove !== -1) {
          this.spatialIndex.splice(indexToRemove, 1);
        }
        const runToRemove = this.userRuns.findIndex(r => r.id === id.toString());
        if (runToRemove !== -1) {
          this.userRuns.splice(runToRemove, 1);
        }
        
        console.log('[HEATMAP-DEBUG] Successfully synced with server, run moved to PMTiles');
        
      } catch (pmtilesError) {
        console.error('[HEATMAP-DEBUG] PMTiles reload failed, keeping run in local storage:', pmtilesError);
        // Save to localStorage so run persists even if PMTiles reload failed
        this.saveUserRuns();
        if (window.showStatusForDebug) {
          window.showStatusForDebug('Uploaded successfully, but map reload failed. Run saved locally.', 4000);
        }
      }

    } catch (error) {
      console.error('Failed to sync with server, keeping local:', error);
      this.saveUserRuns();
      if (window.showStatusForDebug) {
        window.showStatusForDebug('Upload failed, run saved locally: ' + error.message, 4000);
      }
    }

    return id;
  }

  getRunsForBounds(minLat, minLng, maxLat, maxLng, zoom) {
    if (!this.loaded) {
      return { type: 'FeatureCollection', features: [] };
    }

    const features = [];
    const bbox = [minLng, minLat, maxLng, maxLat];
    
    // Use spatial index to find runs that intersect with bounds
    for (const indexEntry of this.spatialIndex) {
      const runBbox = indexEntry.bbox;

      // Check if run bbox intersects with query bbox
      if (this.bboxIntersects(runBbox, bbox)) {
        const run = this.userRuns.find(r => r.id.toString() === indexEntry.id.toString());
        const runData = run;
        const runId = indexEntry.id.toString();
        if (!runData) continue;
        
        if (runData && runData.geoms) {
          // Choose appropriate zoom level with fallback
          const zoomLevel = this.getZoomLevel(zoom);
          let geom = runData.geoms[zoomLevel];

          // Fallback to other zoom levels if current one is invalid/empty
          if (!geom || !geom.coordinates || geom.coordinates.length === 0) {
            geom = runData.geoms['mid'] || runData.geoms['low'] || runData.geoms['high'] || runData.geoms['full'];
          }
          
          // Validate geometry before adding
          if (geom && geom.coordinates && geom.coordinates.length > 1) {
            features.push({
              type: 'Feature',
              geometry: geom,
              properties: {
                id: runId,
                zoom: zoom,
                zoomLevel: zoomLevel,
                ...runData.metadata
              }
            });
          } else {
            console.warn(`Invalid geometry for run ${runId} at zoom ${zoom}:`, geom);
            // Show user notification for debugging
            if (window.showStatusForDebug) {
              window.showStatusForDebug(`Run ${runId} has invalid geometry at zoom ${zoom}`, 2000);
            }
          }
        }
      }
    }

    return {
      type: 'FeatureCollection',
      features: features
    };
  }

  async getRunsForBoundsAsync(minLat, minLng, maxLat, maxLng, zoom) {
    if (!this.loaded) {
      return { type: 'FeatureCollection', features: [] };
    }
    const bbox = [minLng, minLat, maxLng, maxLat];
    return this._queryWorker(bbox, zoom, null, null);
  }

  filterRunsByIds(runIds, minLat, minLng, maxLat, maxLng, zoom, progressCb) {
    if (!this.loaded) {
      return Promise.resolve({ type: 'FeatureCollection', features: [] });
    }
    const bbox = [minLng, minLat, maxLng, maxLat];
    return this._queryWorker(bbox, zoom, runIds, progressCb);
  }

  // Query uploaded runs using the spatial index (legacy support)
  getRunsInPolygon(polygonCoords) {
    if (!this.loaded) return [];

    const runs = [];
    const polyBbox = this.getPolygonBbox(polygonCoords);

    for (const entry of this.spatialIndex) {
      if (this.bboxIntersects(entry.bbox, polyBbox)) {
        const run = this.userRuns.find(r => r.id.toString() === entry.id.toString());
        if (run && this.geometryIntersectsPolygon(run.geoms.full, polygonCoords)) {
          runs.push({ id: parseInt(run.id), metadata: run.metadata, bbox: run.bbox });
        }
      }
    }

    return runs;
  }

  async queryPMTilesInPolygon(polygonCoords) {
    if (!this.loaded) return [];

    const features = map.queryRenderedFeatures(null, {
      layers: ['runsVec']
    });

    const runs = [];
    features.forEach(feature => {
      const props = feature.properties;
      const runBbox = feature.bbox || this.getGeometryBbox(feature.geometry);
      if (this.geometryIntersectsPolygon(feature.geometry, polygonCoords)) {
        runs.push({
          id: props.id,
          metadata: {
            start_time: props.start_time,
            distance: props.distance,
            duration: props.duration,
            activity_type: props.activity_type,
            activity_raw: props.activity_raw
          },
          bbox: runBbox
        });
      }
    });

    return runs;
  }

  getZoomLevel(zoom) {
    if (zoom >= 15) return 'full';
    if (zoom >= 13) return 'high';
    if (zoom >= 10) return 'mid';
    return 'low';
  }

  bboxIntersects(bbox1, bbox2) {
    return !(bbox1[2] < bbox2[0] || bbox1[0] > bbox2[2] || 
             bbox1[3] < bbox2[1] || bbox1[1] > bbox2[3]);
  }

  getPolygonBbox(coords) {
    let minLng = Infinity, minLat = Infinity;
    let maxLng = -Infinity, maxLat = -Infinity;
    
    for (const [lng, lat] of coords) {
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    }
    
    return [minLng, minLat, maxLng, maxLat];
  }

  getGeometryBbox(geometry) {
    const coords = geometry.coordinates;
    let minLng = Infinity, minLat = Infinity;
    let maxLng = -Infinity, maxLat = -Infinity;

    coords.forEach(([lng, lat]) => {
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });

    return [minLng, minLat, maxLng, maxLat];
  }

  geometryIntersectsPolygon(geometry, polygonCoords) {
    const lineCoords = geometry.coordinates;
    for (const coord of lineCoords) {
      if (this.pointInPolygon(coord, polygonCoords)) {
        return true;
      }
    }
    return this.lineIntersectsPolygon(lineCoords, polygonCoords);
  }

  pointInPolygon(point, polygon) {
    const [x, y] = point;
    let inside = false;
    
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      const [xi, yi] = polygon[i];
      const [xj, yj] = polygon[j];
      
      if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi)) {
        inside = !inside;
      }
    }
    
    return inside;
  }

  lineIntersectsPolygon(lineCoords, polygonCoords) {
    for (let i = 1; i < lineCoords.length; i++) {
      const a1 = lineCoords[i - 1];
      const a2 = lineCoords[i];
      for (let j = 1; j < polygonCoords.length; j++) {
        const b1 = polygonCoords[j - 1];
        const b2 = polygonCoords[j];
        if (this.segmentsIntersect(a1, a2, b1, b2)) {
          return true;
        }
      }
    }
    return false;
  }

  segmentsIntersect(p1, p2, p3, p4) {
    function orientation(a, b, c) {
      return (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1]);
    }

    function onSegment(a, b, c) {
      return (
        Math.min(a[0], c[0]) <= b[0] && b[0] <= Math.max(a[0], c[0]) &&
        Math.min(a[1], c[1]) <= b[1] && b[1] <= Math.max(a[1], c[1])
      );
    }

    const o1 = orientation(p1, p2, p3);
    const o2 = orientation(p1, p2, p4);
    const o3 = orientation(p3, p4, p1);
    const o4 = orientation(p3, p4, p2);

    if (o1 * o2 < 0 && o3 * o4 < 0) {
      return true;
    }
    if (o1 === 0 && onSegment(p1, p3, p2)) return true;
    if (o2 === 0 && onSegment(p1, p4, p2)) return true;
    if (o3 === 0 && onSegment(p3, p1, p4)) return true;
    if (o4 === 0 && onSegment(p3, p2, p4)) return true;
    return false;
  }

}

// Initialize global spatial index
window.spatialIndex = new SpatialIndex();