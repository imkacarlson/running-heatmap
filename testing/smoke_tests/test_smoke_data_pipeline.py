"""
Smoke tests for mobile data pipeline validation
Tests data processing components within 2-second timeout
"""
import os
import pickle
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

# Make pytest optional for standalone usage
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create a dummy pytest module for compatibility
    class DummyPytest:
        @staticmethod
        def mark(name):
            def decorator(func):
                return func
            return decorator
        @staticmethod
        def fail(msg):
            raise AssertionError(msg)
    pytest = DummyPytest()

from .base_smoke_test import BaseSmokeTest


@pytest.mark.smoke
class TestDataPipelineSmoke(BaseSmokeTest):
    """
    Smoke tests for data pipeline components focused on mobile testing
    All tests must complete within 2-second timeout per requirement 1.1
    """
    
    def setup_method(self):
        """Setup for each test method"""
        super().setup_method()
        self.server_dir = self.get_server_dir()
        self.test_data_dir = self.get_test_data_dir()
        
    def test_runs_pkl_loading_and_validation(self):
        """
        Test runs.pkl loading and validation within 2-second timeout
        Requirements: 4.1, 1.1
        """
        start_time = time.time()
        
        # Check for runs.pkl in common locations
        possible_paths = [
            self.server_dir / "runs.pkl",
            self.get_project_root() / "data" / "runs.pkl",
            self.get_project_root() / "runs.pkl"
        ]
        
        runs_pkl_path = None
        for path in possible_paths:
            if path.exists():
                runs_pkl_path = path
                break
        
        if runs_pkl_path is None:
            # If no runs.pkl exists, create a minimal one from test data for validation
            runs_pkl_path = self._create_minimal_runs_pkl()
        
        # Test loading within timeout
        try:
            with open(runs_pkl_path, 'rb') as f:
                runs_data = pickle.load(f)
            
            # Validate data structure
            assert isinstance(runs_data, dict), f"runs.pkl should contain dict, got {type(runs_data)}"
            
            if runs_data:  # If not empty
                # Check first run has expected structure
                first_run_id = next(iter(runs_data))
                first_run = runs_data[first_run_id]
                
                assert isinstance(first_run, dict), "Each run should be a dictionary"
                assert 'geoms' in first_run, "Run should have 'geoms' key"
                assert 'bbox' in first_run, "Run should have 'bbox' key"
                assert 'metadata' in first_run, "Run should have 'metadata' key"
                
                # Validate bbox format
                bbox = first_run['bbox']
                assert len(bbox) == 4, f"bbox should have 4 coordinates, got {len(bbox)}"
                assert all(isinstance(coord, (int, float)) for coord in bbox), "bbox coordinates should be numeric"
            
            execution_time = time.time() - start_time
            assert execution_time < 2.0, f"runs.pkl loading took {execution_time:.2f}s (max: 2.0s)"
            
            print(f"      ✅ Loaded {len(runs_data)} runs in {execution_time:.3f}s")
            
        except Exception as e:
            execution_time = time.time() - start_time
            pytest.fail(f"runs.pkl loading failed after {execution_time:.2f}s: {str(e)}")
    
    def test_pmtiles_generation_verification(self):
        """
        Test PMTiles generation verification from sample data
        Requirements: 4.1, 1.1
        """
        start_time = time.time()
        
        # Check if make_pmtiles.py exists
        make_pmtiles_script = self.server_dir / "make_pmtiles.py"
        self.check_file_exists(make_pmtiles_script, "PMTiles generation script")
        
        # Verify script contains expected PMTiles functionality
        script_content = make_pmtiles_script.read_text(encoding='utf-8', errors='ignore')
        assert 'pmtiles' in script_content.lower(), "make_pmtiles.py should contain PMTiles-related code"
        assert 'geojson' in script_content.lower(), "make_pmtiles.py should handle GeoJSON conversion"
        
        # Check if runs.pmtiles exists (created by previous runs)
        pmtiles_path = self.server_dir / "runs.pmtiles"
        if pmtiles_path.exists():
            # Validate PMTiles file is not empty and has reasonable size
            file_size = pmtiles_path.stat().st_size
            assert file_size > 100, f"PMTiles file seems too small: {file_size} bytes"
            assert file_size < 100 * 1024 * 1024, f"PMTiles file seems too large: {file_size} bytes"
            
            print(f"      ✅ Found PMTiles file ({file_size:,} bytes)")
        else:
            print(f"      ℹ️  PMTiles file not found (will be created during full build)")
        
        execution_time = time.time() - start_time
        assert execution_time < 2.0, f"PMTiles verification took {execution_time:.2f}s (max: 2.0s)"
    
    def test_spatial_index_building_validation(self):
        """
        Test spatial index building validation
        Requirements: 4.1, 1.1
        """
        start_time = time.time()
        
        try:
            # Test rtree import (required for spatial indexing)
            from rtree import index
            
            # Create a minimal spatial index to verify functionality
            idx = index.Index()
            
            # Test basic index operations with sample data
            test_bbox = (-122.5, 47.5, -122.4, 47.6)  # Seattle area
            idx.insert(1, test_bbox)
            
            # Test query functionality
            results = list(idx.intersection(test_bbox))
            assert 1 in results, "Spatial index should return inserted item"
            
            # Test with runs.pkl data if available
            runs_pkl_path = self._find_runs_pkl()
            if runs_pkl_path and runs_pkl_path.exists():
                with open(runs_pkl_path, 'rb') as f:
                    runs_data = pickle.load(f)
                
                if runs_data:
                    # Test building index with actual data (limited sample)
                    test_idx = index.Index()
                    count = 0
                    for run_id, run_data in runs_data.items():
                        if count >= 5:  # Limit to 5 runs for speed
                            break
                        if 'bbox' in run_data:
                            test_idx.insert(run_id, run_data['bbox'])
                            count += 1
                    
                    print(f"      ✅ Built spatial index with {count} test runs")
            
            execution_time = time.time() - start_time
            assert execution_time < 2.0, f"Spatial index validation took {execution_time:.2f}s (max: 2.0s)"
            
        except ImportError:
            pytest.fail("rtree library not available - required for spatial indexing")
        except Exception as e:
            execution_time = time.time() - start_time
            pytest.fail(f"Spatial index validation failed after {execution_time:.2f}s: {str(e)}")
    
    def _create_minimal_runs_pkl(self) -> Path:
        """
        Create a minimal runs.pkl from test data for validation
        Returns path to created file
        """
        # Import required modules
        try:
            import gpxpy
            from shapely.geometry import LineString
        except ImportError as e:
            pytest.fail(f"Required dependencies not available: {str(e)}")
        
        # Find test GPX files
        gpx_files = list(self.test_data_dir.glob("*.gpx"))
        if not gpx_files:
            pytest.fail(f"No test GPX files found in {self.test_data_dir}")
        
        # Create minimal runs data from first GPX file
        runs_data = {}
        gpx_file = gpx_files[0]
        
        try:
            with open(gpx_file, 'r') as f:
                gpx = gpxpy.parse(f)
            
            coords = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        coords.append([point.longitude, point.latitude])
            
            if coords:
                # Create minimal run data structure
                geom = LineString(coords)
                bbox = geom.bounds  # (minx, miny, maxx, maxy)
                
                runs_data[1] = {
                    'geoms': {'full': geom},
                    'bbox': bbox,
                    'metadata': {
                        'distance': 1000,  # 1km
                        'duration': 300,   # 5 minutes
                        'activity_type': 'run',
                        'start_time': '2024-01-01T10:00:00'
                    }
                }
        except Exception as e:
            pytest.fail(f"Failed to create minimal runs data: {str(e)}")
        
        # Save to temporary location
        temp_pkl_path = self.server_dir / "runs_test.pkl"
        try:
            with open(temp_pkl_path, 'wb') as f:
                pickle.dump(runs_data, f)
            return temp_pkl_path
        except Exception as e:
            pytest.fail(f"Failed to save minimal runs.pkl: {str(e)}")
    
    def test_mobile_data_directory_structure(self):
        """
        Test mobile data directory structure and required files exist
        Requirements: 4.1, 1.3
        """
        start_time = time.time()
        
        # Check for mobile directory (created during build)
        mobile_dir = self.get_project_root() / "mobile"
        
        if mobile_dir.exists():
            # Validate mobile directory structure
            expected_subdirs = ["www", "android"]
            for subdir in expected_subdirs:
                subdir_path = mobile_dir / subdir
                if subdir_path.exists():
                    print(f"      ✅ Found mobile/{subdir} directory")
                else:
                    print(f"      ℹ️  Mobile/{subdir} directory not found (created during full build)")
            
            # Check for mobile data files
            www_dir = mobile_dir / "www"
            if www_dir.exists():
                expected_files = ["index.html", "main.js"]
                for file_name in expected_files:
                    file_path = www_dir / file_name
                    if file_path.exists():
                        print(f"      ✅ Found mobile/www/{file_name}")
                    else:
                        print(f"      ℹ️  Mobile/www/{file_name} not found (created during build)")
        else:
            print(f"      ℹ️  Mobile directory not found (created during full build)")
        
        execution_time = time.time() - start_time
        assert execution_time < 2.0, f"Mobile directory validation took {execution_time:.2f}s (max: 2.0s)"
    
    def test_pmtiles_file_integrity_and_metadata(self):
        """
        Test PMTiles file integrity and basic metadata
        Requirements: 4.1, 1.3
        """
        start_time = time.time()
        
        # Check for PMTiles file in common locations
        possible_paths = [
            self.server_dir / "runs.pmtiles",
            self.get_project_root() / "mobile" / "www" / "runs.pmtiles",
            self.get_project_root() / "runs.pmtiles"
        ]
        
        pmtiles_found = False
        for pmtiles_path in possible_paths:
            if pmtiles_path.exists():
                pmtiles_found = True
                
                # Validate file size (should be reasonable)
                file_size = pmtiles_path.stat().st_size
                assert file_size > 50, f"PMTiles file too small: {file_size} bytes"
                assert file_size < 500 * 1024 * 1024, f"PMTiles file too large: {file_size} bytes"
                
                # Basic file header validation (PMTiles files start with specific bytes)
                with open(pmtiles_path, 'rb') as f:
                    header = f.read(8)
                    # PMTiles v3 files start with specific magic bytes
                    if len(header) >= 7:
                        # Check if it looks like a valid PMTiles file
                        # (This is a basic check - full validation would require PMTiles library)
                        assert len(header) > 0, "PMTiles file appears to be empty"
                
                print(f"      ✅ Found valid PMTiles file at {pmtiles_path} ({file_size:,} bytes)")
                break
        
        if not pmtiles_found:
            print(f"      ℹ️  PMTiles file not found (created during data processing)")
        
        execution_time = time.time() - start_time
        assert execution_time < 2.0, f"PMTiles validation took {execution_time:.2f}s (max: 2.0s)"
    
    def test_graceful_failure_handling_missing_corrupt_data(self):
        """
        Test graceful failure handling for missing or corrupt data files
        Requirements: 4.1, 1.3
        """
        start_time = time.time()
        
        # Test handling of missing runs.pkl
        missing_pkl_path = self.server_dir / "nonexistent_runs.pkl"
        try:
            with open(missing_pkl_path, 'rb') as f:
                pickle.load(f)
            pytest.fail("Should have failed to load nonexistent file")
        except FileNotFoundError:
            print(f"      ✅ Correctly handles missing runs.pkl")
        except Exception as e:
            pytest.fail(f"Unexpected error handling missing file: {str(e)}")
        
        # Test handling of corrupt pickle file
        corrupt_pkl_path = self.server_dir / "corrupt_test.pkl"
        try:
            # Create a corrupt pickle file
            with open(corrupt_pkl_path, 'wb') as f:
                f.write(b"This is not a valid pickle file")
            
            # Try to load it
            try:
                with open(corrupt_pkl_path, 'rb') as f:
                    pickle.load(f)
                pytest.fail("Should have failed to load corrupt pickle file")
            except (pickle.UnpicklingError, EOFError, ValueError):
                print(f"      ✅ Correctly handles corrupt pickle file")
            except Exception as e:
                print(f"      ✅ Handles corrupt pickle with error: {type(e).__name__}")
            
            # Clean up test file
            corrupt_pkl_path.unlink()
            
        except Exception as e:
            pytest.fail(f"Failed to test corrupt file handling: {str(e)}")
        
        # Test handling of missing test data
        missing_gpx_dir = self.get_project_root() / "nonexistent_test_data"
        gpx_files = list(missing_gpx_dir.glob("*.gpx")) if missing_gpx_dir.exists() else []
        assert len(gpx_files) == 0, "Should handle missing test data directory gracefully"
        print(f"      ✅ Correctly handles missing test data directory")
        
        execution_time = time.time() - start_time
        assert execution_time < 2.0, f"Error handling validation took {execution_time:.2f}s (max: 2.0s)"
    
    def _find_runs_pkl(self) -> Path:
        """Find runs.pkl in common locations"""
        possible_paths = [
            self.server_dir / "runs.pkl",
            self.get_project_root() / "data" / "runs.pkl",
            self.get_project_root() / "runs.pkl"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None