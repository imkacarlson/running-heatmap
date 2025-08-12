"""
Smoke Test Runner for Running Heatmap mobile app
Provides fast validation of core functionality without emulator overhead
"""
import time
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Make pytest optional for standalone usage
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create a dummy pytest module for type hints
    class DummyPytest:
        @staticmethod
        def fail(msg):
            raise Exception(msg)
    pytest = DummyPytest()


@dataclass
class TestFailure:
    """Represents a test failure with detailed information"""
    test_name: str
    error_message: str
    component: str  # 'server', 'api', 'web', 'data', 'build', 'mobile'
    suggestion: Optional[str] = None


@dataclass
class SmokeTestResult:
    """Results from smoke test execution"""
    total_tests: int
    passed: int
    failed: int
    execution_time: float
    failures: List[TestFailure]
    component_results: Dict[str, bool]  # component -> success status


@dataclass
class SmokeTestConfig:
    """Configuration for smoke tests with mobile-focused settings"""
    server_timeout: int = 3  # seconds
    api_timeout: int = 2     # seconds  
    web_timeout: int = 3     # seconds
    mobile_timeout: int = 5  # seconds for mobile-specific operations
    test_data_path: str = "testing/test_data"
    headless_browser: bool = True
    mobile_build_check: bool = True  # Check mobile build artifacts
    apk_validation: bool = True      # Validate APK existence and basic properties


