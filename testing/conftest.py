
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
    A master, session-scoped fixture to handle all expensive, one-time setup operations.
    - Creates isolated test environment
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

    print("\n🧱 Master setup: Starting one-time test session environment setup...")
    
    test_env = Path(tempfile.mkdtemp(prefix="heatmap_master_session_"))
    server_dir = test_env / "server"
    raw_data_dir = test_env / "data" / "raw"
    
    try:
        # 1. Create isolated environment and copy necessary files
        print("1. Creating isolated environment...")
        server_dir.mkdir(parents=True)
        raw_data_dir.mkdir(parents=True)
        
        project_root = Path(__file__).parent.parent
        real_server_dir = project_root / "server"
        
        # Copy server scripts and templates
        files_to_copy = [
            "import_runs.py", "make_pmtiles.py", "build_mobile.py",
            "mobile_template.html", "mobile_main.js", "sw_template.js", 
            "spatial.worker.js", "AndroidManifest.xml.template", 
            "MainActivity.java.template", "HttpRangeServerPlugin.java.template",
            "network_security_config.xml.template"
        ]
        for file_name in files_to_copy:
            shutil.copy(real_server_dir / file_name, server_dir / file_name)

        # Copy test GPX data
        test_data_dir = Path(__file__).parent / "test_data"
        shutil.copy(test_data_dir / "sample_run.gpx", raw_data_dir / "test_run.gpx")
        shutil.copy(test_data_dir / "eastside_run.gpx", raw_data_dir / "eastside_run.gpx")

        # 2. Run data pipeline
        print("\n2. Running data pipeline (GPX import and PMTiles generation)...")
        main_venv_python = project_root / ".venv" / "bin" / "python"
        subprocess.run([str(main_venv_python), "import_runs.py"], cwd=server_dir, check=True, capture_output=True)
        subprocess.run([str(main_venv_python), "make_pmtiles.py"], cwd=server_dir, check=True, capture_output=True)
        pmtiles_path = server_dir / "runs.pmtiles"
        print("✅ Data pipeline complete.")

        # 3. Build mobile APK
        print("\n3. Building mobile APK with test data (this may take 5-10 minutes)...")
        isolated_mobile_dir = test_env / "mobile"
        isolated_mobile_dir.mkdir(exist_ok=True)
        
        # Create a custom build script that uses our test data
        isolated_build_script = isolated_mobile_dir / "build_mobile_test.py"
        build_script_content = f'''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, "{real_server_dir}")

# Override the SCRIPT_DIR to point to our test server directory
import build_mobile
build_mobile.SCRIPT_DIR = "{server_dir}"
build_mobile.PROJECT_ROOT = "{test_env}"
build_mobile.MOBILE_DIR = "{isolated_mobile_dir}"

if __name__ == '__main__':
    build_mobile.main()
'''
        
        with open(isolated_build_script, 'w') as f:
            f.write(build_script_content)
        
        # Run the isolated build using main venv python
        build_env = os.environ.copy()
        build_env['MOBILE_BUILD_AUTO'] = '1'
        build_process = subprocess.Popen([
            str(main_venv_python), str(isolated_build_script)
        ], cwd=isolated_mobile_dir, stdin=subprocess.PIPE, 
           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
           text=True, env=build_env)
        stdout, _ = build_process.communicate(input="y\ny\n", timeout=600)
        
        if build_process.returncode != 0:
            print(stdout)
            raise Exception(f"Master APK build failed with return code {build_process.returncode}")
        
        apk_path = isolated_mobile_dir / "android/app/build/outputs/apk/debug/app-debug.apk"
        if not apk_path.exists():
            raise Exception(f"APK not found at {apk_path}")
        print("✅ Mobile APK built successfully.")

        # 4. Install APK on emulator
        print("\n4. Installing test APK on emulator...")
        android_home = os.environ.get('ANDROID_HOME', f'{os.path.expanduser("~")}/android-sdk')
        adb_path = str(Path(android_home) / "platform-tools" / "adb")
        
        # Uninstall old version first
        subprocess.run([adb_path, "uninstall", "com.run.heatmap"], capture_output=True)
        
        # Install new APK
        install_result = subprocess.run([adb_path, "install", str(apk_path)], capture_output=True, text=True)
        if install_result.returncode != 0:
            raise Exception(f"APK installation failed: {install_result.stderr}")
        print("✅ Test APK installed successfully.")
        
        time.sleep(5) # Give system time to register app

        yield {
            'package_name': 'com.run.heatmap',
            'apk_path': apk_path,
            'pmtiles_path': pmtiles_path,
            'test_env': test_env
        }

    finally:
        if not fast_mode:
            print(f"\n🧹 Cleaning up master test environment: {test_env}")
            shutil.rmtree(test_env)

@pytest.fixture(scope="session")
def test_emulator_with_apk(session_setup):
    """Provides info about the installed app. Depends on the master setup."""
    yield session_setup

@pytest.fixture(scope="function")
def mobile_driver(test_emulator_with_apk):
    """
    Creates a fresh Appium driver for each test function.
    Ensures that the master setup (including APK installation) is complete before starting.
    """
    print("📱 Starting Appium session...")
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from selenium.webdriver.support.ui import WebDriverWait

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = "Android Emulator"
    options.app_package = test_emulator_with_apk['package_name']
    options.app_activity = f"{test_emulator_with_apk['package_name']}.MainActivity"
    options.auto_grant_permissions = True
    options.chromedriver_executable = str(Path(__file__).parent / "vetted-drivers/chromedriver-101")
    options.native_web_screenshot = True
    options.new_command_timeout = 300
    options.auto_webview = False
    
    # Force stop app before each test for a clean state
    android_home = os.environ.get('ANDROID_HOME', f'{os.path.expanduser("~")}/android-sdk')
    adb_path = str(Path(android_home) / "platform-tools" / "adb")
    subprocess.run([adb_path, "shell", "am", "force-stop", test_emulator_with_apk['package_name']], capture_output=True)
    time.sleep(2)

    driver = webdriver.Remote("http://localhost:4723/wd/hub", options=options)
    wait = WebDriverWait(driver, 30)
    
    yield {
        'driver': driver,
        'wait': wait,
        'apk_info': test_emulator_with_apk
    }
    
    print("📱 Closing Appium session...")
    driver.quit()
