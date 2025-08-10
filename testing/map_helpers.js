/**
 * Map Testing Helper Functions
 * 
 * This JavaScript module provides reliable coordinate projection and readiness
 * checking for MapLibre-based apps in automated testing.
 * 
 * Usage: Inject this script into the WebView context before running map tests.
 */
(() => {
  // Duck type check to ensure we only accept real MapLibre instances
  const looksLikeMap = (m) =>
    m && typeof m.project === 'function' &&
    typeof m.getCanvas === 'function' &&
    typeof m.getCenter === 'function';

  // Find the map instance - refuse DOM elements with proper type checking
  const findMap = () => {
    // Prefer the explicit hook you just exported
    if (looksLikeMap(window.__map)) return window.__map;
    // Other explicit homes you might use
    if (looksLikeMap(window.MAP)) return window.MAP;
    if (looksLikeMap(window.heatmapApp?.map)) return window.heatmapApp.map;
    // Last resort: only accept window.map if it quacks like MapLibre (avoid #map element)
    if (looksLikeMap(window.map)) return window.map;
    return null;
  };

  // Get the map canvas element
  const getCanvas = () => {
    const map = findMap();
    if (!map) return null;
    
    // Try different methods to get the canvas
    return map.getCanvas ? map.getCanvas() : 
           document.querySelector('canvas') ||
           document.querySelector('.maplibregl-canvas') ||
           document.querySelector('.mapboxgl-canvas');
  };

  /**
   * Convert longitude/latitude coordinates to canvas-relative CSS pixel offsets
   * This eliminates device pixel ratio and coordinate calculation issues
   * 
   * @param {Array<[number, number]>} lonlatArray - Array of [longitude, latitude] pairs
   * @returns {Array<{x: number, y: number}>} - Array of {x, y} CSS pixel offsets
   */
  function projectToCanvasOffsets(lonlatArray) {
    const map = findMap();
    const canvas = getCanvas();
    
    if (!map || !canvas) {
      throw new Error('Map or canvas not found for projection');
    }
    
    const rect = canvas.getBoundingClientRect();
    
    return lonlatArray.map(([lon, lat]) => {
      // MapLibre's project() returns CSS pixels relative to map container
      const point = map.project([lon, lat]);
      
      // Convert to canvas-relative coordinates with bounds checking
      const x = Math.round(point.x - rect.left);
      const y = Math.round(point.y - rect.top);
      
      // Ensure coordinates are within canvas bounds (with 10px margin)
      const margin = 10;
      return { 
        x: Math.max(margin, Math.min(rect.width - margin, x)), 
        y: Math.max(margin, Math.min(rect.height - margin, y))
      };
    });
  }

  /**
   * Check if the map is ready for interaction
   * Combines multiple readiness indicators for reliability
   * 
   * @returns {boolean} - True if map is ready for interaction
   */
  function isMapReady() {
    const map = findMap();
    if (!map) return false;

    try {
      // Basic loaded check
      const loaded = map.loaded && map.loaded();
      if (!loaded) return false;

      // Check if map is not currently moving/animating
      const notMoving = !map.isMoving || !map.isMoving();
      if (!notMoving) return false;

      // Check if tiles are loaded (if method exists)
      const tilesLoaded = !map.areTilesLoaded || map.areTilesLoaded();
      if (!tilesLoaded) return false;

      // Check if canvas exists and has reasonable dimensions
      const canvas = getCanvas();
      if (!canvas) return false;
      
      const rect = canvas.getBoundingClientRect();
      if (rect.width < 100 || rect.height < 100) return false;

      return true;
    } catch (e) {
      console.warn('Map readiness check failed:', e);
      return false;
    }
  }

  /**
   * Wait for map to be ready using requestAnimationFrame
   * This ensures the rendering pipeline has settled
   * 
   * @returns {Promise<void>}
   */
  function waitForMapStable() {
    return new Promise(resolve => {
      // Double RAF to ensure rendering is complete
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          resolve();
        });
      });
    });
  }

  /**
   * Generate a deterministic polygon around the map center
   * This creates a triangle that's always visible at current zoom
   * 
   * @param {number} radiusPx - Radius in CSS pixels (default: 80)
   * @returns {Array<[number, number]>} - Array of [longitude, latitude] coordinates
   */
  function generateCenterPolygon(radiusPx = 80) {
    const map = findMap();
    if (!map) throw new Error('Map not found for polygon generation');

    const center = map.getCenter(); // {lng, lat}
    const centerPx = map.project([center.lng, center.lat]);

    // Helper to create point at angle
    function polarPoint(radius, angleDeg) {
      const rad = angleDeg * Math.PI / 180;
      return { 
        x: centerPx.x + radius * Math.cos(rad), 
        y: centerPx.y + radius * Math.sin(rad) 
      };
    }

    // Create triangle points (closed polygon)
    const pixelPoints = [
      polarPoint(radiusPx, -90),  // Top
      polarPoint(radiusPx, 150),  // Bottom left  
      polarPoint(radiusPx, 30),   // Bottom right
      polarPoint(radiusPx, -90)   // Close the polygon
    ];

    // Convert back to lon/lat
    return pixelPoints.map(point => {
      const lngLat = map.unproject(point);
      return [lngLat.lng, lngLat.lat];
    });
  }

  /**
   * Wait for map to be idle after navigation
   * Resolves when map fires 'idle' or RAF polling confirms not moving + tiles loaded
   * 
   * @param {number} timeoutMs - Timeout in milliseconds (default: 15000)
   * @returns {Promise<boolean>} - True if map became idle, false if timeout
   */
  async function waitForIdleAfterMove(timeoutMs = 15000) {
    const map = findMap();
    if (!map) throw new Error('Map not found');

    return new Promise((resolve, reject) => {
      let done = false;
      const start = performance.now();

      const finish = ok => { 
        if (!done) { 
          done = true; 
          resolve(!!ok); 
        } 
      };

      const idleHandler = () => finish(true);

      // If the map is already idle when we attach the listener, idle may never fire.
      // So we also poll via RAF.
      const poll = () => {
        if (done) return;
        try {
          const loaded = (map.isStyleLoaded?.() ?? map.loaded?.()) || false;
          const moving = map.isMoving?.() || false;
          const tiles = (map.areTilesLoaded?.() ?? true);

          if (loaded && !moving && tiles) return finish(true);
        } catch (_) { /* ignore */ }

        if (performance.now() - start > timeoutMs) return finish(false);
        requestAnimationFrame(poll);
      };

      map.once?.('idle', idleHandler);
      requestAnimationFrame(() => requestAnimationFrame(poll));

      // Last-resort timeout so we never hang forever
      setTimeout(() => finish(false), timeoutMs + 250);
    });
  }

  /**
   * Wait for runs features to be present in viewport
   * This is the most honest "ready to draw & query" signal
   * 
   * @param {number} timeoutMs - Timeout in milliseconds (default: 15000)
   * @returns {Promise<boolean>} - True if features found, false if timeout
   */
  async function waitForRunsReady(timeoutMs = 15000) {
    const map = findMap();
    if (!map) throw new Error('Map not found');

    const start = performance.now();
    return new Promise(resolve => {
      const tick = () => {
        try {
          // First try source-based check
          const style = map.getStyle && map.getStyle();
          if (style?.sources) {
            const srcNames = Object.keys(style.sources);
            for (const name of srcNames) {
              try {
                const feats = map.querySourceFeatures(name, { sourceLayer: 'runs' }) || [];
                if (feats.length) return resolve(true);
              } catch (_) { /* ignore */ }
            }
          }
          // Fallback: rendered features on any layer that looks like runs
          const layers = style?.layers || [];
          const runLayerIds = layers
            .filter(l => /run|activity|tracks?/i.test(l.id))
            .map(l => l.id);

          const rendered = map.queryRenderedFeatures(undefined, runLayerIds.length ? { layers: runLayerIds } : undefined);
          if (rendered && rendered.length) return resolve(true);
        } catch (_) { /* ignore */ }

        if (performance.now() - start > timeoutMs) return resolve(false);
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }

  /**
   * Get diagnostic information about the current map state
   * Useful for debugging test failures
   * 
   * @returns {Object} - Diagnostic information
   */
  function getMapDiagnostics() {
    const map = findMap();
    const canvas = getCanvas();

    return {
      timestamp: new Date().toISOString(),
      mapFound: !!map,
      mapTypeCheck: map ? {
        project: typeof map.project,
        getCanvas: typeof map.getCanvas,
        getCenter: typeof map.getCenter,
        loaded: typeof map.loaded,
        isStyleLoaded: typeof map.isStyleLoaded,
        areTilesLoaded: typeof map.areTilesLoaded,
        isMoving: typeof map.isMoving
      } : null,
      canvasFound: !!canvas,
      canvasSelector: canvas ? canvas.tagName.toLowerCase() + (canvas.className ? '.' + canvas.className.split(' ').join('.') : '') : null,
      windowSize: { 
        width: window.innerWidth, 
        height: window.innerHeight 
      },
      devicePixelRatio: window.devicePixelRatio,
      canvasSize: canvas ? {
        width: canvas.width,
        height: canvas.height,
        boundingWidth: canvas.getBoundingClientRect().width,
        boundingHeight: canvas.getBoundingClientRect().height
      } : null,
      mapState: map ? {
        loaded: map.loaded ? map.loaded() : null,
        moving: map.isMoving ? map.isMoving() : null,
        tilesLoaded: map.areTilesLoaded ? map.areTilesLoaded() : null,
        center: map.getCenter ? map.getCenter() : null,
        zoom: map.getZoom ? map.getZoom() : null
      } : null,
      domElements: {
        panelOpen: !!document.querySelector('#side-panel.open, .side-panel.open'),
        runCards: document.querySelectorAll('#panel-content .run-card, .run-card').length,
        lassoButton: !!document.querySelector('#lasso-btn, .lasso-btn, [data-testid="lasso-btn"]')
      }
    };
  }

  /**
   * Convert longitude/latitude coordinates to absolute viewport coordinates
   * This eliminates Android WebView element-relative coordinate issues
   * 
   * @param {Array<[number, number]>} lonlatArray - Array of [longitude, latitude] pairs
   * @returns {Array<{x: number, y: number}>} - Array of {x, y} absolute viewport coordinates
   */
  function projectToViewportPoints(lonlatArray) {
    const map = findMap();
    if (!map) throw new Error('Map not found');
    const container = map.getContainer(); // not the canvas
    const crect = container.getBoundingClientRect();

    return lonlatArray.map(([lon, lat]) => {
      const p = map.project([lon, lat]);      // container-relative CSS px
      // Convert to viewport coords
      let x = Math.round(crect.left + p.x);
      let y = Math.round(crect.top  + p.y);

      // Clamp to viewport to avoid bars/edges
      const margin = 15;
      const vw = window.innerWidth, vh = window.innerHeight;
      x = Math.max(margin, Math.min(vw - margin, x));
      y = Math.max(margin, Math.min(vh - margin, y));
      return { x, y };
    });
  }

  // Expose the testing interface
  window.__mapTestHelpers = {
    // Core functionality
    projectToCanvasOffsets,
    projectToViewportPoints,
    isMapReady,
    waitForMapStable,
    generateCenterPolygon,
    getMapDiagnostics,
    
    // New deterministic readiness helpers
    waitForIdleAfterMove,
    waitForRunsReady,
    
    // Direct access to internals for advanced use
    findMap,
    getCanvas,
    
    // Convenience selectors (adjust these based on your app)
    selectors: {
      canvas: 'canvas',
      lassoButton: '#lasso-btn',
      sidePanel: '#side-panel',
      runCards: '#panel-content .run-card'
    }
  };

  // Also expose a simple version for backward compatibility
  window.__itest = {
    canvasSelector: 'canvas',
    projectToCanvasOffsets,
    isReady: isMapReady
  };

  console.log('Map test helpers loaded successfully');
})();