class SmokeTestRunner:
    """
    Main smoke test runner with mobile-focused test discovery and execution
    Designed to run in under 5 seconds for rapid development feedback
    """
    
    def __init__(self, config: Optional[SmokeTestConfig] = None):
        self.config = config or SmokeTestConfig()
        self.start_time = None
        self.project_root = Path(__file__).parent.parent.parent
        
    def run_all_smoke_tests(self, components: Optional[List[str]] = None) -> SmokeTestResult:
        """
        Run all smoke tests or specific components
        
        Args:
            components: List of components to test ['server', 'api', 'web', 'data', 'build', 'mobile']
                       If None, runs all components
        """
        self.start_time = time.time()
        
        # Default to all components if none specified
        if components is None:
            components = ['data', 'server', 'api', 'web', 'build', 'mobile']
        
        print("🚀 Running smoke tests for mobile app...")
        print(f"📋 Components: {', '.join(components)}")
        
        failures = []
        component_results = {}
        total_tests = 0
        passed_tests = 0
        
        # Run tests for each component
        for component in components:
            print(f"\n🔍 Testing {component} component...")
            
            try:
                if component == 'data':
                    result = self._run_data_tests()
                elif component == 'server':
                    result = self._run_server_tests()
                elif component == 'api':
                    result = self._run_api_tests()
                elif component == 'web':
                    result = self._run_web_tests()
                elif component == 'build':
                    result = self._run_build_tests()
                elif component == 'mobile':
                    result = self._run_mobile_tests()
                else:
                    print(f"⚠️  Unknown component: {component}")
                    continue
                
                component_results[component] = result['success']
                total_tests += result['total']
                passed_tests += result['passed']
                
                if result['failures']:
                    failures.extend(result['failures'])
                
                status = "✅" if result['success'] else "❌"
                print(f"{status} {component}: {result['passed']}/{result['total']} tests passed")
                
            except Exception as e:
                print(f"❌ {component}: Critical error - {str(e)}")
                component_results[component] = False
                failures.append(TestFailure(
                    test_name=f"{component}_critical",
                    error_message=str(e),
                    component=component,
                    suggestion=f"Check {component} component setup and dependencies"
                ))
                total_tests += 1
        
        execution_time = time.time() - self.start_time
        
        result = SmokeTestResult(
            total_tests=total_tests,
            passed=passed_tests,
            failed=total_tests - passed_tests,
            execution_time=execution_time,
            failures=failures,
            component_results=component_results
        )
        
        self._print_summary(result)
        return result
    
    def _run_data_tests(self) -> Dict[str, Any]:
        """Test data pipeline components"""
        failures = []
        tests = [
            ("test_data_directory_exists", self._test_data_directory_exists),
            ("test_sample_gpx_files", self._test_sample_gpx_files),
            ("test_runs_pkl_loadable", self._test_runs_pkl_loadable)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
                print(f"   ✅ {test_name}")
            except Exception as e:
                failures.append(TestFailure(
                    test_name=test_name,
                    error_message=str(e),
                    component='data',
                    suggestion="Check test data setup and file permissions"
                ))
                print(f"   ❌ {test_name}: {str(e)}")
        
        return {
            'success': len(failures) == 0,
            'total': len(tests),
            'passed': passed,
            'failures': failures
        }
    
    def _run_server_tests(self) -> Dict[str, Any]:
        """Test server startup and basic functionality"""
        failures = []
        tests = [
            ("test_server_dependencies", self._test_server_dependencies),
            ("test_server_files_exist", self._test_server_files_exist)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
                print(f"   ✅ {test_name}")
            except Exception as e:
                failures.append(TestFailure(
                    test_name=test_name,
                    error_message=str(e),
                    component='server',
                    suggestion="Check server setup and Python dependencies"
                ))
                print(f"   ❌ {test_name}: {str(e)}")
        
        return {
            'success': len(failures) == 0,
            'total': len(tests),
            'passed': passed,
            'failures': failures
        }
    
    def _run_api_tests(self) -> Dict[str, Any]:
        """Test API endpoints (requires server to be running)"""
        # For now, just validate API test structure exists
        failures = []
        tests = [
            ("test_api_test_structure", self._test_api_test_structure)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
                print(f"   ✅ {test_name}")
            except Exception as e:
                failures.append(TestFailure(
                    test_name=test_name,
                    error_message=str(e),
                    component='api',
                    suggestion="API tests require server to be running"
                ))
                print(f"   ❌ {test_name}: {str(e)}")
        
        return {
            'success': len(failures) == 0,
            'total': len(tests),
            'passed': passed,
            'failures': failures
        }
    
    def _run_web_tests(self) -> Dict[str, Any]:
        """Test web interface components"""
        failures = []
        tests = [
            ("test_web_files_exist", self._test_web_files_exist),
            ("test_web_dependencies", self._test_web_dependencies)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
                print(f"   ✅ {test_name}")
            except Exception as e:
                failures.append(TestFailure(
                    test_name=test_name,
                    error_message=str(e),
                    component='web',
                    suggestion="Check web interface files and dependencies"
                ))
                print(f"   ❌ {test_name}: {str(e)}")
        
        return {
            'success': len(failures) == 0,
            'total': len(tests),
            'passed': passed,
            'failures': failures
        }
    
    def _run_build_tests(self) -> Dict[str, Any]:
        """Test mobile build process and artifacts"""
        failures = []
        tests = [
            ("test_build_scripts_exist", self._test_build_scripts_exist),
            ("test_mobile_templates_exist", self._test_mobile_templates_exist)
        ]
        
        if self.config.apk_validation:
            tests.append(("test_cached_apk_exists", self._test_cached_apk_exists))
        
        passed = 0
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
                print(f"   ✅ {test_name}")
            except Exception as e:
                failures.append(TestFailure(
                    test_name=test_name,
                    error_message=str(e),
                    component='build',
                    suggestion="Check mobile build setup and cached artifacts"
                ))
                print(f"   ❌ {test_name}: {str(e)}")
        
        return {
            'success': len(failures) == 0,
            'total': len(tests),
            'passed': passed,
            'failures': failures
        }
    
    def _run_mobile_tests(self) -> Dict[str, Any]:
        """Test mobile-specific components and configuration"""
        failures = []
        tests = [
            ("test_mobile_config_templates", self._test_mobile_config_templates),
            ("test_mobile_data_pipeline", self._test_mobile_data_pipeline)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
                print(f"   ✅ {test_name}")
            except Exception as e:
                failures.append(TestFailure(
                    test_name=test_name,
                    error_message=str(e),
                    component='mobile',
                    suggestion="Check mobile app configuration and data pipeline"
                ))
                print(f"   ❌ {test_name}: {str(e)}")
        
        return {
            'success': len(failures) == 0,
            'total': len(tests),
            'passed': passed,
            'failures': failures
        }
    
    # Individual test methods
    def _test_data_directory_exists(self):
        """Test that test data directory exists"""
        test_data_path = Path(self.config.test_data_path)
        if not test_data_path.exists():
            raise Exception(f"Test data directory not found: {test_data_path}")
    
    def _test_sample_gpx_files(self):
        """Test that sample GPX files exist"""
        test_data_path = Path(self.config.test_data_path)
        gpx_files = list(test_data_path.glob("*.gpx"))
        if not gpx_files:
            raise Exception(f"No GPX files found in {test_data_path}")
        if len(gpx_files) < 2:
            raise Exception(f"Expected at least 2 GPX files, found {len(gpx_files)}")
    
    def _test_runs_pkl_loadable(self):
        """Test that runs.pkl can be loaded if it exists"""
        import pickle
        
        # Check common locations for runs.pkl
        possible_paths = [
            self.project_root / "server" / "runs.pkl",
            self.project_root / "data" / "runs.pkl",
            Path("runs.pkl")
        ]
        
        runs_pkl_found = False
        for pkl_path in possible_paths:
            if pkl_path.exists():
                runs_pkl_found = True
                try:
                    with open(pkl_path, 'rb') as f:
                        data = pickle.load(f)
                    if not isinstance(data, (list, dict)):
                        raise Exception(f"runs.pkl contains invalid data type: {type(data)}")
                    break
                except Exception as e:
                    raise Exception(f"Failed to load runs.pkl from {pkl_path}: {str(e)}")
        
        # It's OK if runs.pkl doesn't exist yet - it gets created during data processing
        if runs_pkl_found:
            print(f"      Found and validated runs.pkl")
    
    def _test_server_dependencies(self):
        """Test that server dependencies are available"""
        try:
            import flask
            import pickle
        except ImportError as e:
            raise Exception(f"Missing server dependency: {str(e)}")
    
    def _test_server_files_exist(self):
        """Test that essential server files exist"""
        server_dir = self.project_root / "server"
        essential_files = [
            "app.py",
            "import_runs.py", 
            "make_pmtiles.py",
            "build_mobile.py"
        ]
        
        for file_name in essential_files:
            file_path = server_dir / file_name
            if not file_path.exists():
                raise Exception(f"Essential server file missing: {file_path}")
    
    def _test_api_test_structure(self):
        """Test that API test structure is ready"""
        # This is a placeholder - actual API tests will be implemented in later tasks
        pass
    
    def _test_web_files_exist(self):
        """Test that web interface files exist"""
        web_dir = self.project_root / "web"
        essential_files = ["index.html", "main.js"]
        
        for file_name in essential_files:
            file_path = web_dir / file_name
            if not file_path.exists():
                raise Exception(f"Essential web file missing: {file_path}")
    
    def _test_web_dependencies(self):
        """Test web dependencies (basic check)"""
        # For now, just check that web files contain expected content
        web_dir = self.project_root / "web"
        index_html = web_dir / "index.html"
        
        if index_html.exists():
            content = index_html.read_text()
            if "map" not in content.lower():
                raise Exception("index.html doesn't appear to contain map-related content")
    
    def _test_build_scripts_exist(self):
        """Test that mobile build scripts exist"""
        server_dir = self.project_root / "server"
        build_files = [
            "build_mobile.py",
            "mobile_template.html",
            "mobile_main.js"
        ]
        
        for file_name in build_files:
            file_path = server_dir / file_name
            if not file_path.exists():
                raise Exception(f"Mobile build file missing: {file_path}")
    
    def _test_mobile_templates_exist(self):
        """Test that mobile configuration templates exist"""
        server_dir = self.project_root / "server"
        template_files = [
            "AndroidManifest.xml.template",
            "MainActivity.java.template",
            "HttpRangeServerPlugin.java.template"
        ]
        
        for file_name in template_files:
            file_path = server_dir / file_name
            if not file_path.exists():
                raise Exception(f"Mobile template missing: {file_path}")
    
    def _test_cached_apk_exists(self):
        """Test that cached APK exists for fast mode testing"""
        cached_apk_path = self.project_root / "testing" / "cached_test_apk" / "app-debug.apk"
        if not cached_apk_path.exists():
            raise Exception(f"Cached APK not found: {cached_apk_path}. Run full build first.")
    
    def _test_mobile_config_templates(self):
        """Test mobile configuration templates are valid"""
        server_dir = self.project_root / "server"
        
        # Check AndroidManifest template has required components
        manifest_template = server_dir / "AndroidManifest.xml.template"
        if manifest_template.exists():
            content = manifest_template.read_text()
            required_components = ["MainActivity", "android.permission.INTERNET"]
            for component in required_components:
                if component not in content:
                    raise Exception(f"AndroidManifest.xml.template missing component: {component}")
    
    def _test_mobile_data_pipeline(self):
        """Test mobile data pipeline components"""
        server_dir = self.project_root / "server"
        
        # Check that PMTiles generation script exists and looks valid
        pmtiles_script = server_dir / "make_pmtiles.py"
        if pmtiles_script.exists():
            try:
                content = pmtiles_script.read_text(encoding='utf-8', errors='ignore')
                if "pmtiles" not in content.lower():
                    raise Exception("make_pmtiles.py doesn't appear to contain PMTiles-related code")
            except UnicodeDecodeError:
                # Try with different encoding
                content = pmtiles_script.read_text(encoding='latin-1', errors='ignore')
                if "pmtiles" not in content.lower():
                    raise Exception("make_pmtiles.py doesn't appear to contain PMTiles-related code")
    
    def _print_summary(self, result: SmokeTestResult):
        """Print comprehensive test summary"""
        print(f"\n{'='*60}")
        print("🏁 SMOKE TEST SUMMARY")
        print(f"{'='*60}")
        
        # Overall result
        if result.failed == 0:
            print("✅ RESULT: All smoke tests passed!")
        else:
            print(f"❌ RESULT: {result.failed}/{result.total_tests} tests failed")
        
        # Performance
        print(f"⏱️  EXECUTION TIME: {result.execution_time:.2f} seconds")
        target_time = 5.0
        if result.execution_time <= target_time:
            print(f"🎯 PERFORMANCE: ✅ Under {target_time}s target")
        else:
            print(f"🎯 PERFORMANCE: ⚠️  Over {target_time}s target")
        
        # Component breakdown
        print(f"\n📊 COMPONENT RESULTS:")
        for component, success in result.component_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {component}")
        
        # Failures detail
        if result.failures:
            print(f"\n❌ FAILURES ({len(result.failures)}):")
            for failure in result.failures:
                print(f"   • {failure.component}/{failure.test_name}: {failure.error_message}")
                if failure.suggestion:
                    print(f"     💡 {failure.suggestion}")
        
        print(f"{'='*60}")


def run_smoke_tests_with_pytest(components: Optional[List[str]] = None, 
                                verbose: bool = False) -> int:
    """
    Run smoke tests using pytest integration
    Returns exit code (0 for success, 1 for failure)
    """
    if not PYTEST_AVAILABLE:
        print("⚠️  pytest not available. Using direct runner instead.")
        runner = SmokeTestRunner()
        result = runner.run_all_smoke_tests(components)
        return 0 if result.failed == 0 else 1
    
    # Discover smoke test files
    smoke_test_dir = Path(__file__).parent
    test_files = list(smoke_test_dir.glob("test_smoke_*.py"))
    
    if not test_files:
        print("⚠️  No smoke test files found. Run SmokeTestRunner directly.")
        runner = SmokeTestRunner()
        result = runner.run_all_smoke_tests(components)
        return 0 if result.failed == 0 else 1
    
    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']
    cmd.extend([str(f) for f in test_files])
    cmd.extend(['-m', 'smoke'])
    
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    # Add component filtering if specified
    if components:
        # This would require custom pytest markers for each component
        # For now, run all smoke tests
        pass
    
    print(f"🧪 Running smoke tests with pytest...")
    print(f"📋 Command: {' '.join(cmd)}")
    
    import subprocess
    result = subprocess.run(cmd, cwd=smoke_test_dir.parent)
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run smoke tests for Running Heatmap mobile app")
    parser.add_argument('--components', nargs='+', 
                       choices=['data', 'server', 'api', 'web', 'build', 'mobile'],
                       help='Specific components to test')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--pytest', action='store_true',
                       help='Use pytest integration instead of direct runner')
    
    args = parser.parse_args()
    
    if args.pytest:
        exit_code = run_smoke_tests_with_pytest(args.components, args.verbose)
    else:
        runner = SmokeTestRunner()
        result = runner.run_all_smoke_tests(args.components)
        exit_code = 0 if result.failed == 0 else 1
    
    sys.exit(exit_code)