// Mobile spatial index and data management
class SpatialIndex {
  constructor() {
    this.loaded = false;
    this.runsData = null;
    this.spatialIndex = null;
    this.userRuns = [];
    this.nextId = 1;
  }

  async loadData() {
    try {
      console.log('Loading mobile spatial data...');
      
      // Load bundled data only
      const runsResponse = await fetch('data/runs.json');
      if (!runsResponse.ok) {
        throw new Error(`Failed to load runs: ${runsResponse.status}`);
      }
      this.runsData = await runsResponse.json();
      
      const indexResponse = await fetch('data/spatial_index.json');
      if (!indexResponse.ok) {
        throw new Error(`Failed to load spatial index: ${indexResponse.status}`);
      }
      this.spatialIndex = await indexResponse.json();

      this.nextId = Math.max(0, ...Object.keys(this.runsData).map(id => parseInt(id))) + 1;

      this.loadUserRuns();

      this.loaded = true;
      console.log(`Loaded ${Object.keys(this.runsData).length} runs with spatial index`);
      
      // Show user feedback
      if (window.showStatusForDebug) {
        window.showStatusForDebug(`Loaded ${Object.keys(this.runsData).length} runs`, 1500);
      }
      
    } catch (error) {
      console.error('Failed to load spatial data:', error);
      throw error;
    }
  }

  loadUserRuns() {
    const stored = localStorage.getItem('userRuns');
    if (!stored) return;
    try {
      const arr = JSON.parse(stored);
      arr.forEach(run => {
        const id = run.id.toString();
        this.runsData[id] = { geoms: run.geoms, bbox: run.bbox, metadata: run.metadata };
        this.spatialIndex.push({ id: parseInt(id), bbox: run.bbox });
        this.userRuns.push(run);
        const num = parseInt(id);
        if (num >= this.nextId) this.nextId = num + 1;
      });
      console.log(`Loaded ${arr.length} user runs from storage`);
    } catch (e) {
      console.error('Failed to load stored runs', e);
    }
  }

  saveUserRuns() {
    try {
      localStorage.setItem('userRuns', JSON.stringify(this.userRuns));
    } catch (e) {
      console.error('Failed to save user runs', e);
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

  addRun(coords, metadata) {
    const id = this.nextId++;
    const bbox = this.getPolygonBbox(coords);
    const geoms = {
      high: { type: 'LineString', coordinates: this.simplify(coords, 0.00005) },
      mid: { type: 'LineString', coordinates: this.simplify(coords, 0.0003) },
      low: { type: 'LineString', coordinates: this.simplify(coords, 0.0009) }
    };
    this.runsData[id.toString()] = { geoms, bbox, metadata };
    this.spatialIndex.push({ id, bbox });
    const run = { id: id.toString(), geoms, bbox, metadata };
    this.userRuns.push(run);
    this.saveUserRuns();
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
        const runId = indexEntry.id.toString();
        const runData = this.runsData[runId];
        
        if (runData && runData.geoms) {
          // Choose appropriate zoom level with fallback
          const zoomLevel = this.getZoomLevel(zoom);
          let geom = runData.geoms[zoomLevel];

          // Fallback to other zoom levels if current one is invalid/empty
          if (!geom || !geom.coordinates || geom.coordinates.length === 0) {
            geom = runData.geoms['mid'] || runData.geoms['low'] || runData.geoms['high'];
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

  filterRunsByIds(runIds, minLat, minLng, maxLat, maxLng, zoom) {
    if (!this.loaded) {
      return { type: 'FeatureCollection', features: [] };
    }

    const features = [];
    const bbox = [minLng, minLat, maxLng, maxLat];
    
    for (const runId of runIds) {
      const runData = this.runsData[runId.toString()];
      
      if (runData && runData.geoms) {
        // Check if run bbox intersects with bounds
        if (this.bboxIntersects(runData.bbox, bbox)) {
          const zoomLevel = this.getZoomLevel(zoom);
          let geom = runData.geoms[zoomLevel];
          
          // Fallback to other zoom levels if current one is invalid/empty
          if (!geom || !geom.coordinates || geom.coordinates.length === 0) {
            geom = runData.geoms['mid'] || runData.geoms['low'] || runData.geoms['high'];
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

  getRunsInPolygon(polygonCoords) {
    if (!this.loaded) {
      return [];
    }

    const runs = [];
    
    // Get polygon bounding box for initial filtering
    const polyBbox = this.getPolygonBbox(polygonCoords);
    
    for (const indexEntry of this.spatialIndex) {
      const runBbox = indexEntry.bbox;
      
      // First check bbox intersection for performance
      if (this.bboxIntersects(runBbox, polyBbox)) {
        const runId = indexEntry.id.toString();
        const runData = this.runsData[runId];
        
        if (runData && runData.geoms) {
          // More precise check: see if any part of the run intersects the polygon
          let intersects = false;
          
          // Check if bounding box center is in polygon
          const runCenter = [
            (runBbox[0] + runBbox[2]) / 2,
            (runBbox[1] + runBbox[3]) / 2
          ];
          
          if (this.pointInPolygon(runCenter, polygonCoords)) {
            intersects = true;
          } else {
            // Also check if any corner of the bounding box is in the polygon
            const corners = [
              [runBbox[0], runBbox[1]], // bottom-left
              [runBbox[2], runBbox[1]], // bottom-right
              [runBbox[2], runBbox[3]], // top-right
              [runBbox[0], runBbox[3]]  // top-left
            ];
            
            for (const corner of corners) {
              if (this.pointInPolygon(corner, polygonCoords)) {
                intersects = true;
                break;
              }
            }
            
            // If still no intersection, check if polygon intersects with run geometry
            if (!intersects) {
              const geom = runData.geoms.high || runData.geoms.mid || runData.geoms.low;
              if (geom && geom.coordinates) {
                // Check if any coordinate point is in the polygon
                for (const coord of geom.coordinates) {
                  if (this.pointInPolygon(coord, polygonCoords)) {
                    intersects = true;
                    break;
                  }
                }
              }
            }
          }
          
          if (intersects) {
            runs.push({
              id: parseInt(runId),
              metadata: runData.metadata,
              bbox: runData.bbox
            });
          }
        }
      }
    }

    return runs;
  }

  getZoomLevel(zoom) {
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

}

// Initialize global spatial index
window.spatialIndex = new SpatialIndex();