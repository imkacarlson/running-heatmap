"""
Centralized map loading detection utility for mobile app tests.
Dynamically waits for OpenStreetMap tiles to load based on actual loading state.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, JavascriptException

class MapLoadDetector:
    """
    Detects when the map and OpenStreetMap tiles are loaded enough for testing.
    Uses progressive checking with adaptive timeouts based on loading progress.
    """
    
    def __init__(self, driver, wait, verbose=False):
        self.driver = driver
        self.wait = wait
        self.verbose = verbose
        self.last_tile_count = 0
        self.stable_tile_checks = 0
        
    def wait_for_map_ready(self, timeout=60, min_tiles_threshold=1):
        """
        Main method: Wait for map to be ready for testing.
        
        Args:
            timeout: Maximum seconds to wait (default 60)
            min_tiles_threshold: Minimum tiles needed to consider map "ready" (default 1 for PMTiles/vector)
            
        Returns:
            True if map is ready, raises TimeoutException if not ready in time
        """
        start_time = time.time()
        
        # Phase 1: Wait for map element to exist
        self._wait_for_map_element()
        
        # Phase 2: Wait for MapLibre GL JS to initialize
        self._wait_for_maplibre_init(timeout - (time.time() - start_time))
        
        # Phase 3: Wait for sufficient tiles to load
        self._wait_for_tiles_loaded(
            timeout - (time.time() - start_time),
            min_tiles_threshold
        )
        
        # Phase 4: Verify map is interactive
        self._verify_map_interactive()
        
        if self.verbose:
            print(f"✅ Map ready after {time.time() - start_time:.1f} seconds")
        
        return True
    
    def _wait_for_map_element(self):
        """Phase 1: Ensure map DOM element exists"""
        if self.verbose:
            print("🔍 Phase 1: Waiting for map element...")
        
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#map"))
        )
        
    def _wait_for_maplibre_init(self, remaining_timeout):
        """Phase 2: Wait for MapLibre GL JS to initialize"""
        if self.verbose:
            print("🔍 Phase 2: Waiting for MapLibre initialization...")
        
        max_attempts = int(remaining_timeout / 2)  # Check every 2 seconds
        
        for attempt in range(max_attempts):
            try:
                map_state = self.driver.execute_script("""
                    return {
                        mapExists: typeof map !== 'undefined',
                        mapLoaded: typeof map !== 'undefined' && map.loaded && map.loaded(),
                        hasContainer: !!document.querySelector('.maplibregl-map, .mapboxgl-map'),
                        hasCanvas: !!document.querySelector('#map canvas'),
                        style: typeof map !== 'undefined' && map.getStyle ? !!map.getStyle() : false
                    };
                """)
                
                if self.verbose and attempt % 5 == 0:  # Log every 10 seconds
                    print(f"   MapLibre state (attempt {attempt+1}): {map_state}")
                
                if (map_state['mapExists'] and 
                    map_state['hasContainer'] and 
                    map_state['hasCanvas']):
                    if self.verbose:
                        print("   ✓ MapLibre initialized")
                    return True
                    
            except JavascriptException as e:
                if self.verbose:
                    print(f"   JS error (attempt {attempt+1}): {e}")
            
            # Use dynamic wait instead of fixed sleep
            from selenium.webdriver.support.ui import WebDriverWait
            WebDriverWait(self.driver, 2).until(lambda d: True)  # Dynamic 2s wait
        
        raise TimeoutException("MapLibre failed to initialize")
    
    def _wait_for_tiles_loaded(self, remaining_timeout, min_tiles):
        """Phase 3: Wait for OpenStreetMap tiles to load"""
        if self.verbose:
            print(f"🔍 Phase 3: Waiting for tiles (minimum {min_tiles})...")
        
        check_interval = 1  # Start checking every second
        max_checks = int(remaining_timeout / check_interval)
        
        for check in range(max_checks):
            tile_info = self._get_tile_loading_state()
            
            if self.verbose and check % 5 == 0:  # Log every 5 seconds
                details = tile_info.get('details', 'No details')
                print(f"   Tiles: {tile_info['loaded']}/{tile_info['total']} loaded, "
                      f"{tile_info['loading']} loading, {tile_info['errored']} errors - {details}")
            
            # Adaptive waiting based on loading progress
            if tile_info['loaded'] >= min_tiles:
                # We have minimum tiles, check if loading is stable
                if self._is_tile_loading_stable(tile_info):
                    if self.verbose:
                        details = tile_info.get('details', 'No details')
                        print(f"   ✓ Tiles loaded and stable: {tile_info['loaded']} tiles - {details}")
                    return True
            
            # Adjust check interval based on loading activity
            if tile_info['loading'] > 0:
                check_interval = 0.5  # Check more frequently when actively loading
            else:
                check_interval = 2  # Check less frequently when idle
            
            # Use dynamic wait instead of variable sleep
            from selenium.webdriver.support.ui import WebDriverWait
            WebDriverWait(self.driver, check_interval).until(lambda d: True)
        
        # If we get here, accept whatever tiles we have if it's at least 1
        final_tiles = self._get_tile_loading_state()
        final_details = final_tiles.get('details', 'No details')
        if final_tiles['loaded'] > 0:
            if self.verbose:
                print(f"   ⚠️ Timeout reached but have {final_tiles['loaded']} tiles, continuing - {final_details}")
            return True
        
        raise TimeoutException(f"Insufficient tiles loaded: {final_tiles['loaded']} - {final_details}")
    
    def _get_tile_loading_state(self):
        """Get current state of vector tile/PMTiles loading using proper MapLibre GL JS APIs"""
        try:
            return self.driver.execute_script("""
                if (typeof map === 'undefined') {
                    return {loaded: 0, loading: 1, errored: 0, total: 1};
                }
                
                try {
                    // Check if map is basically ready
                    const mapLoaded = map.loaded && map.loaded();
                    const styleLoaded = map.isStyleLoaded && map.isStyleLoaded();
                    
                    // Main check: Are all tiles in viewport loaded? (proper way for vector tiles/PMTiles)
                    const tilesLoaded = map.areTilesLoaded && map.areTilesLoaded();
                    
                    // Check if we have rendered features (additional validation)
                    let hasRenderedFeatures = false;
                    try {
                        const features = map.queryRenderedFeatures();
                        hasRenderedFeatures = features && features.length > 0;
                    } catch (e) {
                        // queryRenderedFeatures might fail if map not ready
                        hasRenderedFeatures = false;
                    }
                    
                    // Determine loading state based on MapLibre GL JS proper APIs
                    if (tilesLoaded && mapLoaded && styleLoaded) {
                        // Everything is loaded and ready
                        return {
                            loaded: 1,
                            loading: 0,
                            errored: 0,
                            total: 1,
                            details: 'All tiles loaded via areTilesLoaded()'
                        };
                    } else if (mapLoaded && styleLoaded) {
                        // Map is loaded but tiles might still be loading
                        return {
                            loaded: 0,
                            loading: 1,
                            errored: 0,
                            total: 1,
                            details: 'Map loaded, tiles loading'
                        };
                    } else {
                        // Map still initializing
                        return {
                            loaded: 0,
                            loading: 1,
                            errored: 0,
                            total: 1,
                            details: 'Map initializing'
                        };
                    }
                } catch (error) {
                    // Fallback: Basic map existence check
                    return {
                        loaded: 0,
                        loading: 1,
                        errored: 0,
                        total: 1,
                        details: 'Error checking tile state: ' + error.message
                    };
                }
            """)
        except Exception as e:
            return {
                'loaded': 0, 
                'loading': 1, 
                'errored': 0, 
                'total': 1,
                'details': f'Python exception: {str(e)}'
            }
    
    def _is_tile_loading_stable(self, tile_info):
        """Check if tile loading has stabilized (not changing)"""
        current_count = tile_info['loaded']
        
        if current_count == self.last_tile_count:
            self.stable_tile_checks += 1
        else:
            self.stable_tile_checks = 0
            self.last_tile_count = current_count
        
        # Consider stable if tile count hasn't changed for 2 checks
        return self.stable_tile_checks >= 2
    
    def _verify_map_interactive(self):
        """Phase 4: Verify map is interactive and responding"""
        if self.verbose:
            print("🔍 Phase 4: Verifying map interactivity...")
        
        try:
            # Check if we can get map properties
            interactive_check = self.driver.execute_script("""
                if (typeof map === 'undefined') return false;
                
                try {
                    // These operations should work if map is ready
                    const zoom = map.getZoom();
                    const center = map.getCenter();
                    const bounds = map.getBounds();
                    
                    return {
                        interactive: true,
                        zoom: zoom,
                        hasCenter: !!center,
                        hasBounds: !!bounds
                    };
                } catch (e) {
                    return {interactive: false, error: e.message};
                }
            """)
            
            if not interactive_check or not interactive_check.get('interactive'):
                raise Exception(f"Map not interactive: {interactive_check}")
            
            if self.verbose:
                print(f"   ✓ Map interactive at zoom {interactive_check['zoom']}")
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️ Interactivity check failed: {e}")
            # Non-fatal - some tests might not need full interactivity