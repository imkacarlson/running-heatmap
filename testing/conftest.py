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

# Modularized cleanup utilities for reuse across scripts
def cleanup_test_environment(test_env_path):
    """
    Clean up isolated test environment.
    Reusable utility for cleaning up temporary test directories.
    """
    try:
        if test_env_path and Path(test_env_path).exists():
            shutil.rmtree(test_env_path)
            print(f"✅ Test environment cleaned up: {test_env_path}")
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up test environment {test_env_path}: {e}")

def cleanup_mobile_driver(driver):
    """
    Clean up mobile driver instance.
    Reusable utility for driver cleanup that can be shared between scripts.
    """
    try:
        if driver:
            driver.quit()
            print("✅ Mobile driver cleanup completed")
    except Exception as e:
        print(f"⚠️ Mobile driver cleanup warning: {e}")

def cleanup_app_installation(package_name=None):
    """
    Clean up mobile app installation.
    Reusable utility for removing test app from emulator.
    """
    try:
        if package_name:
            result = subprocess.run([
                "adb", "uninstall", package_name
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ App uninstalled: {package_name}")
            else:
                print(f"⚠️ App uninstall warning: {result.stderr.strip()}")
    except Exception as e:
        print(f"⚠️ App uninstall warning: {e}")

def cleanup_emulator_state():
    """
    Clean up emulator state for consistent testing.
    Reusable utility for clearing emulator state between test runs.
    """
    try:
        # Clear logcat
        subprocess.run(["adb", "logcat", "-c"], capture_output=True, timeout=10)
        
        # Clear cached data if needed
        subprocess.run([
            "adb", "shell", "pm", "clear", "com.android.providers.downloads"
        ], capture_output=True, timeout=10)
        
        print("✅ Emulator state cleaned")
    except Exception as e:
        print(f"⚠️ Emulator state cleanup warning: {e}")

def cleanup_all_test_artifacts(package_name="com.run.heatmap", test_env_path=None, driver=None):
    """
    Comprehensive cleanup utility that combines all cleanup operations.
    Suitable for use in both isolated and persistent test modes.
    """
    print("🧹 Starting comprehensive test cleanup...")
    
    # Clean up driver
    cleanup_mobile_driver(driver)
    
    # Clean up app
    cleanup_app_installation(package_name)
    
    # Clean up emulator state
    cleanup_emulator_state()
    
    # Clean up test environment
    cleanup_test_environment(test_env_path)
    
    print("✅ Comprehensive cleanup completed")

def configure_emulator_stability():
    """
    Configure emulator settings for deterministic test behavior.
    Disables animations and sets consistent density/font scaling.
    """
    stability_commands = [
        # Disable all animations for deterministic behavior
        ['adb', 'shell', 'settings', 'put', 'global', 'window_animation_scale', '0'],
        ['adb', 'shell', 'settings', 'put', 'global', 'transition_animation_scale', '0'],
        ['adb', 'shell', 'settings', 'put', 'global', 'animator_duration_scale', '0'],
        # Set consistent density (420 is standard for many devices)
        ['adb', 'shell', 'wm', 'density', '420'],
        # Set consistent font scaling
        ['adb', 'shell', 'settings', 'put', 'system', 'font_scale', '1.0'],
        # Lock orientation and screen size for WebView stability
        ['adb', 'shell', 'settings', 'put', 'system', 'accelerometer_rotation', '0'],
        ['adb', 'shell', 'settings', 'put', 'system', 'user_rotation', '0'],  # 0 = portrait
        ['adb', 'shell', 'wm', 'size', '1080x1920'],
    ]
    
    print("   🎛️  Configuring emulator for deterministic behavior...")
    
    for cmd in stability_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                setting_name = cmd[-2] if len(cmd) > 3 else "setting"
                print(f"   ✅ {setting_name} = {cmd[-1]}")
            else:
                print(f"   ⚠️  Warning: {' '.join(cmd)} failed: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Warning: {' '.join(cmd)} timed out")
        except Exception as e:
            print(f"   ⚠️  Warning: {' '.join(cmd)} error: {e}")
    
    print("   ✅ Emulator stability configuration complete")

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--fast", 
        action="store_true", 
        default=False, 
        help="Skip expensive build operations (APK build, tile generation) for faster testing cycles"
    )

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", 
        "needs_clean_state: mark test to automatically reset app state before execution for test isolation"
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
    
    Now includes automatic change detection to skip expensive operations when unchanged:
    - Skip APK build when source files unchanged, use existing APK
    - Skip data processing when GPX files unchanged, use existing PMTiles
    """
    # Define project_root at the top so it's available for both modes
    project_root = Path(__file__).parent.parent
    
    # Import change detector for automatic optimization
    from change_detector import ChangeDetector, BuildOptimization
    
    # Initialize change detector
    change_detector = ChangeDetector(project_root)
    
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
    
    # Automatic optimization mode: analyze what needs to be built
    print("\n🔍 Analyzing changes to optimize test build process...")
    optimization = change_detector.get_build_optimization()
    
    print(f"   📊 Build Analysis:")
    print(f"      APK exists: {optimization.apk_exists}")
    print(f"      Source unchanged: {optimization.source_unchanged}")
    print(f"      Data unchanged: {optimization.data_unchanged}")
    print(f"      Can skip build: {optimization.can_skip_build}")
    print(f"      Can skip data: {optimization.can_skip_data}")
    
    # If we can use cached artifacts, use them directly
    if optimization.can_skip_build and optimization.can_skip_data:
        print("\n⚡ Optimization: All cached artifacts are up-to-date, using existing APK and data.")
        cached_apk_path = project_root / "testing" / "cached_test_apk" / "app-debug.apk"
        cached_pmtiles_path = project_root / "testing" / "cached_test_data" / "runs.pmtiles"
        
        yield {
            'package_name': 'com.run.heatmap',
            'apk_path': str(cached_apk_path),
            'pmtiles_path': str(cached_pmtiles_path) if cached_pmtiles_path.exists() else None
        }
        return

    # Determine what needs to be built based on optimization analysis
    need_apk_build = not optimization.can_skip_build
    need_data_processing = not optimization.can_skip_data
    
    print(f"\n🏗️ Infrastructure Setup: Building test environment")
    print(f"   📱 APK build needed: {need_apk_build}")
    print(f"   🗂️ Data processing needed: {need_data_processing}")
    
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
            "process_data.py", "build_mobile.py",
            "mobile_template.html", "mobile_main.js", "sw_template.js", 
            "spatial.worker.js", "AndroidManifest.xml.template", 
            "MainActivity.java.template", "HttpRangeServerPlugin.java.template",
            "network_security_config.xml.template"
        ]
        
        for file_name in essential_files:
            src_file = project_root / "server" / file_name
            if src_file.exists():
                shutil.copy2(src_file, server_dir / file_name)
        
        # Copy package.json and node_modules for mobile build dependencies
        package_json = project_root / "package.json"
        if package_json.exists():
            shutil.copy2(package_json, test_env / "package.json")
            
        node_modules = project_root / "node_modules"
        if node_modules.exists():
            # Only copy the specific modules we need to avoid large copy operation
            test_node_modules = test_env / "node_modules"
            test_node_modules.mkdir(exist_ok=True)
            
            # Copy rbush module specifically
            rbush_module = node_modules / "rbush"
            if rbush_module.exists():
                shutil.copytree(rbush_module, test_node_modules / "rbush")
                print("   📦 Copied rbush dependency for mobile build")
        
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
        if need_data_processing:
            print("   🗂️ Processing test data (GPX import and PMTiles generation)...")
            
            # Use main project's .venv Python which has all server dependencies
            main_venv_python = project_root / ".venv" / "bin" / "python"
            
            print("   🔄 Running consolidated data processing...")
            # Run process_data.py to handle both import and PMTiles generation
            result = subprocess.run([
                str(main_venv_python), "process_data.py"
            ], cwd=server_dir, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Data processing failed with return code {result.returncode}")
            
            print("   ✅ Test data processing complete.")
        else:
            print("   ⚡ Skipping data processing: Using cached PMTiles (data unchanged)")
            # Copy cached PMTiles to test environment
            cached_pmtiles_path = project_root / "testing" / "cached_test_data" / "runs.pmtiles"
            if cached_pmtiles_path.exists():
                shutil.copy2(cached_pmtiles_path, server_dir / "runs.pmtiles")
                print(f"   📋 Using cached PMTiles: {cached_pmtiles_path}")
            else:
                print("   ⚠️ Warning: No cached PMTiles found, falling back to data processing")
                need_data_processing = True  # Force data processing if cache missing
                
                # Run the data processing that was skipped
                print("   🗂️ Processing test data (GPX import and PMTiles generation)...")
                main_venv_python = project_root / ".venv" / "bin" / "python"
                print("   🔄 Running consolidated data processing...")
                result = subprocess.run([
                    str(main_venv_python), "process_data.py"
                ], cwd=server_dir, text=True, timeout=120)
                
                if result.returncode != 0:
                    raise Exception(f"Data processing failed with return code {result.returncode}")
                
                print("   ✅ Test data processing complete.")
        
        # 3. Build mobile APK with test data
        if need_apk_build:
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
            
            # Use the newly built APK
            apk_path = test_env / "mobile/android/app/build/outputs/apk/debug/app-debug.apk"
        else:
            print("   ⚡ Skipping APK build: Using cached APK (source unchanged)")
            # Copy cached APK to test environment for consistency
            cached_apk_path = project_root / "testing" / "cached_test_apk" / "app-debug.apk"
            if cached_apk_path.exists():
                apk_destination = test_env / "mobile/android/app/build/outputs/apk/debug"
                apk_destination.mkdir(parents=True, exist_ok=True)
                apk_path = apk_destination / "app-debug.apk"
                shutil.copy2(cached_apk_path, apk_path)
                print(f"   📋 Using cached APK: {cached_apk_path}")
            else:
                print("   ⚠️ Warning: No cached APK found, falling back to build")
                need_apk_build = True  # Force APK build if cache missing
                
                # Run the APK build that was skipped
                print("   📱 Building mobile APK with test data (this may take 5-10 minutes)...")
                print("   🔍 APK Build Output (verbose mode):")
                
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
                apk_path = test_env / "mobile/android/app/build/outputs/apk/debug/app-debug.apk"
        
        # 4. Install APK on emulator
        print("   📲 Installing test APK on emulator...")
        
        if not apk_path.exists():
            raise Exception(f"APK not found at expected path: {apk_path}")
        
        # Install APK
        result = subprocess.run([
            "adb", "install", "-r", str(apk_path)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"APK installation failed: {result.stderr}")
        
        print("   ✅ Test APK installed successfully.")
        
        # 5. Cache test APK and data for future optimization runs
        print("   💾 Caching test APK and data for future optimization runs...")
        cached_apk_dir = project_root / "testing" / "cached_test_apk"
        cached_data_dir = project_root / "testing" / "cached_test_data"
        
        try:
            # Create cache directories
            cached_apk_dir.mkdir(parents=True, exist_ok=True)
            cached_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Only cache APK if we built it (or needed to re-copy)
            if need_apk_build or not (cached_apk_dir / "app-debug.apk").exists():
                cached_apk_path = cached_apk_dir / "app-debug.apk"
                shutil.copy2(apk_path, cached_apk_path)
                print(f"   📱 Cached test APK: {cached_apk_path}")
            
            # Only cache PMTiles if we processed data (or needed to re-copy)
            if need_data_processing or not (cached_data_dir / "runs.pmtiles").exists():
                pmtiles_source = server_dir / "runs.pmtiles"
                if pmtiles_source.exists():
                    cached_pmtiles_path = cached_data_dir / "runs.pmtiles"
                    shutil.copy2(pmtiles_source, cached_pmtiles_path)
                    print(f"   🗺️ Cached PMTiles data: {cached_pmtiles_path}")
                
            print("   ✅ Test artifacts cached for optimization")
            
            # Update change detection baseline if we built or processed anything
            if need_apk_build or need_data_processing:
                print("   🔄 Updating change detection baseline...")
                change_detector.update_baseline()
            else:
                print("   ⚡ No baseline update needed (used cached artifacts)")
                
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
        # Cleanup using modularized cleanup utility
        cleanup_test_environment(str(test_env))

@pytest.fixture(scope="module")
def emulator_stability_setup(session_setup):
    """
    Module-scoped fixture to configure emulator stability once per test module.
    This avoids repeated ADB calls for stability configuration.
    """
    print(f"\n🎛️  Configuring emulator stability for module...")
    configure_emulator_stability()
    print(f"✅ Emulator stability configured for module")
    return True

@pytest.fixture(scope="module")
def mobile_driver(session_setup, emulator_stability_setup, request):
    """
    Provide Appium WebDriver instance for mobile tests.
    Module-scoped to minimize driver setup overhead while maintaining test isolation.
    Supports selective reset for tests marked with @pytest.mark.needs_clean_state.
    """
    from appium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from pathlib import Path
    import config
    
    print(f"\n📱 Setting up module-scoped mobile driver...")
    
    # Use test config for capabilities
    capabilities = config.TestConfig.ANDROID_CAPABILITIES.copy()
    
    # Use APK path from session setup (works for both fast and full mode)
    if session_setup.get('apk_path'):
        capabilities['appium:app'] = session_setup['apk_path']
    
    # Create WebDriver instance using modern Appium options API
    from appium.options.android import UiAutomator2Options
    options = UiAutomator2Options().load_capabilities(capabilities)
    driver = webdriver.Remote(
        config.TestConfig.APPIUM_SERVER,
        options=options
    )
    
    # Set implicit wait
    driver.implicitly_wait(config.TestConfig.IMPLICIT_WAIT)
    
    # Create WebDriverWait instance
    wait = WebDriverWait(driver, config.TestConfig.EXPLICIT_WAIT)
    
    # Add reset capability for state cleanup between tests
    def reset_app_state():
        """
        Reset app state between tests while reusing the same driver instance.
        This provides test isolation without driver recreation overhead.
        """
        try:
            # Method 1: Background and reactivate app to reset state
            driver.background_app(1)  # Background for 1 second
            driver.activate_app(session_setup['package_name'])  # Bring back to foreground
            
            # Method 2: Alternative - terminate and restart (more thorough but slower)
            # driver.terminate_app(session_setup['package_name'])
            # driver.activate_app(session_setup['package_name'])
            
            print("🔄 App state reset completed")
        except Exception as e:
            print(f"⚠️ App state reset warning: {e}")
            # Fallback: try terminate/restart approach
            try:
                driver.terminate_app(session_setup['package_name'])
                driver.activate_app(session_setup['package_name'])
                print("🔄 App state reset completed (fallback method)")
            except Exception as e2:
                print(f"⚠️ App state reset fallback also failed: {e2}")
    
    # Store reset function and other shared state for selective reset mechanism
    mobile_driver_context = {
        'driver': driver,
        'wait': wait,
        'session_data': session_setup,
        'reset': reset_app_state,
        'last_test_needed_clean_state': False
    }
    
    print(f"✅ Module-scoped mobile driver ready with selective reset capability")
    
    # Yield driver, wait instance, and reset function to tests
    yield mobile_driver_context
    
    # Cleanup using modularized cleanup utility
    cleanup_mobile_driver(driver)

# Global storage for mobile driver context to support selective reset
_mobile_driver_context = {}

@pytest.fixture(autouse=True)
def selective_reset_handler(request, mobile_driver):
    """
    Auto-use fixture that handles selective app state reset based on test markers.
    Tests marked with @pytest.mark.needs_clean_state will automatically get a clean app state.
    """
    global _mobile_driver_context
    _mobile_driver_context = mobile_driver
    
    # Check if current test needs clean state
    test_needs_clean_state = request.node.get_closest_marker("needs_clean_state") is not None
    
    # Reset app state if this test needs clean state OR if previous test needed clean state
    should_reset = (
        test_needs_clean_state or 
        mobile_driver.get('last_test_needed_clean_state', False)
    )
    
    if should_reset:
        print(f"\n🧹 Performing selective app state reset for test: {request.node.name}")
        try:
            mobile_driver['reset']()
            print(f"✅ App state reset completed for: {request.node.name}")
        except Exception as e:
            print(f"⚠️ App state reset failed for {request.node.name}: {e}")
    
    # Update context for next test
    mobile_driver['last_test_needed_clean_state'] = test_needs_clean_state
    
    # Run the test
    yield
    
    # Note: Post-test cleanup could be added here if needed

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

