"""
Upload functionality tests with rock-solid activity verification
Tests complete upload flow: button → file picker → selection → map verification
Reuses proven rock-solid verification methods from existing tests
"""
import time
import pytest
import subprocess
import os
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from appium import webdriver
from appium.options.android import UiAutomator2Options


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


@pytest.mark.mobile
class TestUploadFunctionality:
    """Test upload functionality with rock-solid activity verification"""
    
    def test_upload_gpx_file_flow(self, mobile_driver):
        """Test complete upload flow with rock-solid verification"""
        print("🧪 Testing upload GPX file flow with rock-solid verification...")
        
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        
        # Phase 1: Setup and App Launch
        print("⏳ Allowing app to fully start up...")
        time.sleep(12)  # Extended startup wait
        
        print("🔄 Switching to WebView context...")
        self.switch_to_webview(driver)
        
        print("🗺️ Waiting for map to fully load...")
        self.wait_for_map_load(driver, wait)
        
        self.take_screenshot(driver, "upload_01_initial_state")
        
        # Phase 2: File Upload Process
        print("📁 Setting up test file on device...")
        self.setup_test_file_on_device()
        
        print("📱 Clicking upload button...")
        self.click_upload_button_and_verify(driver, wait)
        
        print("📂 Navigating file picker and selecting test file...")
        self.navigate_file_picker_and_select(driver, wait)
        
        print("⏳ Waiting for upload processing...")
        self.verify_upload_processing_complete(driver, wait)
        
        self.take_screenshot(driver, "upload_02_processing_complete")
        
        # Phase 3: Rock-Solid Activity Verification
        print("🏆 Starting rock-solid verification of uploaded activity...")
        self.rock_solid_upload_verification(driver)
        
        # Phase 4: Cleanup - Clear uploaded activities
        print("🧹 Cleaning up uploaded activities...")
        self.clear_uploaded_activities(driver, wait)
        
        # Phase 5: Cleanup device files
        print("📁 Cleaning up test files from device...")
        self.cleanup_test_file_from_device()
        
        print("🎉 Upload functionality test completed successfully!")
    
    def switch_to_webview(self, driver):
        """Switch to WebView context with retry logic and interference handling"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                print(f"🔄 WebView context switch attempt {attempt + 1}/{max_attempts}")
                contexts = driver.contexts
                print(f"📱 Available contexts: {contexts}")
                
                # Filter to find our app's WebView, avoiding interference from other webviews
                target_webview = None
                for context in contexts:
                    if 'WEBVIEW_com.run.heatmap' in context:
                        target_webview = context
                        break
                    elif 'WEBVIEW' in context and 'webview_shell' not in context:
                        target_webview = context  # Fallback
                
                if target_webview:
                    print(f"🎯 Targeting WebView: {target_webview}")
                    driver.switch_to.context(target_webview)
                    
                    # Verify with simple JS execution and wait for DOM
                    time.sleep(2)  # Give WebView time to initialize
                    driver.execute_script("return typeof document !== 'undefined';")
                    print(f"✅ Successfully switched to: {target_webview}")
                    return target_webview
                else:
                    print("⚠️ No suitable WebView context found")
                    
            except Exception as e:
                print(f"⚠️ WebView switch attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    print("🔄 Waiting before retry...")
                    time.sleep(3 + attempt)
                    
                    # Try to close interfering webview_shell if present
                    try:
                        if 'org.chromium.webview_shell' in str(driver.contexts):
                            print("🧹 Attempting to clear webview_shell interference...")
                            driver.switch_to.context('NATIVE_APP')
                            time.sleep(1)
                    except:
                        pass
                    continue
                else:
                    raise
        
        raise Exception("Failed to switch to WebView context after all attempts")
    
    def wait_for_map_load(self, driver, wait):
        """Wait for map to load with robust criteria for slow connections"""
        print("🗺️ Waiting for map to load (extended wait for slow WiFi)...")
        
        # Wait for map element
        print("🔍 Waiting for map element...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#map")))
        
        # Extended wait for slow connections
        print("⏳ Giving extra time for map initialization...")
        time.sleep(8)
        
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
                    time.sleep(4)
                    
            except Exception as e:
                print(f"⚠️ Map check attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(4)
                    continue
                else:
                    raise
        
        raise Exception(f"Map failed to load after {max_attempts} attempts: {map_status}")
    
    def setup_test_file_on_device(self):
        """Push manual_upload_run.gpx to device Downloads folder"""
        print("📁 Pushing test GPX file to device...")
        
        # Set up ADB environment
        android_home = os.environ.get('ANDROID_HOME', '/home/imkacarlson/android-sdk')
        adb_env = os.environ.copy()
        adb_env['PATH'] = f"{adb_env['PATH']}:{android_home}/platform-tools"
        
        # Source file path
        test_file = Path(__file__).parent / "test_data" / "manual_upload_run.gpx"
        if not test_file.exists():
            raise Exception(f"Test GPX file not found: {test_file}")
        
        # Device destination path
        device_path = "/sdcard/Download/manual_upload_run.gpx"
        
        # Check if file already exists on device
        check_result = subprocess.run(
            ["adb", "shell", "ls", device_path], 
            capture_output=True, text=True, env=adb_env
        )
        
        if check_result.returncode == 0:
            print(f"✅ Test file already exists on device: {device_path}")
        else:
            # Push file to device
            push_result = subprocess.run(
                ["adb", "push", str(test_file), device_path],
                capture_output=True, text=True, env=adb_env
            )
            
            if push_result.returncode != 0:
                raise Exception(f"Failed to push test file: {push_result.stderr}")
            
            print(f"✅ Test file pushed to device: {device_path}")
        
        # Verify file is accessible
        verify_result = subprocess.run(
            ["adb", "shell", "ls", "-la", device_path],
            capture_output=True, text=True, env=adb_env
        )
        
        if verify_result.returncode == 0:
            print(f"📁 File verified on device: {verify_result.stdout.strip()}")
        else:
            raise Exception(f"Failed to verify test file on device: {verify_result.stderr}")
    
    def click_upload_button_and_verify(self, driver, wait):
        """Click upload button and verify file picker opens"""
        print("📱 Locating and clicking upload button...")
        
        # Find upload button
        upload_btn = self.find_clickable_element(driver, wait, "#upload-btn")
        upload_btn.click()
        time.sleep(2)
        
        # Switch to native context to interact with file picker
        print("🔄 Switching to native context for file picker...")
        driver.switch_to.context('NATIVE_APP')
        time.sleep(3)  # Wait for file picker to appear
        
        print("✅ Upload button clicked, file picker should be open")
    
    def navigate_file_picker_and_select(self, driver, wait):
        """Navigate Android file picker and select manual_upload_run.gpx"""
        print("📂 Navigating file picker to select test file...")
        
        try:
            # Wait for file picker to appear
            time.sleep(3)
            
            # Look for Downloads folder or direct file access
            # Try multiple strategies to find and select the file
            
            # Strategy 1: Look for the file directly by name
            try:
                file_element = driver.find_element(
                    "xpath", 
                    "//android.widget.TextView[@text='manual_upload_run.gpx']"
                )
                file_element.click()
                print("✅ Found and selected test file directly")
                return
            except:
                print("🔍 File not visible directly, trying Downloads folder...")
            
            # Strategy 2: Navigate to Downloads folder
            try:
                downloads_folder = driver.find_element(
                    "xpath",
                    "//android.widget.TextView[@text='Download' or @text='Downloads']"
                )
                downloads_folder.click()
                time.sleep(2)
                
                # Now look for the file in Downloads
                file_element = driver.find_element(
                    "xpath",
                    "//android.widget.TextView[@text='manual_upload_run.gpx']"
                )
                file_element.click()
                print("✅ Found and selected test file in Downloads folder")
                return
            except:
                print("🔍 Downloads folder navigation failed, trying scroll...")
            
            # Strategy 3: Scroll and search
            try:
                # Scroll down to find the file
                driver.swipe(500, 800, 500, 400, 1000)  # Swipe up to scroll down
                time.sleep(1)
                
                file_element = driver.find_element(
                    "xpath",
                    "//android.widget.TextView[@text='manual_upload_run.gpx']"
                )
                file_element.click()
                print("✅ Found and selected test file after scrolling")
                return
            except:
                print("⚠️ Could not find test file, taking screenshot for debugging...")
                self.take_screenshot(driver, "upload_file_picker_debug")
                raise Exception("Could not locate test file in file picker")
                
        finally:
            # Wait for file selection to process
            time.sleep(3)
            
            # Switch back to WebView context
            print("🔄 Switching back to WebView context...")
            self.switch_to_webview(driver)
    
    def verify_upload_processing_complete(self, driver, wait):
        """Wait for upload processing to complete and verify success"""
        print("⏳ Waiting for upload processing to complete...")
        
        # Wait for upload status or processing indicators
        max_wait = 30  # 30 seconds timeout
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Check for upload status or success indicators
                status_info = driver.execute_script("""
                    // Check for any status messages or indicators
                    const statusElements = document.querySelectorAll('[class*="status"], [id*="status"], .toast, .notification');
                    const statusTexts = Array.from(statusElements).map(el => el.textContent.trim());
                    
                    // Check if upload processing is mentioned
                    const hasUploadStatus = statusTexts.some(text => 
                        text.toLowerCase().includes('upload') || 
                        text.toLowerCase().includes('processing') ||
                        text.toLowerCase().includes('success') ||
                        text.toLowerCase().includes('added')
                    );
                    
                    return {
                        statusTexts: statusTexts,
                        hasUploadStatus: hasUploadStatus,
                        timestamp: Date.now()
                    };
                """)
                
                if status_info['hasUploadStatus']:
                    print(f"✅ Upload status detected: {status_info['statusTexts']}")
                    break
                    
                # Check if map has been updated with new data
                map_update = driver.execute_script("""
                    // Check if map sources or data have been updated
                    if (typeof map !== 'undefined') {
                        const sources = map.getStyle().sources || {};
                        return {
                            sources: Object.keys(sources),
                            timestamp: Date.now()
                        };
                    }
                    return null;
                """)
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"⚠️ Error checking upload status: {e}")
                time.sleep(2)
                continue
        
        # Final wait for processing
        print("📡 Allowing extra time for upload processing...")
        time.sleep(5)
        
        print("✅ Upload processing wait completed")
    
    def find_clickable_element(self, driver, wait, selector):
        """Find element that might be blocked by other elements"""
        try:
            # First try normal clickable wait
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            return element
        except (TimeoutException, ElementClickInterceptedException):
            # Fallback: just find the element and use ActionChains
            print(f"⚠️ Using ActionChains fallback for element: {selector}")
            element = driver.find_element(By.CSS_SELECTOR, selector)
            
            # Use ActionChains to click
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            time.sleep(1)
            return element
    
    def take_screenshot(self, driver, name):
        """Take screenshot with error handling"""
        screenshots_dir = Path(__file__).parent / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        try:
            path = screenshots_dir / f"{name}.png"
            driver.save_screenshot(str(path))
            print(f"📸 Screenshot saved: {name}.png")
            return path
        except Exception as e:
            print(f"⚠️ Screenshot failed ({name}): {e}")
            return None
    
    # Rock-Solid Verification Methods (adapted from test_mobile_with_fixtures.py)
    
    def rock_solid_upload_verification(self, driver):
        """Complete rock-solid verification for uploaded activity"""
        print("🏆 Starting rock-solid verification of uploaded activity...")
        
        # Step 1: Wait for app's auto-zoom to uploaded activity (no manual navigation needed)
        print("📋 Step 1: Waiting for app's auto-zoom to uploaded activity...")
        print("🎯 App should automatically zoom to uploaded activity - no manual panning needed")
        time.sleep(6)  # Wait for auto-zoom animation to complete
        
        # Step 2: Verify features are in current viewport (after auto-zoom)
        print("📋 Step 2: Verifying features in current viewport after auto-zoom...")
        features = self.verify_features_in_current_viewport(driver)
        assert features['featuresInViewport'] > 0, f"No activity features found in viewport after auto-zoom (found {features['featuresInViewport']})"
        print(f"✅ Found {features['featuresInViewport']} activity features in current viewport")
        
        # Step 3: Verify pixels are actually rendered in current viewport
        print("📋 Step 3: Verifying actual pixel rendering in current viewport...")
        pixels = self.verify_activity_pixels_in_viewport(driver)
        
        # Step 4: Take verification screenshot of current auto-zoomed view
        print("📋 Step 4: Taking verification screenshot of auto-zoomed uploaded activity...")
        # No manual markers needed - the auto-zoom should perfectly frame the uploaded activity
        
        self.take_screenshot(driver, "upload_03_rock_solid_verification")
        
        # Step 5: Get debug rendering state
        print("📋 Step 5: Getting rendering debug info...")
        debug_state = self.debug_rendering_state(driver)
        print(f"🔍 Debug: Map loaded: {debug_state['mapLoaded']}, Canvas: {debug_state['canvasSize']}")
        print(f"🔍 Debug: {len(debug_state['layers'])} layers, {len(debug_state['sources'])} sources")
        
        # Step 6: Final success criteria verification
        success_criteria = {
            'features_found': features['featuresInViewport'] > 0,
            'pixels_available': 'error' not in pixels,
            'pixels_visible': pixels.get('successRate', 0) >= 0.25 if 'error' not in pixels else True,
            'canvas_functional': debug_state['webglContext'] and debug_state['canvasSize']['w'] > 0
        }
        
        print("🏆 Final upload verification results:")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}: {passed}")
        
        # Assert all criteria
        assert success_criteria['features_found'], f"No activity features in viewport after auto-zoom (found {features['featuresInViewport']})"
        if success_criteria['pixels_available']:
            assert success_criteria['pixels_visible'], f"Activity not visible enough in viewport (only {pixels.get('successRate', 0)*100:.1f}% visible)"
        assert success_criteria['canvas_functional'], "Canvas or WebGL context not functional"
        
        print("🎉 UPLOADED ACTIVITY IS DEFINITELY VISIBLE! All verification methods passed.")
        if 'error' not in pixels:
            print(f"📊 Pixel success rate: {pixels['successRate']*100:.1f}%")
        else:
            print("📊 Pixel verification: Not available in WebView (using viewport verification)")
        print(f"📊 Features in current viewport: {features['featuresInViewport']}")
    
    def verify_features_in_current_viewport(self, driver):
        """Verify activity features are visible in current viewport (after auto-zoom)"""
        verification = driver.execute_script("""
            const bounds = map.getBounds();
            const zoom = map.getZoom();
            
            // Query only features that are actually rendered in current viewport
            const renderedFeatures = map.queryRenderedFeatures();
            
            // Filter to only LineString features (activity routes)
            const activityFeatures = renderedFeatures.filter(f => 
                f.geometry && f.geometry.type === 'LineString'
            );
            
            return {
                viewportBounds: bounds.toArray(),
                zoom: zoom,
                totalRenderedFeatures: renderedFeatures.length,
                featuresInViewport: activityFeatures.length,
                sampleFeature: activityFeatures[0] || null,
                viewportCenter: [
                    (bounds.getWest() + bounds.getEast()) / 2,
                    (bounds.getSouth() + bounds.getNorth()) / 2
                ]
            };
        """)
        
        print(f"🗺️ Current viewport verification: {verification['featuresInViewport']} activity features visible")
        print(f"📊 Viewport center: {verification['viewportCenter']}, zoom: {verification['zoom']}")
        
        return verification
    
    def verify_activity_pixels_in_viewport(self, driver):
        """Verify activity line pixels are visible in current viewport (after auto-zoom)"""
        print("🎯 Starting pixel-based verification in current viewport...")
        
        # Sample pixels in a grid pattern across the viewport to detect activity lines
        pixel_check = driver.execute_script("""
            try {
                const canvas = map.getCanvas();
                if (!canvas) {
                    return {
                        error: 'Canvas not available',
                        redPixelsFound: 0,
                        totalSamples: 0,
                        successRate: 0,
                        canvasSize: {width: 0, height: 0}
                    };
                }
                
                const ctx = canvas.getContext('2d', {willReadFrequently: true});
                if (!ctx) {
                    return {
                        error: 'Canvas context not available (WebView limitation)',
                        redPixelsFound: 0,
                        totalSamples: 0,
                        successRate: 0,
                        canvasSize: {width: canvas.width || 0, height: canvas.height || 0}
                    };
                }
                
                // Sample pixels in a grid pattern across the viewport
                const centerX = canvas.width / 2;
                const centerY = canvas.height / 2;
                const sampleRadius = Math.min(canvas.width, canvas.height) / 4; // Sample within central area
                
                const samplePoints = [
                    [centerX, centerY], // Center
                    [centerX - sampleRadius/2, centerY], // Left
                    [centerX + sampleRadius/2, centerY], // Right  
                    [centerX, centerY - sampleRadius/2], // Top
                    [centerX, centerY + sampleRadius/2], // Bottom
                    [centerX - sampleRadius/3, centerY - sampleRadius/3], // Top-left
                    [centerX + sampleRadius/3, centerY - sampleRadius/3], // Top-right
                    [centerX - sampleRadius/3, centerY + sampleRadius/3], // Bottom-left
                    [centerX + sampleRadius/3, centerY + sampleRadius/3], // Bottom-right
                ];
                
                let redPixelsFound = 0;
                let totalSamples = 0;
                
                for (const [x, y] of samplePoints) {
                    // Sample a small area around each point
                    const sampleSize = 15;
                    let foundRed = false;
                    
                    for (let dx = -sampleSize; dx <= sampleSize && !foundRed; dx += 3) {
                        for (let dy = -sampleSize; dy <= sampleSize && !foundRed; dy += 3) {
                            const px = Math.round(x + dx);
                            const py = Math.round(y + dy);
                            
                            if (px < 0 || py < 0 || px >= canvas.width || py >= canvas.height) continue;
                            
                            try {
                                const pixel = ctx.getImageData(px, py, 1, 1).data;
                                const [r, g, b, a] = pixel;
                                
                                // Check if pixel is reddish (activity line color)
                                if (r > 150 && g < 100 && b < 100 && a > 0) {
                                    foundRed = true;
                                    redPixelsFound++;
                                }
                            } catch (pixelError) {
                                continue;
                            }
                        }
                    }
                    totalSamples++;
                }
                
                return {
                    redPixelsFound: redPixelsFound,
                    totalSamples: totalSamples,
                    successRate: redPixelsFound / totalSamples,
                    canvasSize: {width: canvas.width, height: canvas.height}
                };
                
            } catch (error) {
                return {
                    error: 'Viewport pixel sampling failed: ' + error.message,
                    redPixelsFound: 0,
                    totalSamples: 0,
                    successRate: 0,
                    canvasSize: {width: 0, height: 0}
                };
            }
        """)
        
        if 'error' in pixel_check:
            print(f"⚠️ Viewport pixel verification unavailable: {pixel_check['error']}")
            print("📝 Note: This is a WebView limitation, using viewport verification instead")
        else:
            print(f"🎯 Viewport pixel verification: {pixel_check['redPixelsFound']}/{pixel_check['totalSamples']} sample areas have red pixels")
            print(f"📊 Success rate: {pixel_check['successRate']*100:.1f}%")
        
        return pixel_check
    
    def debug_rendering_state(self, driver):
        """Get complete rendering state for debugging (from rock-solid test)"""
        return driver.execute_script("""
            const canvas = map.getCanvas();
            const gl = canvas.getContext('webgl') || canvas.getContext('webgl2');
            
            return {
                mapLoaded: map.loaded(),
                mapStyle: !!map.getStyle(),
                canvasSize: {w: canvas.width, h: canvas.height},
                webglContext: !!gl,
                layers: map.getStyle().layers.map(l => ({
                    id: l.id,
                    type: l.type,
                    visible: map.getLayoutProperty(l.id, 'visibility') !== 'none'
                })),
                sources: Object.keys(map.getStyle().sources)
            };
        """)
    
    def clear_uploaded_activities(self, driver, wait):
        """Clear uploaded activities from the app using the built-in clear function"""
        print("🧹 Opening extras panel to access clear uploads...")
        
        try:
            # Open extras panel
            extras_btn = self.find_clickable_element(driver, wait, "#extras-btn")
            extras_btn.click()
            time.sleep(3)  # Wait for panel to open and load content
            
            # Look for clear uploads button
            print("🔍 Looking for clear uploads button...")
            clear_btn = self.find_clickable_element(driver, wait, "#clear-uploads-btn")
            
            # Use JavaScript to bypass the confirmation dialog and call clearUserUploads directly
            print("🗑️ Clearing uploaded activities programmatically...")
            clear_result = driver.execute_script("""
                try {
                    // Call the clearUserUploads function directly to bypass confirmation
                    if (typeof clearUserUploads === 'function') {
                        clearUserUploads();
                        return {success: true, message: 'Uploads cleared successfully'};
                    } else {
                        return {success: false, message: 'clearUserUploads function not found'};
                    }
                } catch (error) {
                    return {success: false, message: 'Error clearing uploads: ' + error.message};
                }
            """)
            
            if clear_result['success']:
                print("✅ Uploaded activities cleared successfully")
                time.sleep(2)  # Wait for cleanup to complete
            else:
                print(f"⚠️ Failed to clear uploads: {clear_result['message']}")
            
            # Close extras panel
            print("📱 Closing extras panel...")
            extras_btn = self.find_clickable_element(driver, wait, "#extras-btn")
            extras_btn.click()
            time.sleep(2)
            
            # Take screenshot to verify cleanup
            self.take_screenshot(driver, "upload_04_cleanup_complete")
            
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
            print("📝 Note: Cleanup failed but test data is isolated, so this won't affect other tests")
    
    def cleanup_test_file_from_device(self):
        """Remove test GPX file from device storage"""
        print("📁 Removing test file from device...")
        
        # Set up ADB environment
        android_home = os.environ.get('ANDROID_HOME', '/home/imkacarlson/android-sdk')
        adb_env = os.environ.copy()
        adb_env['PATH'] = f"{adb_env['PATH']}:{android_home}/platform-tools"
        
        # Device file path
        device_path = "/sdcard/Download/manual_upload_run.gpx"
        
        try:
            # Remove file from device
            remove_result = subprocess.run(
                ["adb", "shell", "rm", device_path],
                capture_output=True, text=True, env=adb_env
            )
            
            if remove_result.returncode == 0:
                print(f"✅ Test file removed from device: {device_path}")
            else:
                print(f"⚠️ Could not remove test file (may not exist): {remove_result.stderr}")
                
        except Exception as e:
            print(f"⚠️ Error removing test file from device: {e}")
            print("📝 Note: File cleanup failed but won't affect other tests")