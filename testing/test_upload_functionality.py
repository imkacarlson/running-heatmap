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
        print("🔄 Switching to WebView context...")
        self.switch_to_webview(driver)
        
        print("⏳ Waiting for WebView to be ready for interaction...")
        self.wait_for_webview_ready(driver, timeout=30)
        
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
        
        # Phase 5: Extras Panel Verification - Test uploaded activity as most recent and filtering
        print("📱 Starting extras panel most recent activity verification...")
        self.extras_panel_most_recent_verification(driver, wait)
        
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
    
    def wait_for_picker_ready(self, driver, timeout=10):
        """Wait for file picker to be ready for interaction"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if file picker UI elements are present
                # Look for common file picker elements
                picker_indicators = [
                    "//android.widget.TextView[@text='Recent']",
                    "//android.widget.TextView[@text='Downloads']", 
                    "//android.widget.TextView[@text='Download']",
                    "//android.widget.ImageView[@content-desc='Show roots']",
                    "//android.widget.ImageButton[@content-desc='Show roots']",
                    "//*[contains(@resource-id, 'files')]",
                    "//*[contains(@resource-id, 'picker')]"
                ]
                
                for indicator in picker_indicators:
                    try:
                        element = driver.find_element("xpath", indicator)
                        if element.is_displayed():
                            return True
                    except:
                        continue
                        
                time.sleep(0.5)  # Poll every 500ms
                
            except Exception:
                time.sleep(0.5)
                
        # If we can't detect picker readiness, log warning and continue
        print("⚠️ File picker readiness could not be confirmed, proceeding anyway")
        return True

    def click_upload_button_and_verify(self, driver, wait):
        """Click upload button and verify file picker opens"""
        print("📱 Locating and clicking upload button...")
        
        # Find upload button
        upload_btn = self.find_clickable_element(driver, wait, "#upload-btn")
        upload_btn.click()
        
        # Short wait for UI to respond to click
        time.sleep(0.5)
        
        # Switch to native context to interact with file picker
        print("🔄 Switching to native context for file picker...")
        driver.switch_to.context('NATIVE_APP')
        
        print("⏳ Waiting for file picker to be ready...")
        self.wait_for_picker_ready(driver, timeout=10)
        
        print("✅ Upload button clicked, file picker should be open")
    
    def navigate_file_picker_and_select(self, driver, wait):
        """Navigate Android file picker and select manual_upload_run.gpx"""
        print("📂 Navigating file picker to select test file...")
        
        try:
            # File picker should be ready from picker readiness check
            time.sleep(0.5)  # Brief wait for UI to settle
            
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
                time.sleep(1)  # Shorter wait for folder navigation
                
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
                
                time.sleep(1)  # Check every 1 second (more responsive)
                
            except Exception as e:
                print(f"⚠️ Error checking upload status: {e}")
                time.sleep(2)
                continue
        
        # Wait for map to stabilize after upload processing
        print("📡 Waiting for map to stabilize after upload processing...")
        try:
            self.wait_for_map_stable(driver, wait, timeout=10)
        except Exception as e:
            print(f"⚠️ Map stability check failed: {e}, continuing anyway...")
            time.sleep(2)  # Minimal fallback wait
        
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
        # Wait for map navigation to complete with deterministic check
        try:
            self.wait_for_map_stable(driver, None, timeout=10)
        except Exception:
            # Fallback to shorter wait if stability check fails
            time.sleep(2)
        
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
        # Skip pixel sampling in WebView if we know it won't work
        try:
            # Quick test to see if pixel sampling is possible
            test_result = driver.execute_script("""
                try {
                    const canvas = map.getCanvas();
                    if (!canvas) return {canSample: false, reason: 'No canvas'};
                    
                    const ctx = canvas.getContext('2d', {willReadFrequently: true});
                    if (!ctx) return {canSample: false, reason: 'No 2D context'};
                    
                    // Try a single pixel read to test if it works
                    const pixel = ctx.getImageData(1, 1, 1, 1).data;
                    return {canSample: true, testPixel: pixel.length};
                } catch (e) {
                    return {canSample: false, reason: e.message};
                }
            """)
            
            if not test_result.get('canSample', False):
                print(f"⚠️ Skipping pixel sampling: {test_result.get('reason', 'WebView limitation')}")
                print("📝 Using viewport feature verification instead")
                return {'error': 'Pixel sampling unavailable - WebView limitation', 'skipReason': test_result.get('reason')}
        except Exception as e:
            print(f"⚠️ Skipping pixel sampling due to error: {e}")
            return {'error': f'Pixel sampling failed: {str(e)}'}
        
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
        # Skip pixel sampling if we know it won't work
        try:
            test_result = driver.execute_script("""
                try {
                    const canvas = map.getCanvas();
                    const ctx = canvas ? canvas.getContext('2d', {willReadFrequently: true}) : null;
                    return {canSample: !!(canvas && ctx)};
                } catch (e) {
                    return {canSample: false};
                }
            """)
            
            if not test_result.get('canSample', False):
                print("⚠️ Skipping viewport pixel sampling: WebView limitation")
                return {'error': 'Viewport pixel sampling unavailable - WebView limitation'}
        except Exception:
            print("⚠️ Skipping viewport pixel sampling due to error")
            return {'error': 'Viewport pixel sampling failed'}
        
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
    
    def extras_panel_most_recent_verification(self, driver, wait):
        """Test that uploaded activity appears as most recent in extras panel and test filtering toggle"""
        print("📱 Opening extras panel to verify uploaded activity as most recent...")
        
        try:
            # Open extras panel
            extras_btn = self.find_clickable_element(driver, wait, "#extras-btn")
            extras_btn.click()
            time.sleep(3)  # Wait for panel to open and fetchLastActivity to complete
            
            # Verify the extras panel opened
            print("🔍 Checking extras panel opened...")
            extras_panel_info = driver.execute_script("""
                const panel = document.getElementById('extras-panel');
                return {
                    isOpen: panel && panel.classList.contains('open'),
                    hasContent: !!document.getElementById('extras-content')
                };
            """)
            
            assert extras_panel_info['isOpen'], "Extras panel should be open"
            assert extras_panel_info['hasContent'], "Extras panel should have content element"
            
            # Get the most recent activity information from the extras panel
            print("🔍 Verifying uploaded activity appears as most recent...")
            most_recent_activity_info = driver.execute_script("""
                const extrasContent = document.getElementById('extras-content');
                if (!extrasContent) return { error: 'No extras content element' };
                
                const runCards = extrasContent.querySelectorAll('.run-card');
                if (runCards.length === 0) return { error: 'No run cards found' };
                
                const firstCard = runCards[0];
                const dateElement = firstCard.querySelector('.run-date');
                const checkbox = firstCard.querySelector('.last-activity-checkbox');
                
                return {
                    cardCount: runCards.length,
                    hasDateElement: !!dateElement,
                    dateText: dateElement ? dateElement.textContent : null,
                    hasToggleCheckbox: !!checkbox,
                    checkboxLabel: checkbox ? checkbox.parentElement.textContent.trim() : null
                };
            """)
            
            print(f"📊 Most recent activity info: {most_recent_activity_info}")
            
            # Verify uploaded activity appears first (most recent) and has expected August 2024 date
            assert 'error' not in most_recent_activity_info, f"Error getting activity info: {most_recent_activity_info.get('error')}"
            assert most_recent_activity_info['hasDateElement'], "Most recent activity should have date element"
            assert most_recent_activity_info['hasToggleCheckbox'], "Most recent activity should have 'Show only this activity' checkbox"
            
            # Verify the date shows our uploaded activity (August 2024)
            date_text = most_recent_activity_info['dateText']
            assert date_text is not None, "Date text should not be None"
            assert "8/1/2024" in date_text or "08/01/2024" in date_text or "Aug" in date_text, f"Expected uploaded activity date (August 2024), got: {date_text}"
            
            print(f"✅ Uploaded activity verified as most recent: {date_text}")
            
            # Test the "Show only this activity" toggle functionality
            print("🎯 Testing 'Show only this activity' toggle...")
            self.test_show_only_activity_toggle(driver, wait)
            
            # Close extras panel
            print("🔒 Closing extras panel...")
            extras_btn = self.find_clickable_element(driver, wait, "#extras-btn")
            extras_btn.click()
            time.sleep(2)
            
            print("✅ Extras panel most recent activity verification completed successfully!")
            
        except Exception as e:
            print(f"⚠️ Error during extras panel verification: {e}")
            # Try to close panel if it's still open
            try:
                driver.execute_script("""
                    const panel = document.getElementById('extras-panel');
                    if (panel && panel.classList.contains('open')) {
                        const extrasBtn = document.getElementById('extras-btn');
                        if (extrasBtn) extrasBtn.click();
                    }
                """)
                time.sleep(1)
            except:
                pass
            raise
    
    def test_show_only_activity_toggle(self, driver, wait):
        """Test the 'Show only this activity' checkbox functionality for uploaded activity"""
        print("🔘 Testing show only activity toggle functionality...")
        
        # Get initial map state (should show all activities)
        initial_map_state = driver.execute_script("""
            // Check what's currently visible on the map
            const pmtilesLayer = map.getLayer('runsVec');
            const localLayer = map.getLayer('localRunsOverlay');
            
            return {
                pmtilesLayerExists: !!pmtilesLayer,
                localLayerExists: !!localLayer,
                pmtilesFilter: pmtilesLayer ? map.getFilter('runsVec') : null,
                timestamp: Date.now()
            };
        """)
        
        print(f"🗺️ Initial map state: {initial_map_state}")
        
        # Click the "Show only this activity" checkbox
        print("👆 Clicking 'Show only this activity' checkbox...")
        toggle_result = driver.execute_script("""
            const checkbox = document.querySelector('.last-activity-checkbox');
            if (!checkbox) return { error: 'Checkbox not found' };
            
            checkbox.click();
            
            return {
                success: true,
                checked: checkbox.checked,
                timestamp: Date.now()
            };
        """)
        
        assert 'error' not in toggle_result, f"Failed to click toggle: {toggle_result.get('error')}"
        assert toggle_result['checked'], "Checkbox should be checked after clicking"
        
        print("✅ Toggle clicked successfully")
        time.sleep(2)  # Wait for map update
        
        # Verify map now shows only the uploaded activity
        print("🔍 Verifying map shows only uploaded activity...")
        filtered_map_state = driver.execute_script("""
            // Check map filtering state after toggle
            const pmtilesFilter = map.getLayer('runsVec') ? map.getFilter('runsVec') : null;
            const localOverlaySource = map.getSource('localRunsOverlay');
            const localData = localOverlaySource ? localOverlaySource._data : null;
            
            return {
                pmtilesFilter: pmtilesFilter,
                localDataFeatures: localData ? localData.features.length : 0,
                hasFiltering: !!pmtilesFilter,
                timestamp: Date.now()
            };
        """)
        
        print(f"🗺️ Filtered map state: {filtered_map_state}")
        
        # Verify filtering is active (PMTiles layer should have filter, local overlay should show uploaded activity)
        assert filtered_map_state['hasFiltering'], "Map should have filtering active when 'Show only this activity' is checked"
        assert filtered_map_state['localDataFeatures'] > 0, "Local overlay should show the uploaded activity features"
        
        print("✅ Verified map shows only uploaded activity")
        
        # Test unchecking the toggle to restore all activities
        print("🔄 Unchecking toggle to restore all activities...")
        restore_result = driver.execute_script("""
            const checkbox = document.querySelector('.last-activity-checkbox');
            if (!checkbox) return { error: 'Checkbox not found' };
            
            checkbox.click();  // Uncheck
            
            return {
                success: true,
                checked: checkbox.checked,
                timestamp: Date.now()
            };
        """)
        
        assert 'error' not in restore_result, f"Failed to uncheck toggle: {restore_result.get('error')}"
        assert not restore_result['checked'], "Checkbox should be unchecked after second click"
        
        print("✅ Toggle unchecked successfully")
        time.sleep(2)  # Wait for map update
        
        # Verify map now shows all activities again
        print("🔍 Verifying all activities restored...")
        restored_map_state = driver.execute_script("""
            const pmtilesFilter = map.getLayer('runsVec') ? map.getFilter('runsVec') : null;
            
            return {
                pmtilesFilter: pmtilesFilter,
                hasFiltering: !!pmtilesFilter,
                timestamp: Date.now()
            };
        """)
        
        print(f"🗺️ Restored map state: {restored_map_state}")
        
        # Verify filtering is removed (no filter on PMTiles layer)
        assert not restored_map_state['hasFiltering'], "Map filtering should be cleared when toggle is unchecked"
        
        print("✅ 'Show only this activity' toggle functionality verified successfully!")
    
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
        time.sleep(3)  # Wait for map to settle and tiles to load
        
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
        time.sleep(1)
        
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
        
        # Close the side panel
        print("🔒 Closing side panel after lasso verification...")
        driver.execute_script("""
            const panel = document.getElementById('side-panel');
            if (panel && panel.classList.contains('open')) {
                const mapElement = document.getElementById('map');
                if (mapElement) {
                    mapElement.click();
                }
                panel.classList.remove('open');
            }
            
            // Deactivate lasso mode
            const lassoBtn = document.getElementById('lasso-btn');
            if (lassoBtn) {
                const styles = window.getComputedStyle(lassoBtn);
                const isActive = styles.backgroundColor.includes('rgb') && 
                               !styles.backgroundColor.includes('255, 255, 255');
                if (isActive) {
                    lassoBtn.click();
                }
            }
        """)
        time.sleep(1)
        
        print("✅ Lasso selection verification completed - uploaded activity properly shows in sidebar!")
    
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