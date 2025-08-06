"""
Basic functionality tests for the mobile app
Tests existing features to verify the testing framework works
"""
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from base_mobile_test import BaseMobileTest

@pytest.mark.core
class TestBasicFunctionality(BaseMobileTest):
    
    
    
    def test_map_controls_present(self, mobile_driver):
        """Test that map control buttons are present and visible"""
        print("Testing map controls...")
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        self.switch_to_webview(driver)
        self.wait_for_map_load(driver, wait, verbose=True)
        
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
        self.wait_for_map_load(driver, wait, verbose=True)

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
        self.wait_for_map_load(driver, wait, verbose=True)

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

