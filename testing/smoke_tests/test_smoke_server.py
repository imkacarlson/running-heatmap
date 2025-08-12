"""
Smoke tests for server components
Fast validation of server setup and dependencies without full server startup
"""
import pytest
from .base_smoke_test import BaseSmokeTest


@pytest.mark.smoke
@pytest.mark.smoke_server
class TestServerSmoke(BaseSmokeTest):
    """Smoke tests for server infrastructure"""
    
    def test_server_files_exist(self):
        """Verify essential server files exist"""
        server_dir = self.get_server_dir()
        
        essential_files = [
            ("app.py", "Main Flask application"),
            ("import_runs.py", "GPX import script"),
            ("make_pmtiles.py", "PMTiles generation script"),
            ("build_mobile.py", "Mobile build script")
        ]
        
        for file_name, description in essential_files:
            file_path = server_dir / file_name
            self.check_file_exists(file_path, description)
    
    def test_server_dependencies_available(self):
        """Verify server Python dependencies are available"""
        # Core Flask dependencies
        self.check_python_import('flask', 'Flask web framework')
        
        # Data processing dependencies
        self.check_python_import('pickle', 'Pickle for data serialization')
        
        # Common server utilities
        try:
            import json
            import os
            import sys
            print("✅ Standard library modules available")
        except ImportError as e:
            pytest.fail(f"Standard library import failed: {e}")
    
    def test_flask_app_structure(self):
        """Verify Flask app file has expected structure"""
        app_py = self.get_server_dir() / "app.py"
        self.check_file_exists(app_py, "Flask application file")
        
        # Check for basic Flask app structure
        self.check_file_contains(app_py, "Flask", "Flask import")
        self.check_file_contains(app_py, "app =", "Flask app instance")
        
        # Check for common route patterns
        content = app_py.read_text(encoding='utf-8', errors='ignore')
        route_indicators = ["@app.route", "def ", "return"]
        
        for indicator in route_indicators:
            assert indicator in content, f"Flask app missing expected pattern: {indicator}"
    
    def test_data_processing_scripts_structure(self):
        """Verify data processing scripts have expected structure"""
        server_dir = self.get_server_dir()
        
        # Check import_runs.py
        import_script = server_dir / "import_runs.py"
        if import_script.exists():
            self.check_file_contains(import_script, "gpx", "GPX processing functionality")
        
        # Check make_pmtiles.py
        pmtiles_script = server_dir / "make_pmtiles.py"
        if pmtiles_script.exists():
            self.check_file_contains(pmtiles_script, "pmtiles", "PMTiles functionality")
    
    def test_server_configuration_files(self):
        """Verify server configuration and template files"""
        server_dir = self.get_server_dir()
        
        # Check for common configuration patterns
        config_files = [
            "requirements.txt",
            "mobile_template.html",
            "mobile_main.js"
        ]
        
        for config_file in config_files:
            file_path = server_dir / config_file
            if file_path.exists():
                print(f"✅ Found configuration file: {config_file}")
                
                # Basic validation
                assert file_path.stat().st_size > 0, f"Configuration file is empty: {config_file}"
    
    def test_server_port_availability_check(self):
        """Test that we can check for port availability (without starting server)"""
        import socket
        
        # Test common Flask development ports
        test_ports = [5000, 5001, 8000]
        
        for port in test_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            
            try:
                # Try to bind to the port
                result = sock.bind(('localhost', port))
                sock.close()
                print(f"✅ Port {port} available")
                break  # Found an available port
            except OSError:
                print(f"ℹ️  Port {port} in use or unavailable")
                sock.close()
                continue
        else:
            # All ports were unavailable - this might indicate a problem
            print("⚠️  All test ports appear to be in use")
    
    def test_server_environment_setup(self):
        """Verify server environment is properly set up"""
        import os
        import sys
        
        # Check Python version is reasonable
        python_version = sys.version_info
        assert python_version.major >= 3, f"Python 3+ required, found {python_version}"
        assert python_version.minor >= 7, f"Python 3.7+ recommended, found {python_version}"
        
        # Check current working directory makes sense
        cwd = os.getcwd()
        project_root_str = str(self.get_project_root())
        
        # We should be able to navigate to project root
        assert self.get_project_root().exists(), f"Project root not accessible: {project_root_str}"
        
        print(f"✅ Python {python_version.major}.{python_version.minor}")
        print(f"✅ Project root accessible: {project_root_str}")
    
    def test_server_static_assets(self):
        """Verify server static assets and templates exist"""
        server_dir = self.get_server_dir()
        
        # Check for static asset directories
        static_dirs = ["static", "templates"]
        
        for dir_name in static_dirs:
            dir_path = server_dir / dir_name
            if dir_path.exists():
                print(f"✅ Found static directory: {dir_name}")
                
                # Check it's not empty
                files = list(dir_path.glob("*"))
                if files:
                    print(f"   Contains {len(files)} files")
                else:
                    print(f"   Directory is empty")
        
        # Check for mobile-specific templates
        mobile_files = [
            "mobile_template.html",
            "mobile_main.js",
            "sw_template.js"
        ]
        
        for mobile_file in mobile_files:
            file_path = server_dir / mobile_file
            if file_path.exists():
                print(f"✅ Found mobile asset: {mobile_file}")
                
                # Basic content validation
                if mobile_file.endswith('.html'):
                    self.check_file_contains(file_path, "<html", "HTML structure")
                elif mobile_file.endswith('.js'):
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    # Just check it's not empty and looks like JavaScript
                    assert len(content.strip()) > 0, f"JavaScript file is empty: {mobile_file}"