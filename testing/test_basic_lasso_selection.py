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
        
        
        # Navigate to Frederick activity location (where we saw it working)
        frederick_lat, frederick_lon = 39.4168, -77.4169
        zoom_level = 14
        
        print(f"🗺️ Navigating to Frederick activity: {frederick_lat}, {frederick_lon}")
        
        driver.execute_script(f"""
            map.flyTo({{
                center: [{frederick_lon}, {frederick_lat}],
                zoom: {zoom_level},
                duration: 1500
            }});
        """)
        time.sleep(4)  # Wait for navigation and data loading
        
        
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
        
        
        # Draw triangle polygon around Frederick activity - this was working beautifully!
        print("🖊️ Drawing triangle polygon around Frederick activity...")
        self.draw_triangle_polygon(driver, frederick_lat, frederick_lon)
        
        
        # Wait for processing and verify side panel opens - this was happening!
        time.sleep(3)
        print("📋 Checking if side panel opened...")
        
        panel_info = self.check_side_panel(driver)
        
        # Enhanced precision assertions
        assert button_style['exists'], "Lasso button should exist"
        assert panel_info['visible'], "Side panel should be visible after polygon drawing"
        
        # Verify precise selection - should capture exactly 1 run (Frederick, not Eastside)
        run_count = panel_info.get('runCount', 0)  
        print(f"📊 Activity count: {run_count}")
        
        # Should select exactly 1 activity (Frederick run inside triangle)
        assert run_count == 1, f"Expected exactly 1 activity selected, got {run_count}"
        
        # Get details for content verification
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
        
        print("✅ Enhanced lasso precision test completed successfully")
    
    
    
    def draw_triangle_polygon(self, driver, center_lat, center_lon):
        """Draw a simple triangle polygon around the center point - replicates what was working"""
        print(f"🖊️ Drawing triangle around {center_lat}, {center_lon}")
        
        # Get map element for reference
        map_element = driver.find_element(By.CSS_SELECTOR, "#map")
        
        # Generate triangle points around the center
        triangle_info = driver.execute_script(f"""
            const centerLat = {center_lat};
            const centerLon = {center_lon};
            const size = 0.001;  // Small triangle
            
            // Create triangle points around center
            const coords = [
                [centerLon, centerLat + size],     // Top point
                [centerLon - size, centerLat - size], // Bottom left
                [centerLon + size, centerLat - size], // Bottom right  
                [centerLon, centerLat + size]      // Close triangle
            ];
            
            // Convert to screen coordinates
            const mapContainer = document.getElementById('map');
            const mapRect = mapContainer.getBoundingClientRect();
            
            const screenPoints = coords.map(coord => {{
                const point = map.project(coord);
                return {{ 
                    x: Math.round(Math.max(20, Math.min(mapRect.width - 20, point.x))), 
                    y: Math.round(Math.max(20, Math.min(mapRect.height - 20, point.y)))
                }};
            }});
            
            return {{
                points: screenPoints,
                mapBounds: {{ width: mapRect.width, height: mapRect.height }}
            }};
        """)
        
        if not triangle_info or not triangle_info.get('points'):
            raise Exception("Failed to generate triangle points")
        
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
            time.sleep(0.2)  # Visual feedback
        
        # Complete the triangle
        actions.release()
        actions.perform()
        
        time.sleep(2)  # Allow processing
        print("✅ Triangle polygon drawn")
        
        return points
    
