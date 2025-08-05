
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
import base64
import re
from pathlib import Path
from PIL import Image
import pytest_html
import datetime

# Global variable to track test session start time
TEST_SESSION_START_TIME = None

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

@pytest.fixture(scope="session", autouse=True)
def test_session_timestamp():
    """
    Initialize test session start time to filter screenshots by creation time.
    This fixture runs automatically for all test sessions.
    """
    global TEST_SESSION_START_TIME
    TEST_SESSION_START_TIME = datetime.datetime.now()
    print(f"\n🕐 Test session started at: {TEST_SESSION_START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    yield TEST_SESSION_START_TIME

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
        print("   🗃️ Processing test data (GPX import and PMTiles generation)...")
        main_venv_python = project_root / ".venv" / "bin" / "python"
        subprocess.run([str(main_venv_python), "import_runs.py"], cwd=server_dir, check=True, capture_output=True)
        subprocess.run([str(main_venv_python), "make_pmtiles.py"], cwd=server_dir, check=True, capture_output=True)
        pmtiles_path = server_dir / "runs.pmtiles"
        print("   ✅ Test data processing complete.")

        # 3. Build mobile APK
        print("   📱 Building mobile APK with test data (this may take 5-10 minutes)...")
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
        print("   ✅ Mobile APK built successfully.")

        # 4. Install APK on emulator
        print("   📲 Installing test APK on emulator...")
        android_home = os.environ.get('ANDROID_HOME', f'{os.path.expanduser("~")}/android-sdk')
        adb_path = str(Path(android_home) / "platform-tools" / "adb")
        
        # Uninstall old version first
        subprocess.run([adb_path, "uninstall", "com.run.heatmap"], capture_output=True)
        
        # Install new APK
        install_result = subprocess.run([adb_path, "install", str(apk_path)], capture_output=True, text=True)
        if install_result.returncode != 0:
            raise Exception(f"APK installation failed: {install_result.stderr}")
        print("   ✅ Test APK installed successfully.")
        
        time.sleep(5) # Give system time to register app

        yield {
            'package_name': 'com.run.heatmap',
            'apk_path': apk_path,
            'pmtiles_path': pmtiles_path,
            'test_env': test_env
        }

    finally:
        if not fast_mode:
            print(f"\n🧹 Cleaning up infrastructure test environment: {test_env}")
            shutil.rmtree(test_env)

@pytest.fixture(scope="session")
def test_emulator_with_apk(session_setup):
    """Provides info about the installed app. Depends on the infrastructure setup."""
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

def find_test_screenshots(test_nodeid, screenshots_dir):
    """
    Find screenshots associated with a specific test based on naming patterns.
    Only includes screenshots created during the current test session.
    
    Actual patterns found in the codebase:
    - lasso_basic_##_description.png (for lasso tests)
    - upload_##_description.png (for upload tests)  
    - ##_fixture_description.png (for fixture tests)
    - rock_solid_visibility_verified.png (for specific tests)
    """
    global TEST_SESSION_START_TIME
    
    if not screenshots_dir.exists():
        return []
    
    # Use session start time to filter screenshots, with fallback
    session_start = TEST_SESSION_START_TIME
    if session_start is None:
        # Fallback: use a time 1 minute ago if session time not available
        session_start = datetime.datetime.now() - datetime.timedelta(minutes=1)
        print(f"⚠️  Warning: Session start time not available, using fallback: {session_start}")
    
    # Extract test method name from nodeid (e.g., "test_file.py::TestClass::test_method")
    parts = test_nodeid.split("::")
    test_method = parts[-1] if parts else test_nodeid
    test_file = parts[0] if len(parts) > 0 else ""
    
    # Clean test method name (remove test_ prefix and parameter info)
    clean_test_name = re.sub(r'^test_', '', test_method)
    clean_test_name = re.sub(r'\[.*\]$', '', clean_test_name)  # Remove pytest parameters
    
    screenshots = []
    filtered_count = 0
    
    # Look for screenshots matching various patterns based on actual naming conventions
    for screenshot_file in screenshots_dir.glob("*.png"):
        # Check if screenshot was created during current test session
        try:
            file_mtime = datetime.datetime.fromtimestamp(screenshot_file.stat().st_mtime)
            if file_mtime < session_start:
                filtered_count += 1
                continue  # Skip old screenshots
        except Exception as e:
            print(f"Warning: Could not check timestamp for {screenshot_file}: {e}")
            continue
        
        filename = screenshot_file.name.lower()
        should_include = False
        
        # Pattern 1: Direct keyword matching for specific test types
        if "lasso" in test_file.lower() or "lasso" in test_method.lower():
            if "lasso" in filename:
                should_include = True
        
        if "upload" in test_file.lower() or "upload" in test_method.lower():
            if "upload" in filename:
                should_include = True
        
        if "fixture" in test_file.lower() or "fixture" in test_method.lower():
            if "fixture" in filename:
                should_include = True
        
        # Pattern 2: Specific test method patterns
        if "activity_definitely_visible" in test_method.lower() or "rock_solid" in test_method.lower():
            if "rock_solid" in filename or "fixture" in filename:
                should_include = True
        
        # Pattern 3: General patterns for other tests
        if not should_include:
            # Look for test method keywords in filename
            method_keywords = clean_test_name.lower().split('_')
            for keyword in method_keywords:
                if len(keyword) > 3 and keyword in filename:  # Only match meaningful keywords
                    should_include = True
                    break
        
        # Pattern 4: Fallback - check if filename contains any part of the test name
        if not should_include:
            if any([
                clean_test_name.lower() in filename,
                test_method.lower().replace('test_', '') in filename
            ]):
                should_include = True
        
        if should_include:
            screenshots.append(screenshot_file)
    
    # Sort screenshots by filename to maintain step order
    screenshots.sort(key=lambda x: x.name)
    
    # Report filtering results
    if filtered_count > 0:
        print(f"📸 Filtered out {filtered_count} old screenshots for {test_nodeid}")
    
    return screenshots

def create_screenshot_thumbnail(image_path, max_width=300):
    """Create a base64-encoded thumbnail of the screenshot for HTML embedding."""
    try:
        with Image.open(image_path) as img:
            # Calculate proportional height
            width, height = img.size
            if width > max_width:
                new_height = int((height * max_width) / width)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary (removes alpha channel)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as base64 JPEG for smaller size
            import io
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            img_data = buffer.getvalue()
            
            return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        print(f"Warning: Failed to create thumbnail for {image_path}: {e}")
        return None

def create_screenshot_full_base64(image_path):
    """Create a base64-encoded full-size image for modal viewing."""
    try:
        with open(image_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Warning: Failed to encode full image {image_path}: {e}")
        return None

def generate_screenshot_html(screenshots):
    """Generate HTML for displaying screenshots with modal viewer."""
    if not screenshots:
        return ""
    
    html_parts = []
    html_parts.append("""
    <div class="screenshots-section">
        <h4>📸 Test Screenshots ({} images)</h4>
        <div class="screenshots-container">
    """.format(len(screenshots)))
    
    for i, screenshot_path in enumerate(screenshots):
        # Create thumbnail and full-size base64 data
        thumbnail_b64 = create_screenshot_thumbnail(screenshot_path)
        full_b64 = create_screenshot_full_base64(screenshot_path)
        
        if not thumbnail_b64 or not full_b64:
            continue
            
        # Extract meaningful name from filename
        filename = screenshot_path.stem
        display_name = filename.replace('_', ' ').title()
        
        html_parts.append(f"""
            <div class="screenshot-item" style="display: inline-block; margin: 5px; text-align: center;">
                <div style="border: 1px solid #ddd; border-radius: 4px; padding: 5px; background: #f9f9f9;">
                    <img src="data:image/jpeg;base64,{thumbnail_b64}" 
                         alt="{display_name}"
                         style="cursor: pointer; max-width: 300px; display: block;"
                         onclick="showFullScreenshot('{full_b64}', '{display_name}')"
                         title="Click to view full size" />
                    <div style="font-size: 11px; color: #666; margin-top: 3px; max-width: 300px; word-wrap: break-word;">
                        {display_name}
                    </div>
                </div>
            </div>
        """)
    
    html_parts.append("""
        </div>
    </div>
    
    <!-- Modal for full-size image viewing -->
    <div id="screenshot-modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.8);" onclick="closeScreenshotModal()">
        <div style="position: relative; margin: auto; top: 50%; transform: translateY(-50%); max-width: 90%; max-height: 90%; text-align: center;">
            <img id="modal-screenshot" style="max-width: 100%; max-height: 100%; border-radius: 4px;" />
            <div id="modal-title" style="color: white; margin-top: 10px; font-size: 16px;"></div>
            <div style="color: #ccc; margin-top: 5px; font-size: 12px;">Click anywhere to close</div>
        </div>
    </div>
    
    <script>
    function showFullScreenshot(base64Data, title) {
        document.getElementById('modal-screenshot').src = 'data:image/png;base64,' + base64Data;
        document.getElementById('modal-title').textContent = title;
        document.getElementById('screenshot-modal').style.display = 'block';
        event.stopPropagation();
    }
    
    function closeScreenshotModal() {
        document.getElementById('screenshot-modal').style.display = 'none';
    }
    
    // Close modal on Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeScreenshotModal();
        }
    });
    </script>
    """)
    
    return ''.join(html_parts)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to add screenshots to HTML test reports.
    Automatically detects and embeds screenshots taken during test execution.
    """
    outcome = yield
    report = outcome.get_result()
    
    # Only add screenshots for the "call" phase (actual test execution)
    if call.when != "call":
        return
    
    # Find screenshots directory
    screenshots_dir = Path(__file__).parent / "screenshots"
    
    # Find screenshots for this test
    screenshots = find_test_screenshots(item.nodeid, screenshots_dir)
    
    if screenshots:
        # Generate HTML for screenshots
        screenshot_html = generate_screenshot_html(screenshots)
        
        if screenshot_html:
            # Add screenshots as HTML extra to the report
            extra = pytest_html.extras.html(screenshot_html)
            
            # Initialize extras list if it doesn't exist
            if not hasattr(report, 'extra'):
                report.extra = []
            
            report.extra.append(extra)
            
            # Add summary info
            print(f"📸 Added {len(screenshots)} screenshots to HTML report for {item.nodeid}")
    
    return report
