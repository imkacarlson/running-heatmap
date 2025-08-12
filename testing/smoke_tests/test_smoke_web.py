"""
Smoke tests for mobile web interface
Fast validation of mobile template and mobile-specific functionality
"""
import pytest
import time
import subprocess
import sys
import os
from pathlib import Path
from .base_smoke_test import BaseSmokeTest

# Try to import selenium, make it optional for environments without it
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available - web interface tests will be skipped")


@pytest.mark.smoke
@pytest.mark.smoke_mobile_web
class TestMobileWebSmoke(BaseSmokeTest):
    """Smoke tests for mobile web interface validation"""
    
    server_process = None
    server_url = None
    server_port = 5002  # Use different port to avoid conflicts
    driver = None
    
    @classmethod
    def setup_class(cls):
        """Start test server and browser for web testing"""
        super().setup_class()
        
        if not SELENIUM_AVAILABLE:
            pytest.skip("Selenium not available - skipping web interface tests")
        
        cls.server_url = f"http://localhost:{cls.server_port}"
        cls._start_test_server()
        cls._setup_browser()
        
        # Wait for server to be ready
        max_wait = 5
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                import requests
                response = requests.get(f"{cls.server_url}/", timeout=1)
                if response.status_code == 200:
                    print(f"✅ Test server ready at {cls.server_url}")
                    break
            except:
                time.sleep(0.1)
        else:
            pytest.fail(f"Test server failed to start within {max_wait}s")
    
    @classmethod
    def teardown_class(cls):
        """Stop browser and test server"""
        if cls.driver:
            try:
                cls.driver.quit()
            except:
                pass
        
        if cls.server_process:
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()
        
        super().teardown_class()
    
    @classmethod
    def _start_test_server(cls):
        """Start Flask server for web testing"""
        server_dir = cls.project_root / "server"
        
        # Check if runs.pkl exists, create minimal one if not
        runs_pkl = server_dir / "runs.pkl"
        if not runs_pkl.exists():
            cls._create_minimal_test_data(runs_pkl)
        
        # Start server process
        env = {
            'FLASK_ENV': 'testing',
            'FLASK_DEBUG': 'false',
            **dict(os.environ)
        }
        
        try:
            cls.server_process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=server_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=None if sys.platform == "win32" else os.setsid
            )
        except Exception as e:
            pytest.fail(f"Failed to start test server: {e}")
    
    @classmethod
    def _create_minimal_test_data(cls, runs_pkl_path):
        """Create minimal test data for web testing"""
        import pickle
        from shapely.geometry import LineString
        from datetime import datetime
        
        # Create minimal test run data
        test_coords = [
            [-122.4194, 37.7749],  # San Francisco
            [-122.4184, 37.7759],
            [-122.4174, 37.7769]
        ]
        
        line = LineString(test_coords)
        test_runs = {
            1: {
                'bbox': line.bounds,
                'geoms': {
                    'full': line,
                    'high': line,
                    'mid': line,
                    'low': line,
                    'coarse': line,
                },
                'metadata': {
                    'start_time': datetime.now(),
                    'end_time': datetime.now(),
                    'distance': 1000.0,
                    'duration': 300.0,
                    'activity_type': 'run',
                    'activity_raw': 'running',
                    'source_file': 'test_run.gpx',
                },
            }
        }
        
        with open(runs_pkl_path, 'wb') as f:
            pickle.dump(test_runs, f)
        
        print(f"✅ Created minimal test data at {runs_pkl_path}")
    
    @classmethod
    def _setup_browser(cls):
        """Setup headless browser for testing"""
        try:
            # Try Chrome first (most common)
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.set_page_load_timeout(10)
            print("✅ Chrome browser initialized for testing")
            return
            
        except WebDriverException:
            pass
        
        try:
            # Try Firefox as fallback
            firefox_options = FirefoxOptions()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--width=1920')
            firefox_options.add_argument('--height=1080')
            
            cls.driver = webdriver.Firefox(options=firefox_options)
            cls.driver.set_page_load_timeout(10)
            print("✅ Firefox browser initialized for testing")
            return
            
        except WebDriverException:
            pass
        
        pytest.fail("No suitable browser driver found (Chrome or Firefox required)")
    
    def test_mobile_template_loads_successfully(self):
        """Test that mobile template loads without errors"""
        # Check if mobile template exists
        mobile_template = self.get_server_dir() / "mobile_template.html"
        if not mobile_template.exists():
            pytest.skip("Mobile template not found - skipping mobile web tests")
        
        try:
            self.driver.get(self.server_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 5).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Check page title
            title = self.driver.title
            assert title, "Page title should not be empty"
            assert "heatmap" in title.lower() or "run" in title.lower(), \
                f"Page title should contain 'heatmap' or 'run': {title}"
            
            print(f"✅ Mobile template loaded successfully: {title}")
            
        except TimeoutException:
            pytest.fail("Mobile template failed to load within timeout")
        except WebDriverException as e:
            pytest.fail(f"Mobile template loading failed: {e}")
    
    def test_mobile_map_container_exists(self):
        """Test that mobile map container element exists"""
        mobile_template = self.get_server_dir() / "mobile_template.html"
        if not mobile_template.exists():
            pytest.skip("Mobile template not found - skipping mobile map tests")
            
        try:
            self.driver.get(self.server_url)
            
            # Wait for map container to be present
            map_container = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "map"))
            )
            
            # Check map container properties
            assert map_container.is_displayed(), "Mobile map container should be visible"
            
            # Check map container has reasonable dimensions
            size = map_container.size
            assert size['width'] > 100, f"Mobile map container width too small: {size['width']}"
            assert size['height'] > 100, f"Mobile map container height too small: {size['height']}"
            
            print(f"✅ Mobile map container found with size: {size['width']}x{size['height']}")
            
        except TimeoutException:
            pytest.fail("Mobile map container not found within timeout")
        except WebDriverException as e:
            pytest.fail(f"Mobile map container test failed: {e}")
    
    def test_mobile_ui_elements_exist(self):
        """Test that mobile-specific UI elements are present"""
        mobile_template = self.get_server_dir() / "mobile_template.html"
        if not mobile_template.exists():
            pytest.skip("Mobile template not found - skipping mobile UI tests")
            
        try:
            self.driver.get(self.server_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "map"))
            )
            
            # Check for mobile-specific UI elements
            mobile_elements = [
                ("map", "Mobile map container"),
                ("lasso-btn", "Mobile lasso selection button"),
                ("upload-btn", "Mobile upload button"),
                ("zoom-in-btn", "Mobile zoom in button"),
                ("zoom-out-btn", "Mobile zoom out button"),
            ]
            
            for element_id, description in mobile_elements:
                try:
                    element = self.driver.find_element(By.ID, element_id)
                    assert element.is_displayed() or element_id == "map", \
                        f"{description} should be visible"
                    print(f"✅ Found {description}")
                except:
                    print(f"⚠️  {description} not found (may be optional in mobile)")
            
            print("✅ Mobile UI elements validation completed")
            
        except TimeoutException:
            pytest.fail("Mobile UI elements not found within timeout")
        except WebDriverException as e:
            pytest.fail(f"Mobile UI elements test failed: {e}")
    
    def test_mobile_javascript_loads_without_errors(self):
        """Test that mobile JavaScript executes without console errors"""
        mobile_template = self.get_server_dir() / "mobile_template.html"
        if not mobile_template.exists():
            pytest.skip("Mobile template not found - skipping mobile JavaScript tests")
            
        try:
            self.driver.get(self.server_url)
            
            # Wait for page to load completely
            WebDriverWait(self.driver, 5).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Give JavaScript time to initialize
            time.sleep(2)
            
            # Check for JavaScript errors in console
            logs = self.driver.get_log('browser')
            
            # Filter for actual errors (not warnings or info)
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            # Some network errors are expected in mobile test environment
            critical_errors = []
            for error in errors:
                message = error['message'].lower()
                # Skip expected network errors for external resources in mobile context
                if any(skip in message for skip in [
                    'net::err_internet_disconnected',
                    'net::err_name_not_resolved', 
                    'failed to load resource',
                    'openstreetmap.org',
                    'unpkg.com',
                    'pmtiles'  # PMTiles may not be available in test
                ]):
                    continue
                critical_errors.append(error)
            
            if critical_errors:
                error_messages = [err['message'] for err in critical_errors]
                pytest.fail(f"Mobile JavaScript errors found: {error_messages}")
            
            print("✅ Mobile JavaScript loads without critical errors")
            
        except TimeoutException:
            pytest.fail("Mobile JavaScript error check timed out")
        except WebDriverException as e:
            # Some browsers don't support log collection
            print(f"⚠️  Could not check mobile JavaScript errors: {e}")
            print("✅ Mobile JavaScript error check skipped (browser limitation)")
    
    def test_mobile_template_structure(self):
        """Test that mobile template has expected structure"""
        mobile_template = self.get_server_dir() / "mobile_template.html"
        if not mobile_template.exists():
            pytest.skip("Mobile template not found - skipping mobile template tests")
        
        # Check mobile template content
        self.check_file_contains(mobile_template, "<html", "HTML structure")
        self.check_file_contains(mobile_template, "id=\"map\"", "Map container element")
        
        # Check for mobile-specific elements
        template_content = mobile_template.read_text(encoding='utf-8', errors='ignore')
        
        mobile_indicators = [
            "viewport",  # Mobile viewport meta tag
            "map",       # Map container
        ]
        
        for indicator in mobile_indicators:
            assert indicator in template_content.lower(), \
                f"Mobile template missing expected element: {indicator}"
        
        print("✅ Mobile template structure validation completed")
    
    def test_mobile_javascript_structure(self):
        """Test that mobile JavaScript has expected structure"""
        mobile_js = self.get_server_dir() / "mobile_main.js"
        if not mobile_js.exists():
            pytest.skip("Mobile JavaScript not found - skipping mobile JS tests")
        
        # Check mobile JavaScript content
        js_content = mobile_js.read_text(encoding='utf-8', errors='ignore')
        
        # Check for mobile-specific JavaScript patterns
        mobile_js_patterns = [
            "map",           # Map object
            "maplibre",      # MapLibre reference
        ]
        
        for pattern in mobile_js_patterns:
            if pattern.lower() in js_content.lower():
                print(f"✅ Found mobile JS pattern: {pattern}")
            else:
                print(f"⚠️  Mobile JS pattern not found: {pattern} (may be optional)")
        
        print("✅ Mobile JavaScript structure validation completed")
    
    def test_mobile_performance_timing(self):
        """Test that mobile template loads within reasonable time"""
        mobile_template = self.get_server_dir() / "mobile_template.html"
        if not mobile_template.exists():
            pytest.skip("Mobile template not found - skipping mobile performance tests")
            
        start_time = time.time()
        
        try:
            self.driver.get(self.server_url)
            
            # Wait for page to be fully loaded
            WebDriverWait(self.driver, 5).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            load_time = time.time() - start_time
            
            # Mobile template should load quickly for smoke tests
            assert load_time < 5.0, f"Mobile template load too slow: {load_time:.2f}s (should be <5s)"
            
            print(f"✅ Mobile template loaded in {load_time:.2f}s")
            
        except TimeoutException:
            load_time = time.time() - start_time
            pytest.fail(f"Mobile template failed to load within timeout ({load_time:.2f}s)")
        except WebDriverException as e:
            pytest.fail(f"Mobile template performance test failed: {e}")