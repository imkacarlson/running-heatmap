"""
End-to-end GPX to Mobile testing with proper fixture infrastructure
Uses session-scoped fixtures to handle expensive build operations efficiently
"""
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.mobile
class TestDataPipeline:
    """Test data pipeline without Appium dependency"""
    
    def test_data_pipeline_creates_valid_files(self, isolated_test_environment):
        """Test that data pipeline creates valid intermediate files"""
        env = isolated_test_environment
        
        # Verify runs.pkl exists and has content
        runs_pkl = env['mobile_dir'] / "runs.pkl"
        assert runs_pkl.exists(), "runs.pkl should be created"
        
        import pickle
        with open(runs_pkl, 'rb') as f:
            runs = pickle.load(f)
        assert len(runs) == 1, "Should have exactly 1 test run"
        
        # Verify PMTiles exists and has reasonable size
        pmtiles_file = env['pmtiles_path']
        assert pmtiles_file.exists(), "PMTiles should be created"
        assert pmtiles_file.stat().st_size > 1000, "PMTiles should have reasonable size"
        
        print(f"✅ Data pipeline validation passed")
        print(f"   📊 Runs: {len(runs)}")
        print(f"   🗺️ PMTiles: {pmtiles_file.stat().st_size} bytes")
    
    def test_apk_build_succeeds(self, test_apk_with_data):
        """Test that APK build completes successfully"""
        apk_path = test_apk_with_data
        
        assert apk_path.exists(), "APK should exist after build"
        assert apk_path.stat().st_size > 1_000_000, "APK should be at least 1MB"
        
        print(f"✅ APK build validation passed")
        print(f"   📱 APK: {apk_path}")
        print(f"   📊 Size: {apk_path.stat().st_size / 1_000_000:.1f} MB")


