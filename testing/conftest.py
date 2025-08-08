"""
pytest fixtures for GPX to mobile testing
Session-scoped fixtures handle expensive operations once per test session
"""
import os
import pytest
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import pytest_html

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--fast", 
        action="store_true", 
        default=False, 
        help="Skip expensive build operations (APK build, tile generation) for faster testing cycles"
    )

@pytest.fixture(scope="session")
def fast_mode(request):
    """Access the --fast flag value"""
    return request.config.getoption("--fast")

@pytest.fixture(scope="session")
def session_setup(fast_mode):
    """
    Infrastructure setup fixture to handle all expensive, one-time setup operations.
    - Creates isolated test environment with sample GPX data
    - Runs data pipeline (GPX import, PMTiles generation)
    - Builds mobile APK with test data
    - Installs APK on emulator
    This runs only ONCE per test session unless in --fast mode.
    """
    # Define project_root at the top so it's available for both modes
    project_root = Path(__file__).parent.parent
    
    if fast_mode:
        print("\n⚡ Fast mode: Using cached test APK from previous full build.")
        # In fast mode, look for cached test APK from previous full build
        # This APK should contain test data from a previous full test run
        cached_apk_path = project_root / "testing" / "cached_test_apk" / "app-debug.apk"
        cached_pmtiles_path = project_root / "testing" / "cached_test_data" / "runs.pmtiles"
        
        if not cached_apk_path.exists():
            raise Exception(
                f"❌ Fast mode requires cached test APK from previous full build.\n"
                f"   Expected: {cached_apk_path}\n"
                f"   💡 SOLUTION: Run full build first to create cached test APK:\n"
                f"      python run_tests.py --core\n"
                f"   Then fast mode will work:\n"
                f"      python run_tests.py --core --fast"
            )
        
        yield {
            'package_name': 'com.run.heatmap',
            'apk_path': str(cached_apk_path),
            'pmtiles_path': str(cached_pmtiles_path) if cached_pmtiles_path.exists() else None
        }
        return

    print("\n🏗️ Infrastructure Setup: Building test environment and APK with sample data...")
    
    test_env = Path(tempfile.mkdtemp(prefix="heatmap_master_session_"))
    server_dir = test_env / "server"
    raw_data_dir = test_env / "data" / "raw"
    
    try:
        # 1. Create isolated environment and copy necessary files
        print("   📁 Creating isolated test environment with sample GPX data...")
        server_dir.mkdir(parents=True)
        raw_data_dir.mkdir(parents=True)
        
        # Copy essential server files
        essential_files = [
            "import_runs.py", "make_pmtiles.py", "build_mobile.py",
            "mobile_template.html", "mobile_main.js", "sw_template.js", 
            "spatial.worker.js", "AndroidManifest.xml.template", 
            "MainActivity.java.template", "HttpRangeServerPlugin.java.template",
            "network_security_config.xml.template"
        ]
        
        for file_name in essential_files:
            src_file = project_root / "server" / file_name
            if src_file.exists():
                shutil.copy2(src_file, server_dir / file_name)
        
        # Copy essential directories
        essential_dirs = ["templates", "static"]
        for dir_name in essential_dirs:
            src_dir = project_root / "server" / dir_name
            dest_dir = server_dir / dir_name
            if src_dir.exists():
                if src_dir.is_dir():
                    shutil.copytree(src_dir, dest_dir)
                else:
                    # It's a file
                    shutil.copy2(src_dir, dest_dir)
        
        # Copy sample GPX data (exclude manual_upload_run.gpx - that's for manual upload testing only)
        test_data_dir = Path(__file__).parent / "test_data"
        if test_data_dir.exists():
            for gpx_file in test_data_dir.glob("*.gpx"):
                # Skip manual_upload_run.gpx - it should only be available for manual upload testing
                if gpx_file.name != "manual_upload_run.gpx":
                    shutil.copy2(gpx_file, raw_data_dir / gpx_file.name)
                    print(f"   📄 Including {gpx_file.name} in APK build")
                else:
                    print(f"   ⏭️  Excluding {gpx_file.name} from APK (manual upload testing only)")
        
        # 2. Process test data (GPX import and PMTiles generation)
        print("   🗂️ Processing test data (GPX import and PMTiles generation)...")
        
        # Use main project's .venv Python which has all server dependencies
        main_venv_python = project_root / ".venv" / "bin" / "python"
        
        print("   🔄 Running GPX import...")
        # Run import_runs.py first to process GPX data
        result = subprocess.run([
            str(main_venv_python), "import_runs.py"
        ], cwd=server_dir, text=True, timeout=120)
        
        if result.returncode != 0:
            raise Exception(f"GPX import failed with return code {result.returncode}")
        
        print("   🗜️ Running PMTiles generation...")
        # Run PMTiles generation
        result = subprocess.run([
            str(main_venv_python), "make_pmtiles.py"
        ], cwd=server_dir, text=True, timeout=120)
        
        if result.returncode != 0:
            raise Exception(f"PMTiles generation failed with return code {result.returncode}")
        
        print("   ✅ Test data processing complete.")
        
        # 3. Build mobile APK with test data
        print("   📱 Building mobile APK with test data (this may take 5-10 minutes)...")
        print("   🔍 APK Build Output (verbose mode):")
        
        # Run mobile build with auto mode and stdin input for prompts
        build_env = os.environ.copy()
        build_env['MOBILE_BUILD_AUTO'] = '1'  # Enable auto mode
        
        build_process = subprocess.Popen([
            str(main_venv_python), "build_mobile.py"
        ], cwd=server_dir, stdin=subprocess.PIPE, 
           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
           text=True, env=build_env)
        
        # Automatically answer "y" to any prompts
        stdout, _ = build_process.communicate(input="y\ny\n", timeout=600)
        
        # Show the output
        print(stdout)
        
        if build_process.returncode != 0:
            raise Exception(f"Mobile APK build failed with return code {build_process.returncode}")
        
        print("   ✅ Mobile APK built successfully.")
        
        # 4. Install APK on emulator
        print("   📲 Installing test APK on emulator...")
        apk_path = test_env / "mobile/android/app/build/outputs/apk/debug/app-debug.apk"
        
        if not apk_path.exists():
            raise Exception(f"APK not found at expected path: {apk_path}")
        
        # Install APK
        result = subprocess.run([
            "adb", "install", "-r", str(apk_path)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"APK installation failed: {result.stderr}")
        
        print("   ✅ Test APK installed successfully.")
        
        # 5. Cache test APK and data for future fast mode runs
        print("   💾 Caching test APK and data for future fast mode runs...")
        cached_apk_dir = project_root / "testing" / "cached_test_apk"
        cached_data_dir = project_root / "testing" / "cached_test_data"
        
        try:
            # Create cache directories
            cached_apk_dir.mkdir(parents=True, exist_ok=True)
            cached_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy test APK to cache
            cached_apk_path = cached_apk_dir / "app-debug.apk"
            shutil.copy2(apk_path, cached_apk_path)
            print(f"   📱 Cached test APK: {cached_apk_path}")
            
            # Copy PMTiles data to cache
            pmtiles_source = server_dir / "runs.pmtiles"
            if pmtiles_source.exists():
                cached_pmtiles_path = cached_data_dir / "runs.pmtiles"
                shutil.copy2(pmtiles_source, cached_pmtiles_path)
                print(f"   🗺️ Cached PMTiles data: {cached_pmtiles_path}")
                
            print("   ✅ Test artifacts cached for fast mode")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not cache test artifacts: {e}")
        
        # Provide session data to tests
        session_data = {
            'package_name': 'com.run.heatmap',
            'apk_path': str(apk_path),
            'pmtiles_path': str(server_dir / "runs.pmtiles"),
            'test_env': str(test_env),
            'server_dir': str(server_dir)
        }
        
        yield session_data
        
    finally:
        # Cleanup
        try:
            shutil.rmtree(test_env)
        except Exception as e:
            print(f"Warning: Could not clean up test environment: {e}")

@pytest.fixture(scope="function")
def mobile_driver(session_setup):
    """
    Provide Appium WebDriver instance for mobile tests.
    This fixture creates a driver instance and handles cleanup.
    """
    from appium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from pathlib import Path
    import config
    
    print(f"\n📱 Setting up mobile driver...")
    
    # Use test config for capabilities
    capabilities = config.TestConfig.ANDROID_CAPABILITIES.copy()
    
    # Use APK path from session setup (works for both fast and full mode)
    if session_setup.get('apk_path'):
        capabilities['appium:app'] = session_setup['apk_path']
    
    # Create WebDriver instance
    driver = webdriver.Remote(
        config.TestConfig.APPIUM_SERVER,
        capabilities
    )
    
    # Set implicit wait
    driver.implicitly_wait(config.TestConfig.IMPLICIT_WAIT)
    
    # Create WebDriverWait instance
    wait = WebDriverWait(driver, config.TestConfig.EXPLICIT_WAIT)
    
    print(f"✅ Mobile driver ready")
    
    # Yield driver and wait instance to tests
    yield {
        'driver': driver,
        'wait': wait,
        'session_data': session_setup
    }
    
    # Cleanup
    try:
        driver.quit()
        print("✅ Mobile driver cleanup completed")
    except Exception as e:
        print(f"⚠️ Mobile driver cleanup warning: {e}")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to ensure proper test report generation for HTML reports.
    This allows pytest-html to access stdout/stderr capture for log display.
    """
    outcome = yield
    report = outcome.get_result()
    
    # Only process during the "call" phase (actual test execution)
    if call.when != "call":
        return
    
    # Initialize extras list if it doesn't exist - this is REQUIRED for pytest-html
    if not hasattr(report, 'extra'):
        report.extra = []
    
    return report

