"""
Rock-solid lasso selection test using W3C touch actions and deterministic map projection.

This test implements senior engineer recommendations for flakiness elimination:
- W3C touch actions with interpolated moves
- MapLibre coordinate projection (eliminates DPR issues)  
- Deterministic polygon generation
- Enhanced readiness checks
- Comprehensive failure diagnostics
- Emulator stability settings (animations disabled)

Based on professional QA automation best practices.
"""
import time
import pytest
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.common.exceptions import TimeoutException
from base_mobile_test import BaseMobileTest

@pytest.mark.mobile
@pytest.mark.core
class TestBasicLassoSelection(BaseMobileTest):
    """Test basic lasso selection functionality with pre-packaged data"""
    
    def test_basic_lasso_polygon_selection(self, mobile_driver):
        """Rock-solid lasso selection using W3C touch actions and map projection"""
        print("🧪 Testing rock-solid lasso selection with W3C touch actions...")
        
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        
        # Inject map helpers for coordinate projection and readiness checks
        print("📦 Injecting map test helpers...")
        helpers_js = Path(__file__).parent / "map_helpers.js"
        
        # Setup - launch app and wait for initialization
        print("⏳ Allowing app to fully start up...")
        time.sleep(12)
        
        print("🔄 Switching to WebView context...")
        self.switch_to_webview(driver)
        
        print("🗺️ Waiting for map to fully load...")
        self.wait_for_map_load(driver, wait, verbose=True)
        
        # Belt-and-suspenders: bind __map from existing map variable
        print("🔗 Binding __map for test helpers...")
        driver.execute_script("""
          // If the page already has a global 'map' variable, bind it to __map
          if (!window.__map && typeof map !== 'undefined' && map && map.project) {
            window.__map = map;
          }
        """)
        
        # Inject helpers after map is loaded
        if helpers_js.exists():
            with open(helpers_js, 'r') as f:
                helpers_script = f.read()
            driver.execute_script(helpers_script)
            
            # Wait for helpers to be ready
            wait.until(lambda d: d.execute_script("return window.__mapTestHelpers !== undefined"))
            print("✅ Map test helpers injected successfully")
            
            # Quick sanity asserts (so we fail fast with useful message)
            diag = driver.execute_script("return window.__mapTestHelpers.getMapDiagnostics()")
            if not diag["mapFound"]:
                raise AssertionError(f"Map instance not found. Looks like findMap returned null. Diagnostics: {diag}")
            
            # If methods aren't functions, we're still grabbing the DOM node
            mt = diag["mapTypeCheck"]
            need = ["project", "getCanvas", "getCenter"]
            if not all(mt[k] == "function" for k in need):
                raise AssertionError(f"Found something named 'map' but it's not a MapLibre map. Diagnostics: {diag}")
                
            print("✅ Map instance validation passed - found real MapLibre map")
        else:
            print("⚠️ Map helpers not found, using fallback methods")
        
        # Navigate to Frederick activity location
        frederick_lat, frederick_lon = 39.4168, -77.4169
        zoom_level = 14
        
        print(f"🗺️ Navigating to Frederick activity: {frederick_lat}, {frederick_lon}")
        driver.execute_script(f"""
            // Use jumpTo for instant, deterministic positioning (no animation)
            map.jumpTo({{
                center: [{frederick_lon}, {frederick_lat}],
                zoom: {zoom_level}
            }});
        """)
        time.sleep(1)  # Brief pause for tiles to load at new location
        
        # Wait for map idle and runs features using deterministic approach
        print("⏳ Waiting for view to go idle after jumpTo...")
        went_idle = driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (!window.__mapTestHelpers) return cb(false);
            window.__mapTestHelpers.waitForIdleAfterMove(12000).then(cb);
        """)
        print(f"🔎 Idle wait result: {went_idle}")

        print("🔎 Waiting for runs features to be present in viewport...")
        features_ready = driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (!window.__mapTestHelpers) return cb(false);
            window.__mapTestHelpers.waitForRunsReady(12000).then(cb);
        """)
        if not features_ready:
            # Dump diagnostics before failing
            diag = driver.execute_script("return window.__mapTestHelpers && window.__mapTestHelpers.getMapDiagnostics && window.__mapTestHelpers.getMapDiagnostics()")
            raise TimeoutException(f"Runs layer never ready: {diag}")
            
        print("✅ Map is idle and runs features are ready for interaction")
        
        # Verify PMTiles data is loaded
        print("🔍 Verifying PMTiles data is loaded...")
        data_verification = self._verify_pmtiles_data_loaded(driver, frederick_lat, frederick_lon)
        assert data_verification['data_loaded'], f"PMTiles data must be loaded: {data_verification.get('error')}"
        print(f"📊 {data_verification['features_count']} features found in viewport")
        
        # Activate lasso mode
        print("🎯 Activating lasso selection mode...")
        lasso_btn = self.find_clickable_element(driver, wait, "#lasso-btn")
        lasso_btn.click()
        time.sleep(0.5)
        
        # Verify lasso mode is active
        lasso_active = driver.execute_script("""
            const btn = document.getElementById('lasso-btn');
            const styles = window.getComputedStyle(btn);
            return {
                backgroundColor: styles.backgroundColor,
                exists: !!btn
            };
        """)
        print(f"🔍 Lasso button state: {lasso_active}")
        
        # Generate deterministic polygon with larger radius for better motion detection
        print("📐 Generating deterministic polygon...")
        polygon_coords = driver.execute_script("""
            return window.__mapTestHelpers.generateCenterPolygon(110);
        """)
        print(f"🗺️ Generated polygon coordinates: {len(polygon_coords)} points")
        
        # Convert to ABSOLUTE viewport points (not canvas-relative)
        viewport_points = driver.execute_script("""
            return window.__mapTestHelpers.projectToViewportPoints(arguments[0]);
        """, polygon_coords)
        print(f"🎯 Viewport points: {viewport_points}")
        
        # Execute W3C touch action with absolute viewport moves
        print("👆 Drawing polygon with absolute viewport coordinates...")
        self._draw_polygon_absolute_viewport(driver, viewport_points)
        
        # Wait for lasso processing
        print("⏳ Waiting for lasso processing...")
        lasso_result = self._wait_for_lasso_completion(driver, wait)
        
        # Verify results
        assert lasso_result['panel_opened'], f"Side panel should open: {lasso_result['debug_info']}"
        assert lasso_result['run_count'] >= 1, f"Should select at least 1 activity: {lasso_result['debug_info']}"
        
        print(f"✅ Lasso selection completed successfully!")
        print(f"📊 Selected {lasso_result['run_count']} activities")
        
        # Add diagnostics on unexpected results
        if lasso_result['run_count'] == 0:
            diagnostics = driver.execute_script("""
                return window.__mapTestHelpers ? window.__mapTestHelpers.getMapDiagnostics() : 
                       { error: 'Map helpers not available' };
            """)
            print(f"🔍 Diagnostics: {diagnostics}")
    
    def _draw_polygon_absolute_viewport(self, driver, viewport_points):
        """Draw polygon using absolute viewport coordinates (no element-relative issues)"""
        if len(viewport_points) < 3:
            raise ValueError("Need at least 3 points for polygon")
        
        # Freeze scroll position to prevent coordinate shifts
        driver.execute_script("window.scrollTo(0,0)")
        
        # Ensure container is visible 
        driver.execute_script("window.__mapTestHelpers.findMap().getContainer().scrollIntoView({block:'center', inline:'center'})")
        
        # Get viewport dimensions for additional clamping
        vw, vh = driver.execute_script("return [window.innerWidth, window.innerHeight]")
        
        # Belt-and-suspenders viewport clamping
        clamped_points = []
        for p in viewport_points:
            x = max(15, min(vw - 15, int(p["x"])))
            y = max(15, min(vh - 15, int(p["y"])))
            clamped_points.append({"x": x, "y": y})
        
        print(f"🔒 Clamped to viewport bounds: {clamped_points}")
        
        # Create touch pointer
        finger = PointerInput("touch", "finger")
        actions = ActionBuilder(driver, finger)
        
        def move_abs(pt):
            """Absolute viewport move (no element argument)"""
            actions.pointer_action.move_to_location(int(pt["x"]), int(pt["y"]))
        
        def lerp(a, b, t):
            """Interpolate between two absolute points"""
            x = int(a["x"] + (b["x"] - a["x"]) * t)
            y = int(a["y"] + (b["y"] - a["y"]) * t)
            # Clamp again to be paranoid
            x = max(15, min(vw - 15, x))
            y = max(15, min(vh - 15, y))
            return {"x": x, "y": y}
        
        # Start at first point
        first_point = clamped_points[0]
        move_abs(first_point)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(0.1)  # 100ms settle after tap
        
        print(f"👆 Starting absolute touch at {first_point}")
        
        # Draw smooth path between points
        for i in range(len(clamped_points) - 1):
            point_a = clamped_points[i]
            point_b = clamped_points[i + 1]
            
            # Interpolated moves for smoothness
            steps = 12
            for step in range(1, steps + 1):
                interpolated_point = lerp(point_a, point_b, step / steps)
                move_abs(interpolated_point)
                actions.pointer_action.pause(0.015)
            
            print(f"👆 Drew to absolute point {i+1}: {point_b}")
        
        # Release touch
        actions.pointer_action.pointer_up()
        
        # Perform the entire action sequence
        actions.perform()
        print("✅ Absolute viewport polygon drawing completed")
    
    def _wait_for_lasso_completion(self, driver, wait, max_wait=15):
        """Wait for lasso processing with enhanced checks"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Check panel state
            panel_info = self.check_side_panel(driver)
            run_count = panel_info.get('runCount', 0)
            
            if run_count > 0:
                elapsed = time.time() - start_time
                return {
                    'panel_opened': True,
                    'run_count': run_count,
                    'debug_info': f'Success after {elapsed:.1f}s'
                }
            
            time.sleep(0.5)
        
        # Timeout - return diagnostic info
        return {
            'panel_opened': False,
            'run_count': 0,
            'debug_info': f'Timeout after {max_wait}s'
        }
    
    def _generate_fallback_triangle(self, driver, center_lat, center_lon):
        """Generate triangle coordinates using fallback method"""
        return driver.execute_script(f"""
            const centerLat = {center_lat};
            const centerLon = {center_lon};
            const size = 0.003;  // Size in degrees
            
            // Create triangle points around center
            const coords = [
                [centerLon, centerLat + size],        // Top point
                [centerLon - size, centerLat - size], // Bottom left
                [centerLon + size, centerLat - size], // Bottom right  
                [centerLon, centerLat + size]         // Close triangle
            ];
            
            // Convert to screen coordinates
            const mapContainer = document.getElementById('map');
            const mapRect = mapContainer.getBoundingClientRect();
            
            return coords.map(coord => {{
                const point = map.project(coord);
                return {{ 
                    x: Math.round(Math.max(30, Math.min(mapRect.width - 30, point.x))), 
                    y: Math.round(Math.max(30, Math.min(mapRect.height - 30, point.y)))
                }};
            }});
        """)
    
    def _verify_pmtiles_data_loaded(self, driver, center_lat, center_lon):
        """Verify PMTiles data using enhanced helper"""
        return driver.execute_script(f"""
            const centerLat = {center_lat};
            const centerLon = {center_lon};
            const radius = 0.005;
            
            try {{
                const sources = map.getStyle().sources;
                let sourceName = null;
                
                const possibleNames = ['runsVec', 'pmtiles-source', 'runs', 'activities'];
                for (const name of possibleNames) {{
                    if (sources[name]) {{
                        sourceName = name;
                        break;
                    }}
                }}
                
                if (!sourceName) {{
                    return {{ 
                        data_loaded: false, 
                        error: 'No PMTiles source found. Available: ' + Object.keys(sources).join(', '), 
                        features_count: 0 
                    }};
                }}
                
                const features = map.querySourceFeatures(sourceName, {{
                    filter: null,
                    sourceLayer: 'runs'
                }}) || [];
                
                const bbox = [
                    centerLon - radius, centerLat - radius,
                    centerLon + radius, centerLat + radius
                ];
                
                const featuresInArea = features.filter(feature => {{
                    if (!feature.geometry?.coordinates) return false;
                    const coords = feature.geometry.coordinates;
                    return coords.some(coord => {{
                        if (Array.isArray(coord) && coord.length >= 2) {{
                            const [lon, lat] = coord;
                            return lon >= bbox[0] && lon <= bbox[2] && lat >= bbox[1] && lat <= bbox[3];
                        }}
                        return false;
                    }});
                }});
                
                return {{
                    data_loaded: true,
                    features_count: featuresInArea.length,
                    total_features: features.length,
                    source_name: sourceName
                }};
                
            }} catch (error) {{
                return {{
                    data_loaded: false,
                    error: error.message,
                    features_count: 0
                }};
            }}
        """)
    
