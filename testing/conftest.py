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
    if fast_mode:
        print("\n⚡ Fast mode: Skipping all setup, assuming app is already installed.")
        # In fast mode, we just need to provide the package name
        yield {
            'package_name': 'com.run.heatmap',
            'apk_path': None, # Not needed in fast mode
            'pmtiles_path': None # Not needed in fast mode
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
        
        project_root = Path(__file__).parent.parent
        
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
        
        # Copy sample GPX data
        test_data_dir = Path(__file__).parent / "test_data"
        if test_data_dir.exists():
            for gpx_file in test_data_dir.glob("*.gpx"):
                shutil.copy2(gpx_file, raw_data_dir / gpx_file.name)
        
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
    
    # In fast mode, we don't need to specify the app path since it's already installed
    if session_setup.get('apk_path'):
        capabilities['appium:app'] = session_setup['apk_path']
    else:
        # Fast mode: just specify the package to connect to existing installation
        capabilities['appium:appPackage'] = session_setup['package_name']
        capabilities['appium:appActivity'] = 'com.run.heatmap.MainActivity'
        # Remove app key to prevent reinstallation in fast mode
        capabilities.pop('appium:app', None)
    
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

