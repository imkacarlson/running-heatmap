"""
Smoke tests for mobile API endpoints
Fast validation of key API endpoints used by mobile app without full server startup
"""
import pytest
import requests
import json
import time
import threading
import subprocess
import sys
import os
from pathlib import Path
from .base_smoke_test import BaseSmokeTest


@pytest.mark.smoke
@pytest.mark.smoke_mobile_api
class TestMobileAPISmoke(BaseSmokeTest):
    """Smoke tests for mobile API endpoint validation"""
    
    server_process = None
    server_url = None
    server_port = 5001  # Use different port to avoid conflicts
    
    @classmethod
    def setup_class(cls):
        """Start test server for API testing"""
        super().setup_class()
        cls.server_url = f"http://localhost:{cls.server_port}"
        cls._start_test_server()
        
        # Wait for server to be ready
        max_wait = 5
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{cls.server_url}/", timeout=1)
                if response.status_code == 200:
                    print(f"✅ Test server ready at {cls.server_url}")
                    break
            except requests.exceptions.RequestException:
                time.sleep(0.1)
        else:
            pytest.fail(f"Test server failed to start within {max_wait}s")
    
    @classmethod
    def teardown_class(cls):
        """Stop test server"""
        if cls.server_process:
            cls.server_process.terminate()
            try:
                cls.server_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                cls.server_process.kill()
        super().teardown_class()
    
    @classmethod
    def _start_test_server(cls):
        """Start Flask server for testing"""
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
                # Modify the Flask app to use our test port
                preexec_fn=None if sys.platform == "win32" else os.setsid
            )
        except Exception as e:
            pytest.fail(f"Failed to start test server: {e}")
    
    @classmethod
    def _create_minimal_test_data(cls, runs_pkl_path):
        """Create minimal test data for API testing"""
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
    
    def test_mobile_root_endpoint_serves_html(self):
        """Test that root endpoint serves mobile HTML content"""
        try:
            response = requests.get(f"{self.server_url}/", timeout=2)
            
            # Check status code
            assert response.status_code == 200, f"Mobile root endpoint returned {response.status_code}"
            
            # Check content type indicates HTML
            content_type = response.headers.get('content-type', '').lower()
            assert 'html' in content_type or response.text.strip().startswith('<!'), \
                f"Mobile root endpoint doesn't serve HTML content: {content_type}"
            
            # Check basic HTML structure
            html_content = response.text
            assert '<html' in html_content.lower() or '<!doctype html' in html_content.lower(), \
                "Response doesn't contain valid HTML structure"
            
            print("✅ Mobile root endpoint serves HTML successfully")
            
        except requests.exceptions.Timeout:
            pytest.fail("Mobile root endpoint request timed out")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Mobile root endpoint request failed: {e}")
    
    def test_mobile_api_last_activity_endpoint(self):
        """Test /api/last_activity endpoint returns valid JSON for mobile app"""
        try:
            response = requests.get(f"{self.server_url}/api/last_activity", timeout=2)
            
            # Check status code
            assert response.status_code == 200, f"Mobile last activity endpoint returned {response.status_code}"
            
            # Check content type is JSON
            content_type = response.headers.get('content-type', '').lower()
            assert 'json' in content_type, f"Mobile last activity endpoint doesn't return JSON: {content_type}"
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                pytest.fail(f"Mobile last activity endpoint returned invalid JSON: {e}")
            
            # Validate response structure (can be empty if no runs)
            assert isinstance(data, dict), "Mobile last activity response should be a dictionary"
            
            # If data exists, validate structure for mobile consumption
            if data:
                assert 'id' in data, "Mobile last activity response missing 'id' field"
                assert 'metadata' in data, "Mobile last activity response missing 'metadata' field"
                assert isinstance(data['metadata'], dict), "Mobile metadata should be a dictionary"
                
                # Check for mobile-relevant metadata fields
                metadata = data['metadata']
                mobile_fields = ['activity_type', 'distance', 'duration']
                for field in mobile_fields:
                    if field in metadata:
                        print(f"✅ Found mobile-relevant field: {field}")
            
            print("✅ Mobile last activity endpoint returns valid JSON")
            
        except requests.exceptions.Timeout:
            pytest.fail("Mobile last activity endpoint request timed out")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Mobile last activity endpoint request failed: {e}")
    
    def test_mobile_api_runs_in_area_endpoint(self):
        """Test /api/runs_in_area endpoint accepts POST and returns valid structure for mobile app"""
        # Test data: simple square polygon for mobile lasso selection
        test_polygon = [
            [-122.42, 37.77],
            [-122.42, 37.78],
            [-122.41, 37.78],
            [-122.41, 37.77],
            [-122.42, 37.77]  # Close the polygon
        ]
        
        payload = {
            'polygon': test_polygon
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/api/runs_in_area",
                json=payload,
                timeout=2
            )
            
            # Check status code
            assert response.status_code == 200, f"Mobile runs in area endpoint returned {response.status_code}"
            
            # Check content type is JSON
            content_type = response.headers.get('content-type', '').lower()
            assert 'json' in content_type, f"Mobile runs in area endpoint doesn't return JSON: {content_type}"
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                pytest.fail(f"Mobile runs in area endpoint returned invalid JSON: {e}")
            
            # Validate response structure for mobile consumption
            assert isinstance(data, dict), "Mobile runs in area response should be a dictionary"
            assert 'runs' in data, "Mobile response missing 'runs' field"
            assert 'total' in data, "Mobile response missing 'total' field"
            assert isinstance(data['runs'], list), "Mobile runs field should be a list"
            assert isinstance(data['total'], int), "Mobile total field should be an integer"
            
            # Validate individual run structure for mobile app
            for run in data['runs']:
                assert isinstance(run, dict), "Each mobile run should be a dictionary"
                assert 'id' in run, "Mobile run missing 'id' field"
                assert 'geometry' in run, "Mobile run missing 'geometry' field"
                assert 'metadata' in run, "Mobile run missing 'metadata' field"
                
                # Check for mobile-relevant metadata
                metadata = run['metadata']
                mobile_fields = ['activity_type', 'distance', 'duration']
                for field in mobile_fields:
                    if field in metadata:
                        print(f"✅ Mobile run has field: {field}")
            
            print(f"✅ Mobile runs in area endpoint returns valid structure (found {data['total']} runs)")
            
        except requests.exceptions.Timeout:
            pytest.fail("Mobile runs in area endpoint request timed out")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Mobile runs in area endpoint request failed: {e}")
    
    def test_api_error_handling(self):
        """Test API error handling for invalid requests"""
        # Test runs_in_area with invalid data
        invalid_payloads = [
            {},  # Missing polygon
            {'polygon': []},  # Empty polygon
            {'polygon': [[-122.42, 37.77]]},  # Too few points
            {'polygon': [['invalid', 'coords']]},  # Invalid coordinates
        ]
        
        for i, payload in enumerate(invalid_payloads):
            try:
                response = requests.post(
                    f"{self.server_url}/api/runs_in_area",
                    json=payload,
                    timeout=2
                )
                
                # Should return 400 for invalid requests
                assert response.status_code == 400, \
                    f"Invalid payload {i} should return 400, got {response.status_code}"
                
                # Should return JSON error message
                try:
                    error_data = response.json()
                    assert 'error' in error_data, f"Error response {i} missing 'error' field"
                except json.JSONDecodeError:
                    pytest.fail(f"Error response {i} should be valid JSON")
                
            except requests.exceptions.Timeout:
                pytest.fail(f"Error handling test {i} timed out")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Error handling test {i} failed: {e}")
        
        print("✅ API error handling works correctly")
    
    def test_api_timeout_behavior(self):
        """Test API endpoints respond within reasonable time"""
        endpoints = [
            ('GET', '/'),
            ('GET', '/api/last_activity'),
        ]
        
        for method, endpoint in endpoints:
            start_time = time.time()
            
            try:
                if method == 'GET':
                    response = requests.get(f"{self.server_url}{endpoint}", timeout=2)
                else:
                    response = requests.post(f"{self.server_url}{endpoint}", timeout=2)
                
                response_time = time.time() - start_time
                
                # API should respond quickly for smoke tests
                assert response_time < 1.0, \
                    f"{method} {endpoint} took {response_time:.2f}s (should be <1s)"
                
                print(f"✅ {method} {endpoint} responded in {response_time:.3f}s")
                
            except requests.exceptions.Timeout:
                pytest.fail(f"{method} {endpoint} timed out (>2s)")
            except requests.exceptions.RequestException as e:
                pytest.fail(f"{method} {endpoint} request failed: {e}")
    
    def test_pmtiles_endpoint_availability(self):
        """Test PMTiles endpoint is available (may return 404 if no PMTiles file)"""
        try:
            response = requests.get(f"{self.server_url}/runs.pmtiles", timeout=2)
            
            # Either 200 (file exists) or 404 (file doesn't exist) is acceptable
            assert response.status_code in [200, 404], \
                f"PMTiles endpoint returned unexpected status: {response.status_code}"
            
            if response.status_code == 200:
                # If file exists, check it's binary content
                assert len(response.content) > 0, "PMTiles file appears to be empty"
                print("✅ PMTiles endpoint serves file successfully")
            else:
                print("ℹ️  PMTiles file not found (expected for fresh setup)")
                
        except requests.exceptions.Timeout:
            pytest.fail("PMTiles endpoint request timed out")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"PMTiles endpoint request failed: {e}")
    
    def test_api_response_headers(self):
        """Test API endpoints return appropriate headers"""
        try:
            response = requests.get(f"{self.server_url}/api/last_activity", timeout=2)
            
            # Check for CORS headers (if configured)
            headers = response.headers
            
            # Basic header validation
            assert 'content-type' in headers, "Response missing Content-Type header"
            assert 'json' in headers['content-type'].lower(), "API should return JSON content type"
            
            # Check server header exists
            if 'server' in headers:
                print(f"✅ Server header: {headers['server']}")
            
            print("✅ API response headers are appropriate")
            
        except requests.exceptions.Timeout:
            pytest.fail("API headers test timed out")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"API headers test failed: {e}")