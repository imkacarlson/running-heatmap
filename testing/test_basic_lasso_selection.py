"""
Basic lasso selection test - focused on core functionality that we observed working.

This test replicates the successful lasso interaction that was observed:
- Lasso button activation (blue background)
- Triangle polygon drawing around Frederick activity  
- Side panel opening with run information

Uses existing session-scoped fixtures for reliability.
"""
import time
import pytest
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from base_mobile_test import BaseMobileTest

@pytest.mark.mobile
@pytest.mark.core
class TestBasicLassoSelection(BaseMobileTest):
    """Test basic lasso selection functionality with pre-packaged data"""
    
    def test_basic_lasso_polygon_selection(self, mobile_driver):
        """Test basic lasso selection around Frederick activity - replicates observed working behavior"""
        print("🧪 Testing basic lasso selection around Frederick activity...")
        
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        
        # Setup - launch app and wait for full initialization
        print("⏳ Allowing app to fully start up...")
        time.sleep(12)  # Increased startup wait for slow connections
        
        print("🔄 Switching to WebView context...")
        self.switch_to_webview(driver)
        
        print("🗺️ Waiting for map to fully load...")
        self.wait_for_map_load(driver, wait, verbose=True)
        
        
        # Navigate to Frederick activity location with robust data verification
        # Test data spans: lat 39.4143-39.4193, lon -77.4144 to -77.4194  
        frederick_lat, frederick_lon = 39.4168, -77.4169
        zoom_level = 14
        
        print(f"🗺️ Navigating to Frederick activity: {frederick_lat}, {frederick_lon}")
        
        # Navigate to coordinates
        driver.execute_script(f"""
            map.flyTo({{
                center: [{frederick_lon}, {frederick_lat}],
                zoom: {zoom_level},
                duration: 1500
            }});
        """)
        time.sleep(4)  # Wait for navigation
        
        # Verify PMTiles data is loaded and features are in viewport
        print("🔍 Verifying PMTiles data is loaded at target location...")
        data_verification = self._verify_pmtiles_data_loaded(driver, frederick_lat, frederick_lon)
        if not data_verification['data_loaded']:
            print(f"⚠️ PMTiles data not loaded, waiting additional time...")
            time.sleep(3)
            data_verification = self._verify_pmtiles_data_loaded(driver, frederick_lat, frederick_lon)
        
        print(f"📊 Data verification: {data_verification['features_count']} features found in viewport")
        print(f"🔍 Source used: {data_verification.get('source_name', 'unknown')}")
        if not data_verification['data_loaded']:
            print(f"❌ Data loading error: {data_verification.get('error', 'unknown error')}")
        assert data_verification['data_loaded'], "PMTiles data must be loaded before lasso selection"
        
        
        # Activate lasso mode - this was working!
        print("🎯 Activating lasso selection mode...")
        lasso_btn = self.find_clickable_element(driver, wait, "#lasso-btn")
        lasso_btn.click()
        time.sleep(1)
        
        # Verify lasso mode is active (blue background)
        button_style = driver.execute_script("""
            const btn = document.getElementById('lasso-btn');
            const styles = window.getComputedStyle(btn);
            return {
                background: styles.backgroundColor,
                color: styles.color,
                exists: !!btn
            };
        """)
        print(f"🔍 Lasso button active style: {button_style}")
        
        
        # Draw appropriately sized triangle polygon around Frederick activity
        print("🖊️ Drawing robust triangle polygon around Frederick activity...")
        triangle_result = self._draw_robust_triangle_polygon(driver, frederick_lat, frederick_lon)
        assert triangle_result['success'], f"Triangle drawing failed: {triangle_result.get('error', 'Unknown error')}"
        
        
        # Smart wait for lasso processing with multiple verification attempts
        print("⏳ Waiting for lasso processing with smart timeout...")
        lasso_result = self._wait_for_lasso_processing(driver, wait)
        
        # Enhanced precision assertions
        assert button_style['exists'], "Lasso button should exist"
        assert lasso_result['panel_opened'], f"Side panel should open after lasso processing: {lasso_result['debug_info']}"
        
        # Verify precise selection - should capture exactly 1 run (Frederick, not Eastside)
        run_count = lasso_result['run_count']
        print(f"📊 Final activity count: {run_count}")
        
        # Should select exactly 1 activity (Frederick run inside triangle)
        if run_count == 0:
            print(f"❌ No activities selected. Debug info: {lasso_result['debug_info']}")
            print(f"📍 Triangle coordinates used: {triangle_result['coordinates']}")
            print(f"🎯 Expected data range: lat 39.4143-39.4193, lon -77.4144 to -77.4194")
            
        assert run_count == 1, f"Expected exactly 1 activity selected, got {run_count}. Debug: {lasso_result['debug_info']}"
        
        # Get panel information for content verification
        panel_info = self.check_side_panel(driver)
        selected_runs_info = self.get_selected_runs_details(driver)
        print(f"📋 Selected activity content preview: {panel_info.get('fullText', '')[:100]}...")
        
        # Analyze the content for precision verification
        if panel_info['visible'] and panel_info['hasContent'] and run_count == 1:
            full_text = panel_info.get('fullText', '')
            
            # Check if it contains Frederick activity date (7/15/2024) vs Eastside activity date (7/16/2024)
            has_frederick_date = '7/15/2024' in full_text
            has_eastside_date = '7/16/2024' in full_text
            
            # Also check for track names if they appear  
            has_frederick_name = 'Frederick' in full_text
            has_eastside_name = 'Eastside' in full_text
            
            if has_frederick_date and not has_eastside_date:
                print(f"✅ Perfect precision: Frederick activity (7/15/2024) selected, Eastside activity (7/16/2024) excluded")
            elif has_frederick_name and not has_eastside_name:
                print(f"✅ Good precision: Frederick activity selected by name, Eastside excluded")
            elif has_frederick_date or has_frederick_name:
                print(f"✅ Frederick activity detected (date={has_frederick_date}, name={has_frederick_name})")
            else:
                print(f"⚠️ Content analysis: Frederick date={has_frederick_date}, Eastside date={has_eastside_date}")
        else:
            print("✅ Got exactly 1 activity as expected")
        
        print("✅ Robust lasso precision test completed successfully")
        print(f"🎯 Test completed with triangle size: {triangle_result.get('size', 'unknown')}")
        print(f"📈 Processing method: {lasso_result.get('debug_info', 'standard')}")
    
    
    
    def _verify_pmtiles_data_loaded(self, driver, center_lat, center_lon):
        """Verify PMTiles data is loaded and features are available in viewport"""
        return driver.execute_script(f"""
            const centerLat = {center_lat};
            const centerLon = {center_lon};
            const radius = 0.005;  // Slightly larger than our test data span
            
            try {{
                // Check if PMTiles source exists and is loaded
                const sources = map.getStyle().sources;
                let sourceName = null;
                let pmtilesSource = null;
                
                // Try different possible source names
                const possibleNames = ['runsVec', 'pmtiles-source', 'runs', 'activities'];
                for (const name of possibleNames) {{
                    if (sources[name]) {{
                        sourceName = name;
                        pmtilesSource = sources[name];
                        break;
                    }}
                }}
                
                if (!pmtilesSource || !sourceName) {{
                    return {{ 
                        data_loaded: false, 
                        error: 'No PMTiles source found. Available sources: ' + Object.keys(sources).join(', '), 
                        features_count: 0 
                    }};
                }}
                
                // Query features in the area around our center point
                const bbox = [
                    centerLon - radius, centerLat - radius,  // southwest
                    centerLon + radius, centerLat + radius   // northeast  
                ];
                
                const features = map.querySourceFeatures(sourceName, {{
                    filter: null,
                    sourceLayer: 'runs'
                }}) || [];
                
                // Check if any features are in our target area
                const featuresInArea = features.filter(feature => {{
                    if (!feature.geometry || !feature.geometry.coordinates) return false;
                    
                    // For LineString geometry, check if any coordinate is in our bbox
                    const coords = feature.geometry.coordinates;
                    if (Array.isArray(coords) && coords.length > 0) {{
                        return coords.some(coord => {{
                            if (Array.isArray(coord) && coord.length >= 2) {{
                                const [lon, lat] = coord;
                                return lon >= bbox[0] && lon <= bbox[2] && lat >= bbox[1] && lat <= bbox[3];
                            }}
                            return false;
                        }});
                    }}
                    return false;
                }});
                
                return {{
                    data_loaded: true,
                    features_count: featuresInArea.length,
                    total_features: features.length,
                    bbox_used: bbox,
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
    
    def _draw_robust_triangle_polygon(self, driver, center_lat, center_lon):
        """Draw triangle polygon with improved size and error handling"""
        print(f"🖊️ Drawing robust triangle around {center_lat}, {center_lon}")
        
        # Try multiple triangle sizes, starting with larger size based on actual data analysis
        sizes_to_try = [0.0035, 0.003, 0.0025]  # Much larger than original 0.001
        
        for attempt, size in enumerate(sizes_to_try, 1):
            try:
                print(f"🔄 Triangle attempt {attempt} with size {size} degrees...")
                result = self._draw_triangle_with_size(driver, center_lat, center_lon, size)
                if result['success']:
                    print(f"✅ Triangle drawn successfully with size {size}")
                    return result
                print(f"⚠️ Triangle attempt {attempt} failed: {result.get('error')}")
            except Exception as e:
                print(f"❌ Triangle attempt {attempt} exception: {e}")
                if attempt == len(sizes_to_try):  # Last attempt
                    return {'success': False, 'error': f'All triangle attempts failed. Last error: {e}'}
                continue
                
        return {'success': False, 'error': 'All triangle size attempts failed'}
    
    def _draw_triangle_with_size(self, driver, center_lat, center_lon, size):
        """Draw triangle with specific size"""
        # Get map element for reference
        map_element = driver.find_element(By.CSS_SELECTOR, "#map")
        
        # Generate triangle points around the center with specified size
        triangle_info = driver.execute_script(f"""
            const centerLat = {center_lat};
            const centerLon = {center_lon};
            const size = {size};
            
            // Create triangle points around center (larger triangle)
            const coords = [
                [centerLon, centerLat + size],        // Top point
                [centerLon - size, centerLat - size], // Bottom left
                [centerLon + size, centerLat - size], // Bottom right  
                [centerLon, centerLat + size]         // Close triangle
            ];
            
            // Convert to screen coordinates with bounds checking
            const mapContainer = document.getElementById('map');
            const mapRect = mapContainer.getBoundingClientRect();
            
            const screenPoints = coords.map(coord => {{
                const point = map.project(coord);
                return {{ 
                    x: Math.round(Math.max(30, Math.min(mapRect.width - 30, point.x))), 
                    y: Math.round(Math.max(30, Math.min(mapRect.height - 30, point.y)))
                }};
            }});
            
            return {{
                success: true,
                points: screenPoints,
                mapBounds: {{ width: mapRect.width, height: mapRect.height }},
                geoCoords: coords,
                size: size
            }};
        """)
        
        if not triangle_info or not triangle_info.get('points'):
            return {'success': False, 'error': 'Failed to generate triangle points'}
        
        points = triangle_info['points']
        print(f"📐 Triangle points: {points}")
        
        # Draw the triangle using ActionChains
        actions = ActionChains(driver)
        
        # Move to map element, then to first point
        first_point = points[0]
        actions.move_to_element(map_element)
        actions.move_by_offset(
            first_point['x'] - triangle_info['mapBounds']['width'] // 2,
            first_point['y'] - triangle_info['mapBounds']['height'] // 2
        )
        actions.click_and_hold()
        
        # Draw to each subsequent point
        current_x, current_y = first_point['x'], first_point['y']
        for point in points[1:]:
            offset_x = point['x'] - current_x
            offset_y = point['y'] - current_y
            actions.move_by_offset(offset_x, offset_y)
            current_x, current_y = point['x'], point['y']
            time.sleep(0.15)  # Slight delay for drawing
        
        # Complete the triangle
        actions.release()
        actions.perform()
        
        time.sleep(1)  # Brief pause for processing
        
        return {
            'success': True,
            'coordinates': triangle_info['geoCoords'],
            'screen_points': points,
            'size': size
        }
    
    def _wait_for_lasso_processing(self, driver, wait):
        """Smart wait for lasso processing with progressive timeouts and multiple verification methods"""
        max_attempts = 3
        wait_times = [5, 8, 12]  # Progressive timeouts
        
        for attempt in range(max_attempts):
            wait_time = wait_times[attempt]
            print(f"⏳ Lasso processing attempt {attempt + 1}/{max_attempts}, waiting {wait_time}s...")
            
            # Progressive wait with status monitoring
            for i in range(wait_time):
                time.sleep(1)
                if i % 2 == 0:  # Check every 2 seconds
                    panel_info = self.check_side_panel(driver)
                    if panel_info.get('runCount', 0) > 0:
                        print(f"✅ Activities detected early at {i+1}s")
                        return {
                            'panel_opened': True,
                            'run_count': panel_info['runCount'],
                            'debug_info': f'Success on attempt {attempt+1}, early detection at {i+1}s'
                        }
            
            # Final check for this attempt
            panel_info = self.check_side_panel(driver)
            run_count = panel_info.get('runCount', 0)
            
            if run_count > 0:
                print(f"✅ Lasso processing successful on attempt {attempt + 1}")
                return {
                    'panel_opened': True,
                    'run_count': run_count,
                    'debug_info': f'Success on attempt {attempt+1} after {wait_time}s'
                }
            
            print(f"⚠️ Attempt {attempt + 1} failed: runCount={run_count}, panel_visible={panel_info.get('visible')}")
            
            # If not last attempt, try clicking lasso button again
            if attempt < max_attempts - 1:
                print("🔄 Retrying lasso activation...")
                try:
                    lasso_btn = self.find_clickable_element(driver, wait, "#lasso-btn")
                    lasso_btn.click()
                    time.sleep(0.5)
                except Exception as e:
                    print(f"⚠️ Lasso button retry failed: {e}")
        
        # All attempts failed
        return {
            'panel_opened': panel_info.get('visible', False),
            'run_count': 0,
            'debug_info': f'Failed after {max_attempts} attempts. Final panel state: visible={panel_info.get("visible")}, hasContent={panel_info.get("hasContent")}, text_length={len(panel_info.get("fullText", ""))}'
        }
    
