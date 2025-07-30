"""
Mobile app tests that use session-scoped fixtures
"""
import time
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import TestConfig
from pathlib import Path


@pytest.fixture(scope="function")
def mobile_driver(test_emulator_with_apk):
    """Create Appium driver for mobile tests"""
    print("📱 Starting Appium session...")
    
    # Set up Appium options
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android Emulator"
    options.app_package = "com.run.heatmap"
    options.app_activity = "com.run.heatmap.MainActivity"
    options.auto_grant_permissions = True
    options.chromedriver_autodownload = False
    options.chromedriver_executable = str(Path(__file__).parent / "vetted-drivers/chromedriver-101")
    options.native_web_screenshot = True
    options.new_command_timeout = 300
    options.auto_webview = False
    
    # Create driver
    driver = webdriver.Remote("http://localhost:4723/wd/hub", options=options)
    wait = WebDriverWait(driver, 30)
    
    yield {
        'driver': driver,
        'wait': wait,
        'apk_info': test_emulator_with_apk
    }
    
    # Cleanup
    print("📱 Closing Appium session...")
    driver.quit()


class TestMobileAppWithTestData:
    """Mobile app tests using session-scoped fixtures"""
    
    def test_app_launches_with_test_data(self, mobile_driver):
        """Test that app launches successfully with test data"""
        print("🧪 Testing app launch with test data...")
        
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        
        # Give app time to load
        time.sleep(8)
        
        # Take screenshot
        screenshots_dir = Path(__file__).parent / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        driver.save_screenshot(str(screenshots_dir / "01_fixture_app_launch.png"))
        
        # Switch to WebView
        contexts = driver.contexts
        print(f"Available contexts: {contexts}")
        
        webview_context = None
        for context in contexts:
            if 'WEBVIEW' in context:
                webview_context = context
                break
        
        assert webview_context is not None, "Should have WebView context"
        driver.switch_to.context(webview_context)
        print(f"Switched to context: {webview_context}")
        
        # Wait for map
        map_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#map"))
        )
        assert map_element is not None, "Map should be present"
        
        # Verify map loads
        time.sleep(5)
        map_loaded = driver.execute_script("""
            return typeof map !== 'undefined' && map.loaded && map.loaded();
        """)
        
        driver.save_screenshot(str(screenshots_dir / "02_fixture_map_loaded.png"))
        print(f"📍 Map loaded: {map_loaded}")
        print("✅ App launches successfully with test data")
    
    def test_test_activity_visualization(self, mobile_driver):
        """Test that test activity is visible on map"""
        print("🧪 Testing test activity visualization...")
        
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        screenshots_dir = Path(__file__).parent / "screenshots"
        
        # Launch app and switch to WebView
        time.sleep(8)
        
        contexts = driver.contexts
        for context in contexts:
            if 'WEBVIEW' in context:
                driver.switch_to.context(context)
                break
        
        # Wait for map
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#map")))
        time.sleep(5)
        
        # Get map source information
        map_info = driver.execute_script("""
            if (typeof map !== 'undefined') {
                const style = map.getStyle();
                const sources = style.sources || {};
                
                return {
                    sources: Object.keys(sources),
                    runsVecExists: 'runsVec' in sources,
                    runsVecUrl: sources.runsVec ? sources.runsVec.url : null,
                    layers: (style.layers || []).map(l => ({
                        id: l.id,
                        type: l.type,
                        source: l.source
                    }))
                };
            }
            return null;
        """)
        
        print(f"🗺️ Map info: {map_info}")
        
        # Should have PMTiles source loaded
        assert map_info['runsVecExists'], "runsVec source should be loaded with test data"
        print(f"🔗 PMTiles URL: {map_info['runsVecUrl']}")
        
        # Pan to test activity location  
        test_lat = 39.4168
        test_lon = -77.4169
        zoom_level = 13  # Lower zoom to ensure PMTiles features are visible
        
        print(f"🗺️ Panning to test activity: {test_lat}, {test_lon}")
        
        driver.execute_script(f"""
            if (typeof map !== 'undefined') {{
                map.flyTo({{
                    center: [{test_lon}, {test_lat}],
                    zoom: {zoom_level},
                    duration: 2000
                }});
            }}
        """)
        
        # Wait for pan and data loading
        time.sleep(6)
        driver.save_screenshot(str(screenshots_dir / "03_fixture_test_activity_location.png"))
        
        # Query for features
        features_info = driver.execute_script("""
            if (typeof map !== 'undefined') {
                try {
                    const features = map.queryRenderedFeatures();
                    const sourceFeatures = map.querySourceFeatures('runsVec');
                    const lineFeatures = features.filter(f => 
                        f.geometry && f.geometry.type === 'LineString');
                    
                    return {
                        renderedTotal: features.length,
                        renderedLines: lineFeatures.length,
                        sourceTotal: sourceFeatures.length,
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
        
        print(f"🎯 Features: {features_info}")
        
        if features_info and not features_info.get('error'):
            print(f"📊 Rendered: {features_info['renderedTotal']}, Lines: {features_info['renderedLines']}")
            print(f"📂 Source features: {features_info['sourceTotal']}")
            
            # We should have rendered line features (test activity)
            assert features_info['renderedLines'] > 0, "Should have test activity line rendered on map"
            
            if features_info['sampleSource']:
                geom = features_info['sampleSource']['geometry']
                print(f"📍 Sample feature: {geom['type']} with {len(geom['coordinates'])} coordinates")
        
        # Final screenshot
        driver.save_screenshot(str(screenshots_dir / "04_fixture_activity_verification.png"))
        
        print("✅ Test activity visualization completed")
        print("📸 Screenshots saved - check for red activity line visualization")


if __name__ == '__main__':
    import unittest
    unittest.main()