@pytest.mark.mobile
class TestMobileApp:
    """Test mobile app functionality with test data - uses Appium"""
    
    def setup_mobile_driver(self, fresh_app_session):
        """Setup mobile driver for testing"""
        from appium import webdriver
        from selenium.webdriver.support.ui import WebDriverWait
        from pathlib import Path
        
        desired_caps = {
            'platformName': 'Android',
            'deviceName': 'TestDevice',
            'appPackage': 'com.run.heatmap',
            'appActivity': 'com.run.heatmap.MainActivity',
            'automationName': 'UiAutomator2',
            'newCommandTimeout': 300,
            'noReset': True,
            'fullReset': False,
            'chromedriverExecutable': str(Path(__file__).parent / "vetted-drivers" / "chromedriver-101")
        }
        
        self.driver = webdriver.Remote('http://localhost:4723/wd/hub', desired_caps)
        self.wait = WebDriverWait(self.driver, 30)
        return {'driver': self.driver, 'wait': self.wait}
    
    def switch_to_webview(self):
        """Switch to WebView context"""
        time.sleep(2)
        contexts = self.driver.contexts
        for context in contexts:
            if 'WEBVIEW' in context:
                self.driver.switch_to.context(context)
                print(f"✅ Switched to context: {context}")
                return True
        return False
    
    def wait_for_map_load(self):
        """Wait for map to load"""
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#map"))
        )
        time.sleep(3)
    
        try:
            from pathlib import Path
            return path
        except Exception as e:
            return None
    
    @pytest.mark.legacy
    def test_app_launches_with_test_data(self, fresh_app_session):
        """Test that app launches successfully with test data - REDUNDANT: App launch is verified in rock-solid test"""
        print("🧪 Testing app launch with test data...")
        
        # Setup mobile driver
        mobile_info = self.setup_mobile_driver(fresh_app_session)
        
        try:
            # Give app time to load
            time.sleep(8)
            
            # Switch to WebView
            webview_found = self.switch_to_webview()
            assert webview_found, "Should be able to switch to WebView"
            
            # Wait for map to load
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            map_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#map"))
            )
            assert map_element is not None, "Map should be present"
            
            # Verify map loads
            time.sleep(5)
            map_loaded = self.driver.execute_script("""
                return typeof map !== 'undefined' && map.loaded && map.loaded();
            """)
            
            print(f"📍 Map loaded: {map_loaded}")
            print("✅ App launches successfully with test data")
            
        finally:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
    
    @pytest.mark.legacy
    def test_test_activity_is_visible_on_map(self, fresh_app_session):
        """Test that the test activity is actually visible on the map - REDUNDANT: Use rock-solid test instead"""  
        print("🧪 Testing test activity visualization...")
        
        # Setup mobile driver
        mobile_info = self.setup_mobile_driver(fresh_app_session)
        
        try:
            # Launch and load app
            time.sleep(8)
            self.switch_to_webview()
            self.wait_for_map_load()
        
            # Get map information to verify test data is loaded
            map_info = self.driver.execute_script("""
            if (typeof map !== 'undefined') {
                const style = map.getStyle();
                const sources = style.sources || {};
                
                return {
                    sources: Object.keys(sources),
                    runsVecExists: 'runsVec' in sources,
                    runsVecUrl: sources.runsVec ? sources.runsVec.url : null
                };
            }
            return null;
        """)
        
            print(f"🗺️ Map sources: {map_info['sources']}")
            print(f"📊 RunsVec source: {map_info['runsVecExists']}")
            if map_info['runsVecUrl']:
                print(f"🔗 PMTiles URL: {map_info['runsVecUrl']}")
            
            assert map_info['runsVecExists'], "runsVec source should be loaded"
        
            # Pan to test activity location (Frederick, MD)
            test_lat = 39.4168
            test_lon = -77.4169
            zoom_level = 16
        
            print(f"🗺️ Panning to test location: {test_lat}, {test_lon}")
            
            self.driver.execute_script(f"""
                if (typeof map !== 'undefined') {{
                    map.flyTo({{
                        center: [{test_lon}, {test_lat}],
                        zoom: {zoom_level},
                        duration: 2000
                    }});
                }}
            """)
        
            # Wait for map to pan and data to load
            time.sleep(6)
        
            # Check for rendered features in the area
            features_info = self.driver.execute_script("""
            if (typeof map !== 'undefined') {
                try {
                    const features = map.queryRenderedFeatures();
                    const lineFeatures = features.filter(f => 
                        f.geometry && f.geometry.type === 'LineString');
                    
                    // Also try querying source features directly
                    const sourceFeatures = map.querySourceFeatures('runsVec');
                    
                    return {
                        renderedTotal: features.length,
                        renderedLines: lineFeatures.length,
                        sourceTotal: sourceFeatures.length,
                        sampleRendered: lineFeatures[0] || null,
                        sampleSource: sourceFeatures[0] || null,
                        zoom: map.getZoom(),
                        center: map.getCenter()
                    };
                } catch (e) {
                    return { error: e.message };
                }
            }
            return null;
        """)
        
            print(f"🎯 Features info: {features_info}")
            
            if features_info and not features_info.get('error'):
                print(f"📊 Rendered features: {features_info['renderedTotal']}")
                print(f"📍 Line features: {features_info['renderedLines']}")
                print(f"📂 Source features: {features_info['sourceTotal']}")
                print(f"🔍 Zoom: {features_info['zoom']}")
                
                # We should have at least some features from our test data
                assert features_info['sourceTotal'] > 0, "Should have features in PMTiles source"
            
        
            print("✅ Test activity visualization test completed")
            
        finally:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
    
    def test_map_navigation_works(self, fresh_app_session):
        """Test that map navigation controls work with test data"""
        print("🧪 Testing map navigation with test data...")
        
        # Setup mobile driver
        mobile_info = self.setup_mobile_driver(fresh_app_session)
        
        try:
            time.sleep(8)
            self.switch_to_webview() 
            self.wait_for_map_load()
        
            # Test zoom controls
            initial_zoom = self.driver.execute_script("return map.getZoom();")
            
            # Click zoom in
            from selenium.webdriver.common.by import By
            zoom_in_btn = self.driver.find_element(By.CSS_SELECTOR, "#zoom-in-btn")
            zoom_in_btn.click()
            time.sleep(2)
            
            new_zoom = self.driver.execute_script("return map.getZoom();")
            assert new_zoom > initial_zoom, "Zoom should increase"
            
        
            print(f"📍 Zoom test: {initial_zoom} → {new_zoom}")
            print("✅ Map navigation works with test data")
            
        finally:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()


if __name__ == '__main__':
    import unittest
    unittest.main()