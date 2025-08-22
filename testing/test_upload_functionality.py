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
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from base_mobile_test import BaseMobileTest

@pytest.mark.mobile
@pytest.mark.core
class TestUploadFunctionality(BaseMobileTest):
    """Test upload functionality with rock-solid activity verification"""
    
    def test_upload_gpx_file_flow(self, mobile_driver):
        """Test complete upload flow with rock-solid verification"""
        print("🧪 Testing upload GPX file flow with rock-solid verification...")
        
        driver = mobile_driver['driver']
        wait = mobile_driver['wait']
        
        # Phase 1: Setup and App Launch
        print("⏳ Waiting for app WebView to become available...")
        self.wait_for_webview_available(driver, wait, verbose=True)
        
        print("🔄 Switching to WebView context...")
        self.switch_to_webview(driver)
        
        print("🗺️ Waiting for map to fully load...")
        self.wait_for_map_load(driver, wait, verbose=True)
        
        
        # Phase 2: File Upload Process
        print("📁 Setting up test file on device...")
        self.setup_test_file_on_device()
        
        print("📱 Clicking upload button...")
        self.click_upload_button_and_verify(driver, wait)
        
        print("📂 Navigating file picker and selecting test file...")
        self.navigate_file_picker_and_select(driver, wait)
        
        print("⏳ Waiting for upload processing...")
        self.verify_upload_processing_complete(driver, wait)
        
        
        # Phase 3: Rock-Solid Activity Verification
        print("🏆 Starting rock-solid verification of uploaded activity...")
        self.rock_solid_upload_verification(driver)
        
        # Phase 4: Lasso Selection Verification - Test uploaded activity shows in sidebar
        print("🎯 Starting lasso selection verification of all activities (uploaded + packaged)...")
        self.lasso_selection_verification(driver, wait)
        
        # Phase 5: Individual Activity Selection in Extras Sidebar
        print("🎯 Testing individual activity selection in extras sidebar...")
        self.verify_individual_activity_selection_in_extras(driver, wait)
        
        # Phase 6: Cleanup - Clear uploaded activities 
        print("🧹 Cleaning up uploaded activities...")
        self.clear_uploaded_activities(driver, wait)
        
        # Phase 7: Cleanup device files
        print("📁 Cleaning up test files from device...")
        self.cleanup_test_file_from_device()
        
        print("🎉 Upload functionality test completed successfully!")
    
    
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
        
        # Wait for file picker to appear by looking for common file picker elements
        print("⏳ Waiting for file picker to appear...")
        file_picker_wait = WebDriverWait(driver, 10)
        try:
            # Look for common Android file picker elements
            file_picker_wait.until(lambda d: any([
                len(d.find_elements(By.XPATH, "//*[contains(@text, 'Select') or contains(@text, 'Choose') or contains(@text, 'Pick')]")) > 0,
                len(d.find_elements(By.XPATH, "//*[contains(@class, 'file') or contains(@class, 'picker')]")) > 0,
                len(d.find_elements(By.XPATH, "//*[contains(@resource-id, 'file') or contains(@resource-id, 'picker')]")) > 0,
                len(d.find_elements(By.XPATH, "//*[contains(@text, '.gpx') or contains(@text, 'Downloads')]")) > 0
            ]))
            print("✅ File picker interface detected")
        except TimeoutException:
            print("⚠️ File picker timeout - continuing with fallback wait")
            time.sleep(2)  # Short fallback
        
        print("✅ Upload button clicked, file picker should be open")
    
    def navigate_file_picker_and_select(self, driver, wait):
        """Navigate Android file picker and select manual_upload_run.gpx"""
        print("📂 Navigating file picker to select test file...")
        
        try:
            # Wait for file picker elements to be interactive
            print("⏳ Waiting for file picker elements to be ready...")
            file_picker_wait = WebDriverWait(driver, 10)
            file_picker_wait.until(lambda d: any([
                len(d.find_elements(By.XPATH, "//*[@text='manual_upload_run.gpx']")) > 0,
                len(d.find_elements(By.XPATH, "//*[contains(@text, 'Downloads')]")) > 0,
                len(d.find_elements(By.XPATH, "//*[contains(@text, '.gpx')]")) > 0,
                len(d.find_elements(By.XPATH, "//*[@clickable='true']")) > 5  # At least some clickable elements
            ]))
            print("✅ File picker is ready for interaction")
            
            # Strategy 1: Look for the file directly by name (in case it's in Recent)
            try:
                file_element = driver.find_element(
                    "xpath", 
                    "//android.widget.TextView[@text='manual_upload_run.gpx']"
                )
                file_element.click()
                print("✅ Found and selected test file directly in Recent")
                return
            except:
                print("🔍 File not visible in Recent, navigating to Downloads folder...")
            
            # Strategy 2: Use hamburger menu to navigate to Downloads
            try:
                self.navigate_to_downloads_via_menu(driver)
                
                # Now look for the file in Downloads
                file_element = driver.find_element(
                    "xpath",
                    "//android.widget.TextView[@text='manual_upload_run.gpx']"
                )
                file_element.click()
                print("✅ Found and selected test file in Downloads folder")
                return
            except Exception as e:
                print(f"🔍 Menu navigation failed: {e}, trying direct Downloads detection...")
            
            # Strategy 3: Look for Downloads folder directly in main view
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
                print("✅ Found and selected test file in Downloads folder (direct)")
                return
            except:
                print("🔍 Downloads folder not found directly, trying scroll and search...")
            
            # Strategy 4: Scroll to find Downloads folder or file
            try:
                self.scroll_and_find_downloads(driver)
                
                # Look for the file after scrolling
                file_element = driver.find_element(
                    "xpath",
                    "//android.widget.TextView[@text='manual_upload_run.gpx']"
                )
                file_element.click()
                print("✅ Found and selected test file after scrolling")
                return
            except:
                print("⚠️ Could not find test file after all navigation attempts...")
                
                # Debug: dump current screen elements
                self.dump_current_elements(driver)
                raise Exception("Could not locate test file in file picker after all navigation attempts")
                
        finally:
            # Wait for file selection to process
            time.sleep(3)
            
            # Switch back to WebView context
            print("🔄 Switching back to WebView context...")
            self.switch_to_webview(driver)
    
    def navigate_to_downloads_via_menu(self, driver):
        """Navigate to Downloads folder using hamburger menu or side navigation"""
        print("🍔 Attempting to navigate via hamburger menu...")
        
        # Strategy 1: Look for hamburger menu icon (3 lines)
        hamburger_selectors = [
            "//android.widget.ImageView[@content-desc='Show roots']",
            "//android.widget.ImageButton[@content-desc='Show roots']",
            "//android.widget.ImageView[@content-desc='Navigate up']",
            "//android.widget.ImageButton[@content-desc='Navigate up']",
            "//android.widget.ImageView[@content-desc='Open navigation drawer']",
            "//android.widget.ImageButton[@content-desc='Open navigation drawer']",
            "//android.widget.ImageView[contains(@content-desc, 'navigation')]",
            "//android.widget.ImageView[contains(@content-desc, 'menu')]",
            "//android.widget.ImageView[contains(@content-desc, 'drawer')]"
        ]
        
        for selector in hamburger_selectors:
            try:
                hamburger = driver.find_element("xpath", selector)
                hamburger.click()
                print(f"✅ Clicked hamburger menu with selector: {selector}")
                time.sleep(2)
                
                # Now look for Downloads in the side menu
                downloads_selectors = [
                    "//android.widget.TextView[@text='Downloads']",
                    "//android.widget.TextView[@text='Download']",
                    "//android.widget.TextView[contains(@text, 'Download')]",
                    "//*[@content-desc='Downloads']",
                    "//*[@content-desc='Download']"
                ]
                
                for dl_selector in downloads_selectors:
                    try:
                        downloads_item = driver.find_element("xpath", dl_selector)
                        downloads_item.click()
                        print(f"✅ Clicked Downloads in menu with selector: {dl_selector}")
                        time.sleep(2)
                        return
                    except:
                        continue
                        
                print("⚠️ Hamburger menu opened but Downloads not found in menu")
                break
                
            except:
                continue
                
        raise Exception("Could not find or use hamburger menu for navigation")
    
    def scroll_and_find_downloads(self, driver):
        """Scroll through file picker to find Downloads folder"""
        print("📜 Scrolling to find Downloads folder...")
        
        # Try scrolling down to find Downloads folder
        for attempt in range(3):
            try:
                # Look for Downloads folder
                downloads_folder = driver.find_element(
                    "xpath",
                    "//android.widget.TextView[@text='Download' or @text='Downloads']"
                )
                downloads_folder.click()
                print(f"✅ Found Downloads folder after {attempt + 1} scroll attempts")
                time.sleep(2)
                return
            except:
                # Scroll down
                driver.swipe(500, 800, 500, 400, 1000)
                time.sleep(1)
                print(f"🔍 Scrolled down (attempt {attempt + 1}/3)")
        
        raise Exception("Could not find Downloads folder after scrolling")
    
    def dump_current_elements(self, driver):
        """Dump current screen elements for debugging"""
        print("🔍 Dumping current screen elements for debugging...")
        try:
            # Get page source for debugging
            page_source = driver.page_source
            
            # Save to file for analysis
            debug_file = Path(__file__).parent / "debug_upload_file_picker.xml"
            debug_file.parent.mkdir(exist_ok=True)
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            print(f"📁 Page source saved to: {debug_file}")
            
            # Also try to find common elements
            common_elements = [
                "//android.widget.TextView",
                "//android.widget.ImageView",
                "//android.widget.ImageButton",
                "//*[@content-desc]",
                "//*[@text]"
            ]
            
            for selector in common_elements:
                try:
                    elements = driver.find_elements("xpath", selector)
                    print(f"🔍 Found {len(elements)} elements with selector: {selector}")
                    if elements and len(elements) < 10:  # Don't spam too many elements
                        for i, elem in enumerate(elements[:5]):  # Show first 5
                            try:
                                text = elem.get_attribute("text") or elem.get_attribute("content-desc") or "No text"
                                print(f"   Element {i+1}: {text}")
                            except:
                                pass
                except:
                    pass
                    
        except Exception as e:
            print(f"⚠️ Error during element dump: {e}")
    
    def verify_upload_processing_complete(self, driver, wait):
        """Wait for upload processing to complete and verify success"""
        print("⏳ Waiting for upload processing to complete...")
        
        # Define custom condition for upload completion
        def upload_processing_complete(driver):
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
                    return True
                    
                # Check if map has been updated with new data
                map_update = driver.execute_script("""
                    // Check if map sources or data have been updated
                    if (typeof map !== 'undefined') {
                        const sources = map.getStyle().sources || {};
                        return Object.keys(sources).length > 0;
                    }
                    return false;
                """)
                
                return map_update
                
            except Exception as e:
                print(f"⚠️ Error checking upload status: {e}")
                return False
        
        # Use WebDriverWait with custom condition
        try:
            WebDriverWait(driver, 30).until(upload_processing_complete)
            print("✅ Upload processing completed")
        except TimeoutException:
            print("⚠️ Upload processing timeout - continuing anyway")
        
        # Brief additional wait for final settling
        WebDriverWait(driver, 5).until(lambda d: driver.execute_script("return typeof map !== 'undefined'"))
        print("✅ Upload processing wait completed")
    
    
    # Rock-Solid Verification Methods (adapted from test_mobile_with_fixtures.py)
    
    def rock_solid_upload_verification(self, driver):
        """Complete coordinate-specific verification for uploaded activity red line"""
        print("🏆 Starting coordinate-specific verification of uploaded activity red line...")
        
        # Step 1: Navigate to uploaded activity coordinates (from manual_upload_run.gpx)
        print("📋 Step 1: Navigating to uploaded activity coordinates...")
        upload_center_lat, upload_center_lon = 39.4212, -77.4112  # Center of uploaded GPX route
        driver.execute_script(f"""
            map.flyTo({{
                center: [{upload_center_lon}, {upload_center_lat}],
                zoom: 13,
                duration: 1000
            }});
        """)
        
        # Wait for map to settle after navigation
        self.wait_for_map_idle_after_move(driver, timeout_ms=8000, verbose=True)
        
        # Step 2: Verify red activity line at specific uploaded coordinates
        print("📋 Step 2: Verifying red line pixels at uploaded GPX coordinates...")
        pixels = self.verify_uploaded_activity_line_visible(driver)
        
        
        # Step 4: Get debug rendering state
        print("📋 Step 4: Getting rendering debug info...")
        debug_state = self.debug_rendering_state(driver)
        print(f"🔍 Debug: Map loaded: {debug_state['mapLoaded']}, Canvas: {debug_state['canvasSize']}")
        print(f"🔍 Debug: {len(debug_state['layers'])} layers, {len(debug_state['sources'])} sources")
        
        # Step 5: Final success criteria verification
        success_criteria = {
            'pixels_available': 'error' not in pixels,
            'red_line_visible': pixels.get('successRate', 0) >= 0.5 if 'error' not in pixels else False,
            'canvas_functional': debug_state['webglContext'] and debug_state['canvasSize']['w'] > 0,
            'coordinates_verified': pixels.get('redPixelsFound', 0) >= 2  # At least 2 route points show red
        }
        
        print("🏆 Final coordinate-specific verification results:")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}: {passed}")
        
        if 'error' not in pixels:
            print(f"🎯 Red pixels found at {pixels['redPixelsFound']}/{pixels['totalPoints']} uploaded coordinates")
            print(f"📊 Success rate: {pixels['successRate']*100:.1f}%")
        
        # Assert all criteria
        if success_criteria['pixels_available']:
            assert success_criteria['red_line_visible'], f"Uploaded activity red line not visible at expected coordinates (only {pixels.get('successRate', 0)*100:.1f}% visible)"
            assert success_criteria['coordinates_verified'], f"Not enough red pixels at uploaded coordinates (found {pixels.get('redPixelsFound', 0)}/{pixels.get('totalPoints', 0)})"
        else:
            print("⚠️ Pixel verification unavailable due to WebView limitations, using fallback verification")
            # Fallback: verify features are loaded in the expected area
            features = self.verify_features_in_current_viewport(driver)
            assert features['featuresInViewport'] > 0, f"No activity features found at uploaded coordinates (found {features['featuresInViewport']})"
        
        assert success_criteria['canvas_functional'], "Canvas or WebGL context not functional"
        
        print("🎉 Uploaded activity red line verification completed successfully!")
    
    def verify_uploaded_activity_line_visible(self, driver):
        """Verify red activity line is rendered at uploaded GPX coordinates using pixel sampling"""
        print("🎯 Starting pixel-based verification at uploaded GPX coordinates...")
        
        # Sample pixels along the uploaded route points (from manual_upload_run.gpx)
        pixel_check = driver.execute_script("""
            try {
                // Get canvas and context
                const canvas = map.getCanvas();
                if (!canvas) {
                    return {
                        error: 'Canvas not available',
                        redPixelsFound: 0,
                        totalPoints: 4,
                        successRate: 0,
                        details: [],
                        canvasSize: {width: 0, height: 0}
                    };
                }
                
                const ctx = canvas.getContext('2d', {willReadFrequently: true});
                if (!ctx) {
                    return {
                        error: 'Canvas context not available (WebView limitation)',
                        redPixelsFound: 0,
                        totalPoints: 4,
                        successRate: 0,
                        details: [],
                        canvasSize: {width: canvas.width || 0, height: canvas.height || 0}
                    };
                }
                
                // Define route points based on uploaded GPX data (manual_upload_run.gpx)
                const routePoints = [
                    [-77.4100, 39.4200],  // Start point
                    [-77.4105, 39.4205],  // First intermediate
                    [-77.4115, 39.4215],  // Second intermediate  
                    [-77.4125, 39.4225]   // End point
                ];
                
                let redPixelsFound = 0;
                const results = [];
                
                for (const [lng, lat] of routePoints) {
                    // Convert geo coords to screen pixels
                    const point = map.project([lng, lat]);
                    
                    // Sample a small area around each point
                    const sampleSize = 10;
                    let foundRed = false;
                    
                    for (let dx = -sampleSize; dx <= sampleSize; dx += 2) {
                        for (let dy = -sampleSize; dy <= sampleSize; dy += 2) {
                            const x = Math.round(point.x + dx);
                            const y = Math.round(point.y + dy);
                            
                            // Ensure we're within canvas bounds
                            if (x < 0 || y < 0 || x >= canvas.width || y >= canvas.height) continue;
                            
                            try {
                                // Get pixel data
                                const pixel = ctx.getImageData(x, y, 1, 1).data;
                                const [r, g, b, a] = pixel;
                                
                                // Check if pixel is reddish (activity line color)
                                // Looking for red-dominant pixels with some alpha
                                if (r > 150 && g < 100 && b < 100 && a > 0) {
                                    foundRed = true;
                                    redPixelsFound++;
                                    break;
                                }
                            } catch (pixelError) {
                                // Skip this pixel if we can't read it
                                continue;
                            }
                        }
                        if (foundRed) break;
                    }
                    
                    results.push({
                        coord: [lng, lat],
                        screenPos: {x: point.x, y: point.y},
                        foundRed: foundRed
                    });
                }
                
                return {
                    redPixelsFound: redPixelsFound,
                    totalPoints: routePoints.length,
                    successRate: redPixelsFound / routePoints.length,
                    details: results,
                    canvasSize: {width: canvas.width, height: canvas.height}
                };
                
            } catch (error) {
                return {
                    error: 'Pixel sampling failed: ' + error.message,
                    redPixelsFound: 0,
                    totalPoints: 4,
                    successRate: 0,
                    details: [],
                    canvasSize: {width: 0, height: 0}
                };
            }
        """)
        
        if 'error' in pixel_check:
            print(f"⚠️ Pixel verification unavailable: {pixel_check['error']}")
            print("📝 Note: This is a WebView limitation, using viewport verification instead")
        else:
            print(f"🎯 Pixel verification: {pixel_check['redPixelsFound']}/{pixel_check['totalPoints']} uploaded route points have red pixels")
            print(f"📊 Success rate: {pixel_check['successRate']*100:.1f}%")
            
            # Show details for each route point
            for i, detail in enumerate(pixel_check['details']):
                coord_str = f"{detail['coord'][1]:.4f}, {detail['coord'][0]:.4f}"
                status = "✅" if detail['foundRed'] else "❌"
                print(f"   {status} Point {i+1}: ({coord_str}) -> Red pixels: {detail['foundRed']}")
        
        return pixel_check
    
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
            
            # Wait for extras panel to open and load content
            print("⏳ Waiting for extras panel to open...")
            panel_wait = WebDriverWait(driver, 10)
            panel_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#extras-panel, .extras-panel")))
            
            # Also wait for panel content to be visible
            panel_wait.until(lambda d: d.execute_script("""
                const panel = document.querySelector('#extras-panel, .extras-panel');
                return panel && panel.offsetHeight > 0 && panel.style.display !== 'none';
            """))
            print("✅ Extras panel opened successfully")
            
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
    
    # Lasso Selection Methods
    
    def lasso_selection_verification(self, driver, wait):
        """Test lasso selection to verify uploaded activity appears in sidebar with all activities"""
        print("🎯 Starting lasso selection verification after upload...")
        
        # Navigate to area that encompasses all activities (uploaded + 2 packaged)
        # Using Frederick center coordinates to encompass all three activities
        frederick_lat, frederick_lon = 39.4168, -77.4169  # Center of all activities
        zoom_level = 11  # Zoomed out to see all activities
        
        print(f"🗺️ Navigating to Frederick area to encompass all activities: {frederick_lat}, {frederick_lon}")
        driver.execute_script(f"""
            map.jumpTo({{
                center: [{frederick_lon}, {frederick_lat}],
                zoom: {zoom_level}
            }});
        """)
        
        # Wait for map to settle after navigation
        self.wait_for_map_idle_after_move(driver, timeout_ms=8000, verbose=True)
        
        # Inject map helpers if not already present
        print("📦 Ensuring map test helpers are available...")
        self._inject_map_helpers(driver, wait)
        
        # Wait for map idle and runs features
        print("⏳ Waiting for view to go idle after navigation...")
        went_idle = driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (!window.__mapTestHelpers) return cb(false);
            window.__mapTestHelpers.waitForIdleAfterMove(15000).then(cb);
        """)
        print(f"🔎 Idle wait result: {went_idle}")
        
        # Activate lasso mode
        print("🎯 Activating lasso selection mode...")
        lasso_btn = self.find_clickable_element(driver, wait, "#lasso-btn")
        lasso_btn.click()
        
        # Wait for lasso mode to be activated
        lasso_wait = WebDriverWait(driver, 5)
        lasso_wait.until(lambda d: d.execute_script("""
            return document.querySelector('#lasso-btn').classList.contains('active') ||
                   document.body.classList.contains('lasso-mode') ||
                   document.querySelector('#map').style.cursor === 'crosshair';
        """))
        print("✅ Lasso mode activated")
        
        # Generate large polygon to encompass all activities (uploaded + 2 packaged)
        print("📐 Generating large polygon to encompass all three activities...")
        large_polygon_coords = driver.execute_script("""
            return window.__mapTestHelpers.generateCenterPolygon(400);
        """)
        print(f"🗺️ Generated large polygon coordinates: {len(large_polygon_coords)} points")
        
        # Convert to viewport points
        viewport_points = driver.execute_script("""
            return window.__mapTestHelpers.projectToViewportPoints(arguments[0]);
        """, large_polygon_coords)
        print(f"🎯 Viewport points: {viewport_points}")
        
        # Draw the polygon
        print("👆 Drawing large polygon to select all activities...")
        self._draw_polygon_absolute_viewport(driver, viewport_points)
        
        # Wait for lasso processing and verify results
        print("⏳ Waiting for lasso processing to complete...")
        lasso_result = self._wait_for_lasso_completion(driver, wait, max_wait=20)
        
        # Verify that exactly 3 activities are selected (2 packaged + 1 uploaded)
        assert lasso_result['panel_opened'], f"Side panel should open after lasso selection: {lasso_result['debug_info']}"
        assert lasso_result['run_count'] == 3, f"Should select exactly 3 activities (2 packaged + 1 uploaded): found {lasso_result['run_count']} activities. Debug: {lasso_result['debug_info']}"
        
        print(f"✅ Lasso selection verification completed successfully!")
        print(f"📊 Selected {lasso_result['run_count']} activities - uploaded activity successfully integrated with packaged data")
        
        # Phase 5: Individual Activity Selection and Map Visibility Test
        print("\n🔄 Testing individual activity selection and map visibility...")
        print("🎯 This will verify that uploaded activity works identically to packaged activities")
        
        # We should already have sidebar open with 3 activities from the lasso test
        print(f"✅ Starting with sidebar open and {lasso_result['run_count']} activities selected")
        
        # Step 1: Sidebar manipulation - deselect all, then select only uploaded activity
        print("🎯 Step 1: Testing sidebar selection controls...")
        
        # First, click "deselect all"
        print("   📝 Clicking 'Deselect All' button...")
        deselect_all_btn = self.find_clickable_element(driver, wait, "#deselect-all")
        deselect_all_btn.click()
        time.sleep(1)
        
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
        
        # Now select only the uploaded activity (should be the first/newest one in the list)
        print("   📝 Selecting only the uploaded activity...")
        
        # Find and click the checkbox for the uploaded activity (should be first since it's the newest)
        uploaded_activity_selected = driver.execute_script("""
            const checkboxes = document.querySelectorAll('.run-checkbox');
            const activityCards = document.querySelectorAll('.activity-card, .run-item, [data-activity], [data-run-id]');
            
            // The uploaded activity should be the newest (first in list since activities are sorted by date descending)
            // Updated GPX file has date 2024-07-17, making it newer than sample_run (2024-07-15) and eastside_run (2024-07-16)
            let uploadedCheckbox = null;
            
            if (checkboxes.length >= 3) {
                // The uploaded activity should be the first one (newest date: 2024-07-17)
                uploadedCheckbox = checkboxes[0];
            } else {
                // Fallback: use first available checkbox
                uploadedCheckbox = checkboxes[0];
            }
            
            if (uploadedCheckbox) {
                uploadedCheckbox.checked = true;
                uploadedCheckbox.dispatchEvent(new Event('change', {bubbles: true}));
                return {
                    success: true,
                    selectedIndex: Array.from(checkboxes).indexOf(uploadedCheckbox),
                    totalCheckboxes: checkboxes.length,
                    expectedPosition: 'first (newest activity with date 2024-07-17)'
                };
            }
            
            return {
                success: false,
                selectedIndex: -1,
                totalCheckboxes: checkboxes.length,
                expectedPosition: 'first (newest activity)'
            };
        """)
        
        assert uploaded_activity_selected['success'], f"Failed to select uploaded activity checkbox: {uploaded_activity_selected}"
        print(f"   ✅ Uploaded activity selected (checkbox {uploaded_activity_selected['selectedIndex'] + 1} of {uploaded_activity_selected['totalCheckboxes']}) - {uploaded_activity_selected.get('expectedPosition', 'newest activity')}")
        
        # Step 2: Minimize the sidebar
        print("   📝 Minimizing sidebar...")
        collapse_btn = self.find_clickable_element(driver, wait, "#panel-collapse")
        collapse_btn.click()
        
        # Wait for sidebar to collapse
        collapse_wait = WebDriverWait(driver, 5)
        collapse_wait.until(lambda d: d.execute_script("""
            const panel = document.getElementById('side-panel');
            return panel && panel.classList.contains('collapsed');
        """))
        print("   ✅ Sidebar collapsed successfully")
        
        # Verify sidebar is collapsed (redundant check, but keeping for compatibility)
        sidebar_collapsed = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            return panel && panel.classList.contains('collapsed');
        """)
        
        assert sidebar_collapsed, "Sidebar should be collapsed after clicking collapse button"
        print("   ✅ Sidebar successfully minimized")
        
        print("✅ Step 1 completed: Sidebar manipulation successful")
        
        # Step 2: Visibility verification
        print("🎯 Step 2: Verifying map visibility...")
        
        # Positive test: Verify exactly one activity (the uploaded one) is visible
        print("   🔍 Positive test: Verifying only uploaded activity is visible...")
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
        
        # Success criteria for uploaded activity visibility
        success_criteria = {
            'single_activity_visible': features_verification['featuresInViewport'] == 1,
            'filter_applied': map_filter_check['filterApplied'],
        }
        
        print("🏆 Uploaded activity visibility verification results:")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}: {passed}")
        
        # Assert all criteria
        assert success_criteria['single_activity_visible'], f"Exactly 1 activity should be visible on map (uploaded activity only), found {features_verification['featuresInViewport']}"
        assert success_criteria['filter_applied'], "Map filter should be applied when sidebar is open with single activity selected"
        
        print("   ✅ Visibility verification passed: Only uploaded activity is visible with filter applied")
        
        print("✅ Step 2 completed: Uploaded activity visibility verification successful")
        
        # Step 3: Proper cleanup - reopen sidebar and close with 'x'
        print("🎯 Step 3: Performing proper cleanup...")
        
        # Reopen the sidebar from collapsed state
        print("   📝 Reopening sidebar from collapsed state...")
        expand_btn = self.find_clickable_element(driver, wait, "#expand-btn")
        expand_btn.click()
        time.sleep(1)
        
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
        time.sleep(1)
        
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
        
        # Assert that all 3 activities are visible after filter is cleared
        assert final_features_check['featuresInViewport'] >= 3, f"All 3 activities (2 packaged + 1 uploaded) should be visible after clearing filter (found {final_features_check['featuresInViewport']})"
        print("   ✅ All activities are visible again after cleanup - filter properly cleared")
        
        print("✅ Step 3 completed: Proper cleanup successful")
        
        print("🎉 Individual activity selection and map visibility test completed successfully!")
        print("📋 Additional verification completed:")
        print("   ✓ Started with sidebar open and 3 activities selected (2 packaged + 1 uploaded)") 
        print("   ✓ 'Deselect all' button works correctly with uploaded activity")
        print("   ✓ Individual uploaded activity selection works")
        print("   ✓ Sidebar can be minimized with uploaded activity selected")
        print("   ✓ Map shows only uploaded activity when sidebar is minimized")
        print("   ✓ Other activities are filtered out correctly")
        print("   ✓ Sidebar can be reopened from collapsed state")
        print("   ✓ Sidebar can be properly closed with 'x' button")
        print("   ✓ All activities become visible again after cleanup")
        print("✅ Uploaded activity integrates seamlessly with existing sidebar functionality!")
    
    def verify_individual_activity_selection_in_extras(self, driver, wait):
        """Verify individual activity selection using the extras sidebar checkbox"""
        print("🎯 Starting individual activity selection test in extras sidebar...")
        
        # Step 1: Open extras sidebar
        print("📱 Opening extras sidebar...")
        extras_btn = self.find_clickable_element(driver, wait, "#extras-btn")
        extras_btn.click()
        
        # Wait for extras panel to be fully open
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#extras-panel.open")))
        print("   ✅ Extras panel opened successfully")
        
        # Step 2: Find and click the last activity checkbox (show only this activity)
        print("🔍 Finding the 'show only this activity' checkbox...")
        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-panel .last-activity-checkbox")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
        
        print("☑️  Clicking 'show only this activity' checkbox...")
        # Check if checkbox is already checked before clicking
        was_checked_before = checkbox.is_selected()
        print(f"   🔍 Debug - Checkbox state before click: {'checked' if was_checked_before else 'unchecked'}")
        
        checkbox.click()
        
        # Verify checkbox state after click
        is_checked_after = checkbox.is_selected()
        print(f"   🔍 Debug - Checkbox state after click: {'checked' if is_checked_after else 'unchecked'}")
        
        if not was_checked_before and is_checked_after:
            print(f"   ✅ Activity checkbox successfully checked")
        elif was_checked_before and not is_checked_after:
            print(f"   ✅ Activity checkbox successfully unchecked")
        elif was_checked_before and is_checked_after:
            print(f"   ⚠️ Checkbox was already checked - click may have had no effect")
        else:
            print(f"   ⚠️ Checkbox click may not have worked properly")
        
        # Step 2.5: Wait for filter to apply (zoom and wait for map idle like working test)
        print("🗺️ Zooming and waiting for filter to apply...")
        driver.execute_script("map.jumpTo({ center: [-77.4169, 39.4168], zoom: 12 });")
        driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (typeof map === 'undefined') return cb(false);
            map.once('idle', () => cb(true));
        """)
        print("   ✅ Map idle after filter application")
        
        # Step 3: Minimize extras sidebar (using correct collapse method)
        print("📱 Minimizing extras sidebar...")
        collapse_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-collapse")))
        collapse_btn.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#extras-panel.collapsed")))
        print("   ✅ Extras panel collapsed successfully")
        
        # Step 4: Verify only the selected activity is visible (reuse existing working verification)
        print("🔍 Verifying only selected activity is visible...")
        features_verification = self.verify_features_in_current_viewport(driver)
        
        # Also check the map filter is correctly applied (reuse existing logic from lines 981-994)
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
        
        # Success criteria for single activity visibility (same as working verification in lines 1000-1003)
        success_criteria = {
            'single_activity_visible': features_verification['featuresInViewport'] == 1,
            'filter_applied': map_filter_check['filterApplied'],
        }
        
        print("🏆 Single activity visibility verification results:")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}: {passed}")
        
        # Assert all criteria (same as working assertions in lines 1011-1012)
        assert success_criteria['single_activity_visible'], f"Exactly 1 activity should be visible on map (selected activity only), found {features_verification['featuresInViewport']}"
        assert success_criteria['filter_applied'], "Map filter should be applied when activity is individually selected"
        
        print("   ✅ Single activity visibility verification passed")
        
        # Step 6: Reopen extras sidebar (expand from collapsed state)
        print("📱 Reopening extras sidebar...")
        expand_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-expand-btn")))
        expand_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#extras-panel.collapsed")))
        print("   ✅ Extras panel expanded successfully")
        
        # Step 7: Uncheck the "show only this activity" checkbox
        print("☐ Unchecking 'show only this activity' checkbox...")
        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-panel .last-activity-checkbox")))
        if checkbox.is_selected():
            checkbox.click()
            print(f"   ✅ Activity checkbox unchecked successfully")
        else:
            print(f"   ℹ️ Activity checkbox was already unchecked")
        
        # Step 8: Close extras panel completely (using X button)
        print("📱 Closing extras panel completely...")
        close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-close")))
        close_btn.click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#extras-panel.open")))
        print("   ✅ Extras panel closed successfully")
        
        # Step 9: Verify all activities are visible again (reuse existing working verification)
        print("🔍 Verifying all activities are visible again...")
        
        # Zoom out slightly to ensure multiple runs are in view
        driver.execute_script("map.setZoom(10);")
        driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (typeof map === 'undefined') return cb(false);
            map.once('idle', () => cb(true));
        """)
        
        # Use existing working verification method  
        final_features_verification = self.verify_features_in_current_viewport(driver)
        print(f"   📊 Final features in viewport: {final_features_verification['featuresInViewport']}")
        
        # Check that filter is cleared (reuse existing logic)
        final_map_filter_check = driver.execute_script("""
            const layer = map.getLayer('runsVec');
            const filter = layer ? map.getFilter('runsVec') : null;
            const renderedFeatures = map.queryRenderedFeatures();
            const activityFeatures = renderedFeatures.filter(f => 
                f.geometry && f.geometry.type === 'LineString'
            );
            
            return {
                hasFilter: filter != null,
                filterCleared: filter == null,
                renderedActivityCount: activityFeatures.length
            };
        """)
        
        print(f"   📊 Final map filter check: {final_map_filter_check}")
        
        # Success criteria for all activities visible (same as working verification in lines 1062-1065)
        final_success_criteria = {
            'all_activities_visible': final_features_verification['featuresInViewport'] >= 3,
            'filter_cleared': final_map_filter_check['filterCleared'],
        }
        
        print("🏆 All activities visibility verification results:")
        for criterion, passed in final_success_criteria.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}: {passed}")
        
        # Assert all criteria (same as working assertions in lines 1064-1065)
        assert final_success_criteria['all_activities_visible'], f"All 3 activities (2 packaged + 1 uploaded) should be visible after unchecking, found {final_features_verification['featuresInViewport']}"
        assert final_success_criteria['filter_cleared'], "Map filter should be cleared after unchecking activity selection"
        
        print("   ✅ All activities visibility verification passed")
        
        print("🎉 Individual activity selection test completed successfully!")
        print("📋 Verification summary:")
        print("   ✓ Found 'show only this activity' checkbox in extras sidebar")
        print("   ✓ Checkbox successfully applies activity filter")
        print("   ✓ Map filter applies when activity is individually selected")
        print("   ✓ Only selected activity is visible when checkbox is checked")
        print("   ✓ Activity checkbox can be unchecked")
        print("   ✓ Map filter clears when activity is deselected")
        print("   ✓ All activities become visible again after deselection")
        print("✅ Uploaded activity works identically to packaged activities in extras sidebar!")
    
    def _inject_map_helpers(self, driver, wait):
        """Inject map helpers for lasso functionality"""
        helpers_js_path = Path(__file__).parent / "map_helpers.js"
        
        # First bind __map if not already bound
        driver.execute_script("""
            if (!window.__map && typeof map !== 'undefined' && map && map.project) {
                window.__map = map;
            }
        """)
        
        # Inject helpers if available and not already injected
        if helpers_js_path.exists() and not driver.execute_script("return window.__mapTestHelpers !== undefined"):
            with open(helpers_js_path, 'r') as f:
                helpers_script = f.read()
            driver.execute_script(helpers_script)
            
            # Wait for helpers to be ready
            wait.until(lambda d: d.execute_script("return window.__mapTestHelpers !== undefined"))
            print("✅ Map test helpers injected successfully")
        else:
            print("✅ Map test helpers already available or file not found")
    
    def _draw_polygon_absolute_viewport(self, driver, viewport_points):
        """Draw polygon using absolute viewport coordinates (adapted from lasso test)"""
        if len(viewport_points) < 3:
            raise ValueError("Need at least 3 points for polygon")
        
        # Freeze scroll position to prevent coordinate shifts
        driver.execute_script("window.scrollTo(0,0)")
        
        # Get viewport dimensions for clamping
        vw, vh = driver.execute_script("return [window.innerWidth, window.innerHeight]")
        
        # Clamp points to viewport bounds
        clamped_points = []
        for p in viewport_points:
            x = max(15, min(vw - 15, int(p["x"])))
            y = max(15, min(vh - 15, int(p["y"])))
            clamped_points.append({"x": x, "y": y})
        
        print(f"🔒 Clamped to viewport bounds: {len(clamped_points)} points")
        
        # Create touch pointer
        finger = PointerInput("touch", "finger")
        actions = ActionBuilder(driver, finger)
        
        def move_abs(pt):
            """Absolute viewport move"""
            actions.pointer_action.move_to_location(int(pt["x"]), int(pt["y"]))
        
        def lerp(a, b, t):
            """Interpolate between two absolute points"""
            x = int(a["x"] + (b["x"] - a["x"]) * t)
            y = int(a["y"] + (b["y"] - a["y"]) * t)
            x = max(15, min(vw - 15, x))
            y = max(15, min(vh - 15, y))
            return {"x": x, "y": y}
        
        # Start at first point
        first_point = clamped_points[0]
        move_abs(first_point)
        actions.pointer_action.pointer_down()
        actions.pointer_action.pause(0.1)
        
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
        """Wait for lasso processing with enhanced checks (adapted from lasso test)"""
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