"""
Base class for smoke tests with common functionality
Focused on mobile testing infrastructure and rapid validation
"""
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

# Make pytest optional for standalone usage
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create a dummy pytest module for compatibility
    class DummyPytest:
        @staticmethod
        def fail(msg):
            raise AssertionError(msg)
    pytest = DummyPytest()


class BaseSmokeTest:
    """
    Base class for smoke tests providing common mobile-focused functionality
    Designed for tests that run in under 5 seconds total
    """
    
    @classmethod
    def setup_class(cls):
        """Class-level setup for smoke tests"""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.start_time = time.time()
        
    @classmethod
    def teardown_class(cls):
        """Class-level teardown with timing validation"""
        execution_time = time.time() - cls.start_time
        if execution_time > 5.0:
            print(f"⚠️  Warning: Smoke test class took {execution_time:.2f}s (target: <5s)")
    
    def setup_method(self):
        """Method-level setup"""
        self.test_start_time = time.time()
    
    def teardown_method(self):
        """Method-level teardown with timing validation"""
        execution_time = time.time() - self.test_start_time
        if execution_time > 2.0:
            print(f"⚠️  Warning: Individual smoke test took {execution_time:.2f}s (target: <2s)")
    
    def get_project_root(self) -> Path:
        """Get project root directory"""
        return self.project_root
    
    def get_server_dir(self) -> Path:
        """Get server directory"""
        return self.project_root / "server"
    
    def get_web_dir(self) -> Path:
        """Get web directory"""
        return self.project_root / "web"
    
    def get_test_data_dir(self) -> Path:
        """Get test data directory"""
        return self.project_root / "testing" / "test_data"
    
    def get_cached_apk_path(self) -> Path:
        """Get cached APK path for fast mode testing"""
        return self.project_root / "testing" / "cached_test_apk" / "app-debug.apk"
    
    def check_file_exists(self, file_path: Path, description: str = None) -> bool:
        """
        Check if file exists with descriptive error message
        
        Args:
            file_path: Path to check
            description: Human-readable description of the file
            
        Returns:
            True if file exists
            
        Raises:
            AssertionError: If file doesn't exist
        """
        desc = description or str(file_path)
        assert file_path.exists(), f"{desc} not found: {file_path}"
        return True
    
    def check_directory_exists(self, dir_path: Path, description: str = None) -> bool:
        """
        Check if directory exists with descriptive error message
        
        Args:
            dir_path: Directory path to check
            description: Human-readable description of the directory
            
        Returns:
            True if directory exists
            
        Raises:
            AssertionError: If directory doesn't exist
        """
        desc = description or str(dir_path)
        assert dir_path.exists() and dir_path.is_dir(), f"{desc} directory not found: {dir_path}"
        return True
    
    def check_file_contains(self, file_path: Path, content: str, description: str = None) -> bool:
        """
        Check if file contains specific content
        
        Args:
            file_path: Path to file
            content: Content to search for
            description: Human-readable description
            
        Returns:
            True if content found
            
        Raises:
            AssertionError: If content not found or file doesn't exist
        """
        desc = description or f"{file_path} contains '{content}'"
        assert file_path.exists(), f"File not found for content check: {file_path}"
        
        file_content = file_path.read_text(encoding='utf-8', errors='ignore')
        assert content in file_content, f"{desc} - content not found in {file_path}"
        return True
    
    def check_python_import(self, module_name: str, description: str = None) -> bool:
        """
        Check if Python module can be imported
        
        Args:
            module_name: Name of module to import
            description: Human-readable description
            
        Returns:
            True if import successful
            
        Raises:
            AssertionError: If import fails
        """
        desc = description or f"Python module '{module_name}'"
        try:
            __import__(module_name)
            return True
        except ImportError as e:
            pytest.fail(f"{desc} import failed: {str(e)}")
    
    def run_quick_command(self, cmd: list, timeout: int = 3, 
                         description: str = None) -> subprocess.CompletedProcess:
        """
        Run a quick command with timeout for smoke tests
        
        Args:
            cmd: Command to run as list
            timeout: Timeout in seconds (default 3)
            description: Human-readable description
            
        Returns:
            CompletedProcess result
            
        Raises:
            AssertionError: If command fails or times out
        """
        desc = description or f"Command: {' '.join(cmd)}"
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=self.project_root
            )
            return result
        except subprocess.TimeoutExpired:
            pytest.fail(f"{desc} timed out after {timeout}s")
        except Exception as e:
            pytest.fail(f"{desc} failed: {str(e)}")
    
    def validate_mobile_template(self, template_path: Path, 
                                required_placeholders: list) -> bool:
        """
        Validate mobile configuration template has required placeholders
        
        Args:
            template_path: Path to template file
            required_placeholders: List of required placeholder strings
            
        Returns:
            True if all placeholders found
            
        Raises:
            AssertionError: If template invalid or placeholders missing
        """
        assert template_path.exists(), f"Mobile template not found: {template_path}"
        
        content = template_path.read_text(encoding='utf-8', errors='ignore')
        
        for placeholder in required_placeholders:
            assert placeholder in content, \
                f"Mobile template {template_path} missing placeholder: {placeholder}"
        
        return True
    
    def check_mobile_build_artifacts(self) -> Dict[str, bool]:
        """
        Check for mobile build artifacts and return status
        
        Returns:
            Dictionary with artifact names and their existence status
        """
        server_dir = self.get_server_dir()
        
        artifacts = {
            'build_script': (server_dir / "build_mobile.py").exists(),
            'mobile_template': (server_dir / "mobile_template.html").exists(),
            'mobile_main_js': (server_dir / "mobile_main.js").exists(),
            'android_manifest_template': (server_dir / "AndroidManifest.xml.template").exists(),
            'main_activity_template': (server_dir / "MainActivity.java.template").exists(),
            'http_plugin_template': (server_dir / "HttpRangeServerPlugin.java.template").exists(),
        }
        
        return artifacts
    
    def get_test_execution_time(self) -> float:
        """Get current test execution time"""
        return time.time() - self.test_start_time
    
    def assert_fast_execution(self, max_time: float = 2.0):
        """Assert that test is executing within time limit"""
        current_time = self.get_test_execution_time()
        assert current_time <= max_time, \
            f"Smoke test too slow: {current_time:.2f}s (max: {max_time}s)"