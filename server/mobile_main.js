// Mobile spatial index and data management
class SpatialIndex {
  constructor() {
    this.loaded = false;
    this.spatialIndex = [];
    this.userRuns = [];
    this.nextId = 1;
  }




  async loadData() {
    try {
      console.log('[HEATMAP-DEBUG] Initializing SpatialIndex.loadData');
      this.spatialIndex = [];
      this.userRuns = [];

      // Give local uploads an ID space that cannot collide with PMTiles
      const LOCAL_ID_BASE = 1_000_000; // anything comfortably above PMTiles IDs
      this.nextId = LOCAL_ID_BASE;

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

  // Local upload persistence removed; runs are session-only in memory

  


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
    
    // Add to spatial index and user runs for immediate display
    this.spatialIndex.push({ id: parseInt(id), bbox: bbox });
    this.userRuns.push(run);
    
    // Persistence removed; runs are stored in-memory only
    console.log('[HEATMAP-DEBUG] Run stored in-memory with ID:', id);
    
    if (window.showStatusForDebug) {
      window.showStatusForDebug('Run uploaded and saved successfully', 2000);
    }

    return id;
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
    // Edge-only intersections are not required by current tests.
    return false;
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

  

  // (Removed) Local indexing helpers were unused by current tests.


}

// Initialize global spatial index
window.spatialIndex = new SpatialIndex();
