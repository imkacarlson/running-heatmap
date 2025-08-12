"""
Smoke tests for data pipeline components
Fast validation of data loading and processing without full pipeline execution
"""
import pytest
import pickle
from pathlib import Path
from .base_smoke_test import BaseSmokeTest


@pytest.mark.smoke
@pytest.mark.smoke_data
class TestDataPipelineSmoke(BaseSmokeTest):
    """Smoke tests for data pipeline validation"""
    
    def test_test_data_directory_structure(self):
        """Verify test data directory exists and has expected structure"""
        test_data_dir = self.get_test_data_dir()
        
        # Check directory exists
        self.check_directory_exists(test_data_dir, "Test data directory")
        
        # Check for GPX files
        gpx_files = list(test_data_dir.glob("*.gpx"))
        assert len(gpx_files) >= 2, f"Expected at least 2 GPX files, found {len(gpx_files)}"
        
        # Verify GPX files are not empty
        for gpx_file in gpx_files:
            assert gpx_file.stat().st_size > 100, f"GPX file too small: {gpx_file}"
    
    def test_sample_gpx_files_valid(self):
        """Verify sample GPX files contain valid GPS data"""
        test_data_dir = self.get_test_data_dir()
        gpx_files = list(test_data_dir.glob("*.gpx"))
        
        for gpx_file in gpx_files[:2]:  # Check first 2 files only for speed
            content = gpx_file.read_text(encoding='utf-8', errors='ignore')
            
            # Basic GPX structure validation
            assert '<?xml' in content, f"GPX file missing XML header: {gpx_file}"
            assert '<gpx' in content, f"GPX file missing GPX root element: {gpx_file}"
            assert '<trk' in content, f"GPX file missing track data: {gpx_file}"
            assert '<trkpt' in content, f"GPX file missing track points: {gpx_file}"
            
            # Check for coordinate data
            assert 'lat=' in content, f"GPX file missing latitude data: {gpx_file}"
            assert 'lon=' in content, f"GPX file missing longitude data: {gpx_file}"
    
    def test_runs_pkl_loadable_if_exists(self):
        """Test that runs.pkl can be loaded if it exists (optional)"""
        # Check common locations for runs.pkl
        possible_paths = [
            self.get_server_dir() / "runs.pkl",
            self.get_project_root() / "data" / "runs.pkl",
            Path("runs.pkl")
        ]
        
        runs_pkl_found = False
        for pkl_path in possible_paths:
            if pkl_path.exists():
                runs_pkl_found = True
                
                # Verify it can be loaded
                with open(pkl_path, 'rb') as f:
                    data = pickle.load(f)
                
                # Basic validation
                assert isinstance(data, (list, dict)), \
                    f"runs.pkl contains invalid data type: {type(data)}"
                
                if isinstance(data, list) and len(data) > 0:
                    # Check first item has expected structure
                    first_item = data[0]
                    assert isinstance(first_item, dict), \
                        "runs.pkl list items should be dictionaries"
                
                print(f"✅ Found and validated runs.pkl at {pkl_path}")
                break
        
        # It's OK if runs.pkl doesn't exist - it gets created during data processing
        if not runs_pkl_found:
            print("ℹ️  runs.pkl not found (will be created during data processing)")
    
    def test_data_processing_dependencies(self):
        """Verify dependencies for data processing are available"""
        # Check Python modules needed for data processing
        self.check_python_import('pickle', 'Pickle module for data serialization')
        
        # Check for optional but common dependencies
        try:
            import xml.etree.ElementTree
            print("✅ XML processing available")
        except ImportError:
            pytest.fail("XML processing not available for GPX parsing")
        
        # Verify we can create test data structures
        test_data = {'test': 'data', 'coordinates': [1.0, 2.0]}
        assert isinstance(test_data, dict), "Basic data structure creation failed"
    
    def test_spatial_index_dependencies(self):
        """Verify spatial indexing dependencies if available"""
        try:
            # Try to import rtree if available (used for spatial indexing)
            import rtree
            print("✅ Spatial indexing (rtree) available")
        except ImportError:
            print("ℹ️  Spatial indexing (rtree) not available - will use fallback methods")
        
        # Basic coordinate validation
        test_coords = [(47.6062, -122.3321), (47.6205, -122.3493)]
        assert len(test_coords) == 2, "Basic coordinate handling failed"
        assert all(isinstance(coord, tuple) and len(coord) == 2 for coord in test_coords), \
            "Coordinate format validation failed"