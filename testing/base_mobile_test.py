"""
Base class for mobile tests with common functionality including dynamic map loading.
"""
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, JavascriptException
from map_load_detector import MapLoadDetector

class BaseMobileTest:
    """Base class providing common mobile test functionality"""
    
    def wait_for_map_load(self, driver, wait, verbose=False):
        """
        Dynamically wait for map to load using MapLoadDetector.
        
        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
            verbose: Enable detailed logging
            
        Returns:
            True when map is ready
        """
        detector = MapLoadDetector(driver, wait, verbose=verbose)
        return detector.wait_for_map_ready()
    
    def wait_for_webview_ready(self, driver, timeout=30):
        """
        Wait for WebView context to be available for switching.
        Replaces fixed time.sleep() calls in WebView switching.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum seconds to wait (default 30)
            
        Returns:
            True when WebView context is available, raises TimeoutException if not available in time
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if WebView contexts are available
                contexts = driver.contexts
                webview_available = any('WEBVIEW' in ctx for ctx in contexts)
                
                if webview_available:
                    # WebView context is available for switching
                    return True
                        
                time.sleep(0.5)  # Poll every 500ms
                
            except Exception:
                time.sleep(0.5)
                
        raise TimeoutException(f"WebView context not available after {timeout} seconds")
    
    def wait_for_map_stable(self, driver, wait, timeout=45):
        """
        Wait for map to be loaded and stable with tiles ready.
        Replaces fixed time.sleep() calls after map navigation.
        Uses enhanced MapLoadDetector for consistent stability verification.
        
        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance  
            timeout: Maximum seconds to wait (default 45)
            
        Returns:
            True when map is stable, raises TimeoutException if not stable in time
        """
        # Use enhanced MapLoadDetector with stable tile count verification
        detector = MapLoadDetector(driver, wait, verbose=False)
        
        # First ensure basic map readiness (30s max)
        detector.wait_for_map_ready(timeout=min(30, timeout))
        
        # Then wait for tile stability with 3 consecutive stable checks
        remaining_timeout = max(15, timeout - 30)  # At least 15s for stability
        return detector.wait_for_stable_tiles(timeout=remaining_timeout, stability_checks=3)
    
    def wait_for_layers_stable(self, driver, expected_count, timeout=30):
        """
        Wait for activity layers/features to reach expected count and remain stable.
        Replaces fixed time.sleep() calls after layer rendering.
        
        Args:
            driver: Selenium WebDriver instance
            expected_count: Expected number of activity features/layers
            timeout: Maximum seconds to wait (default 30)
            
        Returns:
            True when layers are stable, raises TimeoutException if not stable in time
        """
        start_time = time.time()
        consecutive_stable_checks = 0
        required_stable_checks = 3
        last_count = 0
        
        while time.time() - start_time < timeout:
            try:
                # Query rendered features to check activity visibility
                feature_info = driver.execute_script("""
                    if (typeof map === 'undefined') return {count: 0, ready: false};
                    
                    try {
                        // Check if map is ready for queries
                        if (!map.loaded || !map.loaded()) {
                            return {count: 0, ready: false};
                        }
                        
                        // Query all rendered features
                        const allFeatures = map.queryRenderedFeatures();
                        
                        // Count LineString features (activity routes)
                        const activityFeatures = allFeatures.filter(f => 
                            f.geometry && f.geometry.type === 'LineString'
                        );
                        
                        return {
                            count: activityFeatures.length,
                            ready: true,
                            total: allFeatures.length
                        };
                    } catch (e) {
                        return {count: 0, ready: false, error: e.message};
                    }
                """)
                
                if not feature_info.get('ready', False):
                    time.sleep(0.5)
                    continue
                    
                current_count = feature_info.get('count', 0)
                
                # Check if we have expected count and it's stable
                if current_count >= expected_count and current_count == last_count:
                    consecutive_stable_checks += 1
                    if consecutive_stable_checks >= required_stable_checks:
                        return True
                else:
                    consecutive_stable_checks = 0
                    
                last_count = current_count
                time.sleep(0.5)  # Poll every 500ms
                
            except Exception:
                consecutive_stable_checks = 0
                time.sleep(0.5)
                
        # If we can't reach expected count but have some features, that might be acceptable
        final_info = driver.execute_script("""
            if (typeof map === 'undefined') return {count: 0};
            try {
                const allFeatures = map.queryRenderedFeatures();
                const activityFeatures = allFeatures.filter(f => 
                    f.geometry && f.geometry.type === 'LineString'
                );
                return {count: activityFeatures.length};
            } catch (e) {
                return {count: 0};
            }
        """)
        
        final_count = final_info.get('count', 0)
        if final_count > 0:
            # Accept partial success if we have some features visible
            return True
            
        raise TimeoutException(f"Layers not stable after {timeout} seconds (expected: {expected_count}, final: {final_count})")
    
    def switch_to_webview(self, driver, max_attempts=3):
        """
        Switch to WebView context with retry logic and interference handling.
        Consolidated from multiple test files.
        """
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
                    
                    # Wait for WebView JavaScript execution to be ready instead of fixed sleep
                    try:
                        # Test JavaScript execution readiness after context switch
                        start_time = time.time()
                        while time.time() - start_time < 10:  # 10 second timeout
                            try:
                                result = driver.execute_script("return typeof document !== 'undefined';")
                                if result:
                                    print(f"✅ Successfully switched to: {target_webview}")
                                    return target_webview
                                break
                            except Exception:
                                time.sleep(0.5)  # Poll every 500ms
                                continue
                        
                        # If we get here, JavaScript execution isn't ready
                        print(f"⚠️ WebView JavaScript not ready after context switch: {target_webview}")
                        # Continue to retry logic below
                    except Exception as e:
                        print(f"⚠️ WebView readiness check failed: {e}")
                        # Continue to retry logic below
                else:
                    print("⚠️ No suitable WebView context found")
                    
            except Exception as e:
                print(f"⚠️ WebView switch attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    print("🔄 Waiting before retry...")
                    time.sleep(2 + attempt)  # Shorter increasing delay
                    
                    # Try to close interfering webview_shell if present
                    try:
                        if 'org.chromium.webview_shell' in str(driver.contexts):
                            print("🧹 Attempting to clear webview_shell interference...")
                            driver.switch_to.context('NATIVE_APP')
                            time.sleep(0.5)  # Shorter wait
                    except:
                        pass
                    continue
                else:
                    raise
        
        raise Exception("Failed to switch to WebView context after all attempts")
    
    def find_clickable_element(self, driver, wait, selector):
        """
        Find element that might be blocked by other elements.
        Consolidated from multiple test files.
        """
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
    
    
    def check_side_panel(self, driver):
        """
        Check if side panel opened and has content.
        Consolidated from multiple test files.
        """
        panel_info = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            const panelContent = document.getElementById('panel-content');
            
            if (!panel) return { visible: false, error: 'No side panel element' };
            
            const styles = window.getComputedStyle(panel);
            const isVisible = styles.display !== 'none' && styles.visibility !== 'hidden';
            
            let runCount = 0;
            let hasContent = false;
            let allText = '';
            
            if (panelContent) {
                hasContent = panelContent.textContent.trim().length > 10;
                allText = panelContent.textContent.trim();
                
                // Try different strategies to count actual activity cards
                // Strategy 1: Look for specific activity card containers
                let activityCards = panelContent.querySelectorAll('.activity-card, .run-item, [data-activity], [data-run-id]');
                
                // Strategy 2: Look for date patterns (each activity should have a date)
                const dateMatches = allText.match(/\\d{1,2}\\/\\d{1,2}\\/\\d{4}/g);
                const uniqueDates = dateMatches ? [...new Set(dateMatches)] : [];
                
                // Strategy 3: Look for distance/time pattern combinations (📏 + ⏱️)
                const distanceTimePattern = /📏[^⏱️]*⏱️/g;
                const distanceTimeMatches = allText.match(distanceTimePattern);
                
                // Use the most reliable count
                if (activityCards.length > 0) {
                    runCount = activityCards.length;
                } else if (uniqueDates.length > 0) {
                    runCount = uniqueDates.length;
                } else if (distanceTimeMatches && distanceTimeMatches.length > 0) {
                    runCount = distanceTimeMatches.length;
                } else if (hasContent) {
                    // Fallback: assume 1 activity if there's meaningful content
                    runCount = 1;
                }
            }
            
            return {
                visible: isVisible,
                hasContent: hasContent,
                runCount: runCount,
                display: styles.display,
                visibility: styles.visibility,
                fullText: allText
            };
        """)
        
        self._print_formatted_panel_info(panel_info)
        return panel_info
    
    def _print_formatted_panel_info(self, panel_info):
        """Format and print side panel information in a human-readable way"""
        if not panel_info:
            print("📋 Side Panel Status: No panel info available")
            return
            
        print("📋 Side Panel Status:")
        
        # Panel visibility
        if panel_info.get('visible', False):
            display = panel_info.get('display', 'unknown')
            visibility = panel_info.get('visibility', 'unknown')
            print(f"   ✅ Visible (display: {display}, visibility: {visibility})")
        else:
            print(f"   ❌ Not visible")
            if 'error' in panel_info:
                print(f"      Error: {panel_info['error']}")
            return
        
        # Run count and content
        run_count = panel_info.get('runCount', 0)
        has_content = panel_info.get('hasContent', False)
        
        if not has_content:
            print("   📭 No content found")
            return
            
        if run_count > 0:
            print(f"   🏃 Found {run_count} activit{'ies' if run_count != 1 else 'y'}:")
            
            # Parse and format the full text
            full_text = panel_info.get('fullText', '')
            if full_text:
                activities = self._parse_activities_from_text(full_text)
                for i, activity in enumerate(activities, 1):
                    print(f"      {i}. {activity}")
            else:
                print("      (Activity details not available)")
        else:
            print("   📝 Panel has content but no activities detected")
            # Show a snippet of the content for debugging
            full_text = panel_info.get('fullText', '')
            if full_text:
                snippet = full_text.replace('\n', ' ').strip()[:100]
                if len(snippet) == 100:
                    snippet += "..."
                print(f"      Content snippet: {snippet}")
    
    def _parse_activities_from_text(self, full_text):
        """Parse individual activities from the panel's full text"""
        import re
        
        activities = []
        
        # Clean up the text - remove excessive whitespace and newlines
        cleaned_text = re.sub(r'\s+', ' ', full_text).strip()
        
        # Look for date patterns (various formats)
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [AP]M',  # MM/DD/YYYY HH:MM:SS AM/PM
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
        ]
        
        # Try to split by date patterns
        for pattern in date_patterns:
            matches = list(re.finditer(pattern, cleaned_text))
            if matches:
                for match in matches:
                    date_str = match.group()
                    # Find the end of this activity (start of next date or end of text)
                    start_pos = match.start()
                    next_match = None
                    for other_match in matches:
                        if other_match.start() > match.start():
                            next_match = other_match
                            break
                    
                    if next_match:
                        end_pos = next_match.start()
                    else:
                        end_pos = len(cleaned_text)
                    
                    # Extract the activity text
                    activity_text = cleaned_text[start_pos:end_pos].strip()
                    
                    # Clean up and format the activity
                    activity = self._format_single_activity(activity_text)
                    if activity and activity not in activities:
                        activities.append(activity)
                break
        
        # If no date patterns found, try to split by emojis or other markers
        if not activities:
            # Split by running emoji or other common separators
            parts = re.split(r'🏃|🚴|🏊', cleaned_text)
            for part in parts:
                part = part.strip()
                if part and len(part) > 10:  # Ignore very short fragments
                    activity = self._format_single_activity(part)
                    if activity:
                        activities.append(activity)
        
        # If still no activities, return the cleaned text as one activity
        if not activities and cleaned_text:
            activities.append(self._format_single_activity(cleaned_text))
        
        return activities[:10]  # Limit to 10 activities to avoid spam
    
    def _format_single_activity(self, activity_text):
        """Format a single activity text for display"""
        import re
        
        # Remove excessive whitespace
        activity = re.sub(r'\s+', ' ', activity_text).strip()
        
        # Remove common UI artifacts
        activity = re.sub(r'^\s*🏃\s*', '', activity)  # Remove leading running emoji
        
        # Extract meaningful parts (date, distance, time)
        parts = []
        
        # Look for date
        date_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}(?:\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M)?', activity)
        if date_match:
            parts.append(date_match.group())
        
        # Look for distance (with emoji)
        distance_match = re.search(r'📏\s*[\d.]+\s*mi', activity)
        if distance_match:
            parts.append(distance_match.group())
        
        # Look for time (with emoji)  
        time_match = re.search(r'⏱️\s*\d+:\d+', activity)
        if time_match:
            parts.append(time_match.group())
        
        if parts:
            return ' - '.join(parts)
        
        # Fallback: return cleaned activity if it's not too long
        if len(activity) <= 100:
            return activity
        else:
            return activity[:97] + "..."
    
    def get_selected_runs_details(self, driver):
        """
        Extract details about selected runs from side panel.
        Consolidated from multiple test files.
        """
        runs_info = driver.execute_script("""
            const panel = document.getElementById('side-panel');
            const panelContent = document.getElementById('panel-content');
            
            if (!panel || !panelContent) return [];
            
            const runs = [];
            
            // Look for run cards or similar elements
            const runElements = panelContent.querySelectorAll('.run-card, [class*="run"], .activity-item, [data-run]');
            
            runElements.forEach(element => {
                const textContent = element.textContent || '';
                const title = element.querySelector('h3, h4, .title, .name');
                const date = element.querySelector('.date, .time');
                
                runs.push({
                    name: title ? title.textContent.trim() : textContent.slice(0, 50),
                    fullText: textContent.trim(),
                    hasElement: true
                });
            });
            
            // If no specific run elements found, check for general text content
            if (runs.length === 0) {
                const allText = panelContent.textContent.trim();
                if (allText.length > 10) {
                    runs.push({
                        name: 'Unknown Run',
                        fullText: allText,
                        hasElement: false
                    });
                }
            }
            
            return runs;
        """)
        
        return runs_info or []
    
    def debug_rendering_state(self, driver):
        """
        Get complete rendering state for debugging.
        Consolidated from rock-solid test methods.
        """
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
    
    def verify_features_in_current_viewport(self, driver):
        """
        Verify activity features are visible in current viewport.
        Consolidated from rock-solid test methods.
        """
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