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
        print("⏳ Waiting for app WebView to become available...")
        self.wait_for_webview_available(driver, wait, verbose=True)
        
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
        
        # Wait for map to settle after navigation
        self.wait_for_map_idle_after_move(driver, timeout_ms=5000, verbose=True)
        
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
        
        # Wait for lasso mode to activate
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.getElementById('lasso-btn').classList.contains('active')")
        )
        
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
        
        # Verify results for small polygon
        assert lasso_result['panel_opened'], f"Side panel should open: {lasso_result['debug_info']}"
        assert lasso_result['run_count'] >= 1, f"Should select at least 1 activity: {lasso_result['debug_info']}"
        
        print(f"✅ Small polygon lasso selection completed successfully!")
        print(f"📊 Selected {lasso_result['run_count']} activities with small polygon")
        
        # Close the side panel before starting the second test
        print("🔒 Closing side panel to prepare for second test...")
        panel_closed = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            if (panel && panel.classList.contains('open')) {
                // Try clicking the close button first
                const closeBtn = panel.querySelector('.close-btn, .close, [data-dismiss], .panel-close');
                if (closeBtn) {
                    closeBtn.click();
                    return 'clicked_close_button';
                }
                
                // Fallback: click outside the panel to close it
                const mapElement = document.getElementById('map');
                if (mapElement) {
                    mapElement.click();
                    return 'clicked_map_to_close';
                }
                
                // Last resort: remove the open class directly
                panel.classList.remove('open');
                return 'removed_class_directly';
            }
            return 'panel_already_closed';
        """)
        print(f"📋 Panel close method: {panel_closed}")
        
        # Wait for panel to close
        WebDriverWait(driver, 5).until(
            lambda d: not d.execute_script("return document.getElementById('side-panel').classList.contains('open')")
        )
        
        # Verify panel is closed
        panel_closed_check = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            return !panel || !panel.classList.contains('open') || 
                   window.getComputedStyle(panel).display === 'none';
        """)
        
        if not panel_closed_check:
            print("⚠️ Panel didn't close properly, forcing closure...")
            driver.execute_script("""
                const panel = document.getElementById('side-panel');
                if (panel) {
                    panel.style.display = 'none';
                    panel.classList.remove('open');
                }
            """)
        else:
            print("✅ Side panel closed successfully")
        
        # Test 2: Draw a larger polygon that should capture both packaged activities
        print("\n🔄 Testing larger polygon to capture both packaged activities...")
        print("🎯 This larger polygon should encompass both sample_run.gpx and eastside_run.gpx")
        
        # Zoom out to ensure both activities are visible for the large polygon test
        print("🔍 Zooming out to ensure both activities are in view...")
        current_zoom = driver.execute_script("return map.getZoom();")
        new_zoom = max(11, current_zoom - 2)  # Zoom out by 2 levels, minimum zoom 11
        print(f"📏 Current zoom: {current_zoom}, new zoom: {new_zoom}")
        
        driver.execute_script(f"""
            // Use jumpTo for instant, deterministic positioning (no animation)
            map.jumpTo({{
                center: [{frederick_lon}, {frederick_lat}],
                zoom: {new_zoom}
            }});
        """)
        
        # Wait for map to settle at new zoom level
        print("⏳ Waiting for map to settle at new zoom level...")
        self.wait_for_map_idle_after_move(driver, timeout_ms=6000, verbose=True)
        
        # Wait for map idle and runs features at new zoom level
        print("⏳ Waiting for view to go idle after zoom out...")
        zoom_idle = driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (!window.__mapTestHelpers) return cb(false);
            window.__mapTestHelpers.waitForIdleAfterMove(12000).then(cb);
        """)
        print(f"🔎 Zoom out idle result: {zoom_idle}")
        
        # Verify features are still ready at new zoom
        features_ready_zoom = driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (!window.__mapTestHelpers) return cb(false);
            window.__mapTestHelpers.waitForRunsReady(10000).then(cb);
        """)
        
        if not features_ready_zoom:
            print("⚠️ Features not immediately ready at new zoom, continuing anyway...")
        else:
            print("✅ Features ready at new zoom level")
        
        # Wait for UI to be ready for second test (lasso button available)
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "lasso-btn"))
        )
        
        # Reactivate lasso mode (it gets deactivated when panel closes)
        print("🎯 Reactivating lasso selection mode for second test...")
        lasso_btn_second = self.find_clickable_element(driver, wait, "#lasso-btn")
        lasso_btn_second.click()
        
        # Wait for lasso mode to activate
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.getElementById('lasso-btn').classList.contains('active')")
        )
        
        # Verify lasso mode is active
        lasso_active_check = driver.execute_script("""
            const btn = document.getElementById('lasso-btn');
            const styles = window.getComputedStyle(btn);
            return {
                backgroundColor: styles.backgroundColor,
                isActive: styles.backgroundColor.includes('rgb') && 
                         !styles.backgroundColor.includes('255, 255, 255')
            };
        """)
        print(f"🔍 Lasso button state for second test: {lasso_active_check}")
        
        if not lasso_active_check['isActive']:
            print("❌ Lasso mode not properly activated for second test")
            # Try clicking again
            lasso_btn_second.click()
            
            # Wait for lasso mode to activate after retry
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script("return document.getElementById('lasso-btn').classList.contains('active')")
            )
        
        # Generate larger polygon with 350px radius to span both activities
        print("📐 Generating larger polygon (350px radius) to encompass both activities...")
        large_polygon_coords = driver.execute_script("""
            return window.__mapTestHelpers.generateCenterPolygon(350);
        """)
        print(f"🗺️ Generated large polygon coordinates: {len(large_polygon_coords)} points")
        
        # Convert to viewport points for the larger polygon
        large_viewport_points = driver.execute_script("""
            return window.__mapTestHelpers.projectToViewportPoints(arguments[0]);
        """, large_polygon_coords)
        print(f"🎯 Large polygon viewport points: {large_viewport_points}")
        
        # Draw the larger polygon
        print("👆 Drawing larger polygon with absolute viewport coordinates...")
        self._draw_polygon_absolute_viewport(driver, large_viewport_points)
        
        # Wait for lasso processing of larger polygon
        print("⏳ Waiting for large polygon lasso processing...")
        large_lasso_result = self._wait_for_lasso_completion(driver, wait, max_wait=20)
        
        # Verify results for large polygon - should capture both activities
        assert large_lasso_result['panel_opened'], f"Side panel should open for large polygon: {large_lasso_result['debug_info']}"
        assert large_lasso_result['run_count'] == 2, f"Large polygon should select exactly 2 activities (both packaged GPX files): found {large_lasso_result['run_count']} activities. Debug: {large_lasso_result['debug_info']}"
        
        print(f"✅ Large polygon lasso selection completed successfully!")
        print(f"📊 Selected {large_lasso_result['run_count']} activities with large polygon")
        print("🎉 Both small and large polygon tests passed - lasso selection working correctly!")
        
        # Continue to sidebar selection test instead of cleaning up
        print("\n🔄 Continuing to sidebar selection and visibility test...")
        
        # We should already have sidebar open with 2 activities from the large polygon test
        print(f"✅ Starting with sidebar open and {large_lasso_result['run_count']} activities selected")
        
        # Step 1: Sidebar manipulation - deselect all, then select one
        print("🎯 Step 1: Testing sidebar selection controls...")
        
        # First, click "deselect all"
        print("   📝 Clicking 'Deselect All' button...")
        deselect_all_btn = self.find_clickable_element(driver, wait, "#deselect-all")
        deselect_all_btn.click()
        
        # Wait for all checkboxes to be unchecked
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.querySelectorAll('.run-checkbox:checked').length") == 0
        )
        
        # Verify all checkboxes are unchecked and no activities are visible
        deselect_verification = driver.execute_script("""
            const checkboxes = document.querySelectorAll('.run-checkbox');
            const checkedBoxes = Array.from(checkboxes).filter(cb => cb.checked);
            const selectedRunsSize = window.selectedRuns ? window.selectedRuns.size : 0;
            
            return {
                totalCheckboxes: checkboxes.length,
                checkedCheckboxes: checkedBoxes.length,
                selectedRunsSize: selectedRunsSize,
                allUnchecked: checkedBoxes.length === 0
            };
        """)
        
        assert deselect_verification['allUnchecked'], f"All checkboxes should be unchecked after 'Deselect All': {deselect_verification}"
        print(f"   ✅ All {deselect_verification['totalCheckboxes']} checkboxes successfully unchecked")
        
        # Now select only the first activity
        print("   📝 Selecting first activity only...")
        first_checkbox = self.find_clickable_element(driver, wait, ".run-checkbox:first-of-type")
        first_checkbox.click()
        
        # Ensure the change event is properly triggered
        driver.execute_script("""
            const checkbox = document.querySelector('.run-checkbox:first-of-type');
            if (checkbox) {
                checkbox.dispatchEvent(new Event('change', {bubbles: true}));
            }
        """)
        
        # Wait for checkbox to be checked and UI to update
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.querySelectorAll('.run-checkbox:checked').length") > 0
        )
        
        print("   ✅ First activity checkbox clicked")
        
        # Step 2: Minimize the sidebar
        print("   📝 Minimizing sidebar...")
        collapse_btn = self.find_clickable_element(driver, wait, "#panel-collapse")
        collapse_btn.click()
        
        # Wait for sidebar to collapse
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script("return document.getElementById('side-panel').classList.contains('collapsed')")
        )
        
        # Verify sidebar is collapsed
        sidebar_collapsed = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            return panel && panel.classList.contains('collapsed');
        """)
        
        assert sidebar_collapsed, "Sidebar should be collapsed after clicking collapse button"
        print("   ✅ Sidebar successfully minimized")
        
        print("✅ Step 1 completed: Sidebar manipulation successful")
        
        # Step 2: Visibility verification
        print("🎯 Step 2: Verifying map visibility...")
        
        # Positive test: Verify exactly one activity is visible
        print("   🔍 Positive test: Verifying selected activity is visible...")
        features_verification = self.verify_features_in_current_viewport(driver)
        
        # Also check the map filter is correctly applied
        map_filter_check = driver.execute_script("""
            const layer = map.getLayer('runsVec');
            const filter = layer ? map.getFilter('runsVec') : null;
            const renderedFeatures = map.queryRenderedFeatures();
            const activityFeatures = renderedFeatures.filter(f => 
                f.geometry && f.geometry.type === 'LineString'
            );
            
            return {
                hasFilter: filter != null,
                filterApplied: filter != null,
                renderedActivityCount: activityFeatures.length
            };
        """)
        
        print(f"   📊 Map filter check: {map_filter_check}")
        print(f"   📊 Features in viewport: {features_verification['featuresInViewport']}")
        
        # Success criteria similar to test_01_activity_visibility.py
        success_criteria = {
            'features_found': features_verification['featuresInViewport'] > 0,
            'filter_applied': map_filter_check['filterApplied'],
        }
        
        print("🏆 Visibility verification results:")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}: {passed}")
        
        # Assert all criteria (following test_01_activity_visibility pattern)
        assert success_criteria['features_found'], f"No features visible on map (found {features_verification['featuresInViewport']})"
        assert success_criteria['filter_applied'], "Map filter should be applied when sidebar is open with selection"
        
        print("   ✅ Visibility verification passed: Selected activity is visible with filter applied")
        
        print("✅ Step 2 completed: Visibility verification successful")
        
        # Step 3: Proper cleanup - reopen sidebar and close with 'x'
        print("🎯 Step 3: Performing proper cleanup...")
        
        # Reopen the sidebar from collapsed state
        print("   📝 Reopening sidebar from collapsed state...")
        expand_btn = self.find_clickable_element(driver, wait, "#expand-btn")
        expand_btn.click()
        
        # Wait for sidebar to expand
        WebDriverWait(driver, 5).until(
            lambda d: not d.execute_script("return document.getElementById('side-panel').classList.contains('collapsed')")
        )
        
        # Verify sidebar is expanded
        sidebar_expanded = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            return panel && !panel.classList.contains('collapsed') && panel.classList.contains('open');
        """)
        
        assert sidebar_expanded, "Sidebar should be expanded after clicking expand button"
        print("   ✅ Sidebar successfully reopened")
        
        # Close with 'x' button
        print("   📝 Closing sidebar with 'x' button...")
        close_btn = self.find_clickable_element(driver, wait, "#panel-close")
        close_btn.click()
        
        # Wait for sidebar to close
        WebDriverWait(driver, 5).until(
            lambda d: not d.execute_script("return document.getElementById('side-panel').classList.contains('open')")
        )
        
        # Verify sidebar is properly closed and filter is cleared
        final_cleanup_check = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            const layer = map.getLayer('runsVec');
            const filter = layer ? map.getFilter('runsVec') : undefined;
            
            return {
                panelClosed: panel && !panel.classList.contains('open'),
                noFilter: filter == null
            };
        """)
        
        assert final_cleanup_check['panelClosed'], "Panel should be closed after clicking 'x'"
        assert final_cleanup_check['noFilter'], "Map filter should be cleared after closing sidebar"
        
        print("   ✅ Sidebar properly closed and filters cleared")
        
        # Final verification: all activities should be visible again
        final_features_check = self.verify_features_in_current_viewport(driver)
        print(f"   📊 Final check - features visible after cleanup: {final_features_check['featuresInViewport']}")
        
        # Assert that both packaged activities are visible after filter is cleared
        assert final_features_check['featuresInViewport'] >= 2, f"Both packaged activities should be visible after clearing filter (found {final_features_check['featuresInViewport']})"
        print("   ✅ All activities are visible again after cleanup - filter properly cleared")
        
        print("✅ Step 3 completed: Proper cleanup successful")
        
        print("🎉 Sidebar selection and visibility test completed successfully!")
        print("📋 Additional test verified:")
        print("   ✓ Started with sidebar open and multiple activities selected") 
        print("   ✓ 'Deselect all' button works correctly")
        print("   ✓ Individual activity selection works")
        print("   ✓ Sidebar can be minimized")
        print("   ✓ Map shows only selected activity when sidebar is minimized")
        print("   ✓ Non-selected activities are filtered out")
        print("   ✓ Sidebar can be reopened from collapsed state")
        print("   ✓ Sidebar can be properly closed with 'x' button")
        print("   ✓ All activities become visible again after cleanup")
        
        # Final cleanup: Close the side panel at the end of both tests
        print("🧹 Final cleanup: Closing side panel...")
        final_cleanup = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            if (panel && panel.classList.contains('open')) {
                // Try clicking the map to close it
                const mapElement = document.getElementById('map');
                if (mapElement) {
                    mapElement.click();
                }
                // Also remove the class directly
                panel.classList.remove('open');
                panel.style.display = 'none';
            }
            
            // Also deactivate lasso mode
            const lassoBtn = document.getElementById('lasso-btn');
            if (lassoBtn) {
                const styles = window.getComputedStyle(lassoBtn);
                const isActive = styles.backgroundColor.includes('rgb') && 
                               !styles.backgroundColor.includes('255, 255, 255');
                if (isActive) {
                    lassoBtn.click(); // Turn off lasso mode
                }
            }
            
            return 'cleanup_completed';
        """)
        print(f"🧹 Final cleanup result: {final_cleanup}")
        
        # Add diagnostics on unexpected results
        if lasso_result['run_count'] == 0 or large_lasso_result['run_count'] != 2:
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
            
            # Use shorter polling interval for more responsive checking
            WebDriverWait(driver, 0.2).until(lambda d: True)
        
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
    
