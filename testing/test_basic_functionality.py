"""
Basic functionality tests for the mobile app
Tests existing features to verify the testing framework works
"""
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.core
class TestBasicFunctionality:
    
    def test_map_controls_present(self, mobile_driver):
        """Test that map control buttons are present and visible"""
        print("Testing map controls...")
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        self.switch_to_webview(driver)
        self.wait_for_map_load(driver, wait)
        
        # Wait for map controls to be visible (using correct CSS selectors)
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#zoom-in-btn")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#zoom-out-btn")))
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#extras-btn")))
        
        # Assert that all controls are displayed
        assert driver.find_element(By.CSS_SELECTOR, "#zoom-in-btn").is_displayed()
        assert driver.find_element(By.CSS_SELECTOR, "#zoom-out-btn").is_displayed()
        assert driver.find_element(By.CSS_SELECTOR, "#extras-btn").is_displayed()
        
        print("✅ All map controls are present and visible")
        
    def test_zoom_functionality(self, mobile_driver):
        """Test that zoom controls work"""
        print("Testing zoom functionality...")
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        self.switch_to_webview(driver)
        self.wait_for_map_load(driver, wait)

        initial_zoom = driver.execute_script("return map.getZoom();")
        print(f"Initial zoom level: {initial_zoom}")
        
        # Click zoom-in and verify zoom level increases
        driver.find_element(By.CSS_SELECTOR, "#zoom-in-btn").click()
        time.sleep(2)
        zoomed_in_level = driver.execute_script("return map.getZoom();")
        print(f"Zoom after zoom-in: {zoomed_in_level}")
        assert zoomed_in_level > initial_zoom
        
        # Click zoom-out and verify zoom level decreases
        driver.find_element(By.CSS_SELECTOR, "#zoom-out-btn").click()
        time.sleep(2)
        zoomed_out_level = driver.execute_script("return map.getZoom();")
        print(f"Zoom after zoom-out: {zoomed_out_level}")
        assert zoomed_out_level < zoomed_in_level
        
        print("✅ Zoom functionality works correctly")
        
    def test_extras_panel_opens(self, mobile_driver):
        """Test that the extras panel opens when button is clicked"""
        print("Testing extras panel...")
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        self.switch_to_webview(driver)
        self.wait_for_map_load(driver, wait)

        # Click extras button to open panel
        driver.find_element(By.CSS_SELECTOR, "#extras-btn").click()
        time.sleep(1)
        
        # Verify panel is visible (check for 'open' class)
        panel = driver.find_element(By.CSS_SELECTOR, "#extras-panel")
        panel_classes = panel.get_attribute("class")
        assert "open" in panel_classes, f"Extras panel should have 'open' class, got: {panel_classes}"
        
        # Click close button to close panel
        driver.find_element(By.CSS_SELECTOR, "#extras-close").click()
        time.sleep(1)
        
        # Verify panel is hidden (no 'open' class)
        panel_classes = panel.get_attribute("class")
        assert "open" not in panel_classes, f"Extras panel should not have 'open' class after closing, got: {panel_classes}"
        
        print("✅ Extras panel opens and closes correctly")

    def wait_for_map_load(self, driver, wait):
        """Wait for map to load with robust criteria for slow connections"""
        print("🗺️ Waiting for map to load (extended wait for slow WiFi)...")
        
        # Wait for map element with longer timeout
        print("🔍 Waiting for map element...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#map")))
        
        # Extended wait for slow connections
        print("⏳ Giving extra time for map initialization on slow WiFi...")
        time.sleep(8)  # Increased from 3 to 8 seconds
        
        # Wait for map to actually be functional with retries
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                print(f"🔍 Map functionality check {attempt + 1}/{max_attempts}...")
                
                map_status = driver.execute_script("""
                    return {
                        mapExists: typeof map !== 'undefined',
                        elementExists: !!document.getElementById('map'),
                        canvasExists: !!document.querySelector('#map canvas'),
                        mapLoaded: typeof map !== 'undefined' && map.loaded && map.loaded(),
                        mapStyle: typeof map !== 'undefined' && map.isStyleLoaded && map.isStyleLoaded(),
                        hasContainer: !!document.querySelector('#map .mapboxgl-canvas-container, #map .maplibregl-canvas-container')
                    };
                """)
                
                print(f"🔍 Map status: {map_status}")
                
                # Check multiple conditions for robust loading detection
                conditions_met = (
                    map_status['mapExists'] and 
                    map_status['elementExists'] and
                    (map_status['canvasExists'] or map_status['hasContainer'])
                )
                
                if conditions_met:
                    print("✅ Map loaded successfully")
                    # Extra wait for data loading
                    print("📡 Allowing time for map data to load...")
                    time.sleep(3)
                    return True
                    
                if attempt < max_attempts - 1:
                    print(f"⏳ Map not ready, waiting... (attempt {attempt + 1})")
                    time.sleep(4)  # Wait before retry
                    
            except Exception as e:
                print(f"⚠️ Map check attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(4)
                    continue
                else:
                    raise
        
        raise Exception(f"Map failed to load after {max_attempts} attempts: {map_status}")

    def switch_to_webview(self, driver):
        """Switch to WebView context for hybrid app testing"""
        time.sleep(10)  # Wait for WebView to load
        contexts = driver.contexts
        print(f"Available contexts: {contexts}")
        
        for context in contexts:
            if 'WEBVIEW' in context:
                driver.switch_to.context(context)
                print(f"Switched to context: {context}")
                return True
        return False
