"""
Basic functionality tests for the mobile app
Tests existing features to verify the testing framework works
"""
import time
import pytest
from base_test import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class TestBasicFunctionality(BaseTest):
    
    @pytest.mark.legacy
    def test_app_launches_successfully(self):
        """Test that the app launches and basic UI elements are present - REDUNDANT: App launch is verified in rock-solid test"""
        print("Testing app launch...")
        
        # Give app extra time to fully load
        time.sleep(5)
        
        # Take screenshot of initial state
        self.take_screenshot("01_initial_launch")
        
        # Switch to WebView context to interact with the web content
        webview_found = self.switch_to_webview()
        self.assertTrue(webview_found, "Could not find WebView context")
        
        # Wait for map container to be present (using CSS selector instead of ID)
        map_element = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#map"))
        )
        self.assertIsNotNone(map_element, "Map container not found")
        
        print("✅ App launched successfully and map container found")
        
    @pytest.mark.core
    def test_map_controls_present(self):
        """Test that map control buttons are present and visible"""
        print("Testing map controls...")
        
        time.sleep(3)
        self.switch_to_webview()
        
        # Wait for map to load
        self.wait_for_map_load()
        
        # Check for zoom in button (using CSS selectors)
        zoom_in_btn = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#zoom-in-btn"))
        )
        self.assertTrue(zoom_in_btn.is_displayed(), "Zoom in button not visible")
        
        # Check for zoom out button
        zoom_out_btn = self.driver.find_element(By.CSS_SELECTOR, "#zoom-out-btn")
        self.assertTrue(zoom_out_btn.is_displayed(), "Zoom out button not visible")
        
        # Check for lasso button
        lasso_btn = self.driver.find_element(By.CSS_SELECTOR, "#lasso-btn")
        self.assertTrue(lasso_btn.is_displayed(), "Lasso button not visible")
        
        # Check for extras button
        extras_btn = self.driver.find_element(By.CSS_SELECTOR, "#extras-btn")
        self.assertTrue(extras_btn.is_displayed(), "Extras button not visible")
        
        self.take_screenshot("02_map_controls_visible")
        print("✅ All map controls are present and visible")
        
    @pytest.mark.core
    def test_zoom_functionality(self):
        """Test that zoom controls work"""
        print("Testing zoom functionality...")
        
        time.sleep(3)
        self.switch_to_webview()
        self.wait_for_map_load()
        
        # Get initial zoom level
        initial_zoom = self.driver.execute_script("return map.getZoom();")
        print(f"Initial zoom level: {initial_zoom}")
        
        # Click zoom in
        zoom_in_btn = self.driver.find_element(By.CSS_SELECTOR, "#zoom-in-btn")
        zoom_in_btn.click()
        time.sleep(2)
        
        # Check zoom increased
        new_zoom = self.driver.execute_script("return map.getZoom();")
        print(f"Zoom after zoom-in: {new_zoom}")
        self.assertGreater(new_zoom, initial_zoom, "Zoom did not increase")
        
        # Click zoom out
        zoom_out_btn = self.driver.find_element(By.CSS_SELECTOR, "#zoom-out-btn")
        zoom_out_btn.click()
        time.sleep(2)
        
        # Check zoom decreased
        final_zoom = self.driver.execute_script("return map.getZoom();")
        print(f"Zoom after zoom-out: {final_zoom}")
        self.assertLess(final_zoom, new_zoom, "Zoom did not decrease")
        
        self.take_screenshot("03_zoom_functionality")
        print("✅ Zoom functionality works correctly")
        
    @pytest.mark.core
    def test_extras_panel_opens(self):
        """Test that the extras panel opens when button is clicked"""
        print("Testing extras panel...")
        
        time.sleep(3)
        self.switch_to_webview()
        self.wait_for_map_load()
        
        # Click extras button
        extras_btn = self.driver.find_element(By.CSS_SELECTOR, "#extras-btn")
        extras_btn.click()
        time.sleep(2)
        
        # Check that extras panel is now open
        extras_panel = self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#extras-panel"))
        )
        
        # Check if panel has 'open' class
        panel_classes = extras_panel.get_attribute("class")
        self.assertIn("open", panel_classes, "Extras panel did not open")
        
        # Check for last activity content (this might take time to load)
        time.sleep(3)
        extras_content = self.driver.find_element(By.CSS_SELECTOR, "#extras-content")
        self.assertTrue(extras_content.is_displayed(), "Extras content not visible")
        
        self.take_screenshot("04_extras_panel_open")
        
        # Close the panel
        extras_close = self.driver.find_element(By.CSS_SELECTOR, "#extras-close")
        extras_close.click()
        time.sleep(1)
        
        # Verify panel closed
        panel_classes = extras_panel.get_attribute("class")
        self.assertNotIn("open", panel_classes, "Extras panel did not close")
        
        print("✅ Extras panel opens and closes correctly")

if __name__ == '__main__':
    import unittest
    unittest.main()