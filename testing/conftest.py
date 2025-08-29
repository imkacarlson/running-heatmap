"""
pytest fixtures for GPX to mobile testing
Session-scoped fixtures handle expensive operations once per test session
"""
import os
import sys
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

def pytest_configure(config):
    # Stash the driver so sessionfinish can access it
    config._appium_driver_ref = {}

def pytest_sessionfinish(session, exitstatus):
    # JS coverage is now collected per-test in mobile_driver fixture
    # This hook is kept for potential future session-level cleanup
    pass

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

@pytest.fixture(scope="function")  # Always use function scope when FORCE_BUILD might be set
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
    import sys
    
    # Create debug file to confirm fixture execution and track what's happening
    debug_file = Path(__file__).parent / "fixture_debug.txt"
    with open(debug_file, "w") as f:
        f.write(f"SESSION_SETUP FIXTURE EXECUTED - fast_mode={fast_mode}\n")
        f.write(f"SKIP_APK_BUILD={os.environ.get('SKIP_APK_BUILD')}\n")
        f.write(f"SKIP_DATA_PROCESSING={os.environ.get('SKIP_DATA_PROCESSING')}\n")
        f.write(f"INSTRUMENT_JS={os.environ.get('INSTRUMENT_JS')}\n")
        f.write(f"COVERAGE_RUN={os.environ.get('COVERAGE_RUN')}\n")
    
    # Also create instrumented files check
    instr_debug_file = Path(__file__).parent / "instrumented_debug.txt"
    
    # Try multiple approaches to ensure output appears
    message = f"\n🚀 SESSION_SETUP FIXTURE STARTING - fast_mode={fast_mode}"
    print(message)
    sys.stderr.write(message + "\n")  # Also write to stderr
    sys.stdout.flush()
    sys.stderr.flush()
    
    env_message = f"   🔧 Environment check: SKIP_APK_BUILD={os.environ.get('SKIP_APK_BUILD')}"
    print(env_message)
    sys.stdout.flush()
    sys.stderr.write(env_message + "\n")
    
    sys.stdout.flush()  # Force immediate output
    sys.stderr.flush()
    
    # Define project_root at the top so it's available for both modes
    project_root = Path(__file__).parent.parent
    
    # Import change detector for automatic optimization with error handling
    try:
        from change_detector import ChangeDetector, BuildOptimization
        print("   ✅ Change detector imported successfully")
        sys.stdout.flush()
    except ImportError as e:
        print(f"   ❌ Failed to import change detector: {e}")
        sys.stdout.flush()
        raise
    
    # Initialize change detector
    try:
        change_detector = ChangeDetector(project_root)
        print("   ✅ Change detector initialized successfully")
        sys.stdout.flush()
    except Exception as e:
        print(f"   ❌ Failed to initialize change detector: {e}")
        sys.stdout.flush()
        raise
    
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
    
    # Use optimization decisions from run_tests.py (single source of truth)
    print("\n🔍 Using optimization decisions from run_tests.py...")
    skip_apk_build = os.environ.get('SKIP_APK_BUILD') == '1'
    skip_data_processing = os.environ.get('SKIP_DATA_PROCESSING') == '1'
    
    print(f"   🔧 Environment variables from run_tests.py:")
    print(f"      SKIP_APK_BUILD = '{os.environ.get('SKIP_APK_BUILD')}' → skip_apk_build = {skip_apk_build}")
    print(f"      SKIP_DATA_PROCESSING = '{os.environ.get('SKIP_DATA_PROCESSING')}' → skip_data_processing = {skip_data_processing}")
    sys.stdout.flush()
    
    # If we can use cached artifacts, use them directly
    if skip_apk_build and skip_data_processing:
        print("\n⚡ Optimization: All cached artifacts are up-to-date, using existing APK and data.")
        cached_apk_path = project_root / "testing" / "cached_test_apk" / "app-debug.apk"
        cached_pmtiles_path = project_root / "testing" / "cached_test_data" / "runs.pmtiles"
        
        yield {
            'package_name': 'com.run.heatmap',
            'apk_path': str(cached_apk_path),
            'pmtiles_path': str(cached_pmtiles_path) if cached_pmtiles_path.exists() else None
        }
        return

    # Determine what actually needs to be built based on run_tests.py decisions
    need_apk_build = not skip_apk_build
    need_data_processing = not skip_data_processing

    print(f"\n🏗️ Infrastructure Setup: Building test environment")
    print(f"   📱 APK build needed: {need_apk_build}")
    print(f"   🗂️ Data processing needed: {need_data_processing}")
    
    # Write critical decisions to debug file (bypass pytest output buffering)
    with open(debug_file, "a") as f:
        f.write(f"FINAL_DECISIONS:\n")
        f.write(f"  skip_apk_build={skip_apk_build}\n")
        f.write(f"  skip_data_processing={skip_data_processing}\n") 
        f.write(f"  need_apk_build={need_apk_build}\n")
        f.write(f"  need_data_processing={need_data_processing}\n")
        f.write(f"  will_execute_build_mobile_py={need_apk_build}\n")
    
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
            "AndroidManifest.xml.template", 
            "MainActivity.java.template", "HttpRangeServerPlugin.java.template",
            "network_security_config.xml.template"
        ]
        
        for file_name in essential_files:
            src_file = project_root / "server" / file_name
            if src_file.exists():
                shutil.copy2(src_file, server_dir / file_name)
        
        # Copy .instrumented directory if it exists and instrumentation is enabled
        instrument_js = os.environ.get("INSTRUMENT_JS")
        print(f"\n   📦 JavaScript Instrumentation Check:")
        print(f"      INSTRUMENT_JS = '{instrument_js}'")
        sys.stdout.flush()
        
        if instrument_js == "1":
            instrumented_dir = project_root / "server" / ".instrumented"
            print(f"      Source instrumented directory: {instrumented_dir}")
            print(f"      Directory exists: {instrumented_dir.exists()}")
            
            if instrumented_dir.exists():
                files = list(instrumented_dir.iterdir())
                print(f"      Files in instrumented directory:")
                for f in files:
                    print(f"         • {f.name} ({f.stat().st_size} bytes)")
                
                dest_instrumented = server_dir / ".instrumented" 
                print(f"      Destination: {dest_instrumented}")
                
                try:
                    shutil.copytree(instrumented_dir, dest_instrumented)
                    copied_files = list(dest_instrumented.iterdir())
                    print(f"      ✅ Copied .instrumented directory: {len(copied_files)} files")
                    print(f"      Copied files:")
                    for f in copied_files:
                        print(f"         • {f.name} ({f.stat().st_size} bytes)")

                except Exception as e:
                    print(f"      ❌ Failed to copy instrumented directory: {e}")
            else:
                print(f"      ❌ Instrumented directory not found: {instrumented_dir}")
                print(f"      📋 Contents of server directory:")
                server_src_dir = project_root / "server"
                for item in server_src_dir.iterdir():
                    print(f"         • {item.name}")
        else:
            print(f"      ⏭️ Skipping instrumented directory copy (INSTRUMENT_JS = '{instrument_js}', expected '1')")
        
        sys.stdout.flush()
        
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
        
        # Define python path for subprocesses
        is_cov_run = os.environ.get('COVERAGE_RUN') == '1'
        main_venv_python = project_root / ".venv" / "bin" / "python"
        
        # If coverage is needed but not available in main venv, install it
        if is_cov_run:
            try:
                # Test if coverage is available in the main venv
                result = subprocess.run([
                    str(main_venv_python), '-c', 'import coverage'
                ], capture_output=True, timeout=10)
                if result.returncode != 0:
                    print("   📦 Installing coverage in main project venv...")
                    subprocess.run([
                        str(main_venv_python), '-m', 'pip', 'install', 'coverage[toml]'
                    ], check=True, timeout=30)
                    print("   ✅ Coverage installed successfully")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not install coverage: {e}")
                print("   📝 Coverage will be skipped for subprocesses")

        # 2. Process test data (GPX import and PMTiles generation)
        if need_data_processing:
            print("   🗂️ Processing test data (GPX import and PMTiles generation)...")
            
            print("   🔄 Running consolidated data processing...")
            # Run process_data.py to handle both import and PMTiles generation
            cmd = [str(main_venv_python)]
            if is_cov_run:
                cmd.extend([
                    "-m", "coverage", "run", "--parallel-mode",
                    "--rcfile", str(project_root / '.coveragerc'),
                    "--source", str(server_dir)  # ensure process_data.py in isolated env is measured
                ])
            cmd.append("process_data.py")

            result = subprocess.run(cmd, cwd=server_dir, text=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"Data processing failed with return code {result.returncode}")
            
            print("   ✅ Test data processing complete.")
        else:
            print("   ⚡ Skipping data processing: Using cached PMTiles and PKL (data unchanged)")
            # Copy cached PMTiles to test environment
            cached_pmtiles_path = project_root / "testing" / "cached_test_data" / "runs.pmtiles"
            cached_pkl_path = project_root / "testing" / "cached_test_data" / "runs.pkl"

            if cached_pmtiles_path.exists() and cached_pkl_path.exists():
                shutil.copy2(cached_pmtiles_path, server_dir / "runs.pmtiles")
                shutil.copy2(cached_pkl_path, server_dir / "runs.pkl")
                print(f"   📋 Using cached PMTiles: {cached_pmtiles_path}")
                print(f"   📦 Using cached PKL: {cached_pkl_path}")
            else:
                print("   ⚠️ Warning: No cached PMTiles found, falling back to data processing")
                need_data_processing = True  # Force data processing if cache missing
                
                # Run the data processing that was skipped
                print("   🗂️ Processing test data (GPX import and PMTiles generation)...")
                print("   🔄 Running consolidated data processing...")
                cmd = [str(main_venv_python)]
                if is_cov_run:
                    cmd.extend([
                        "-m", "coverage", "run", "--parallel-mode",
                        "--rcfile", str(project_root / '.coveragerc'),
                        "--source", str(server_dir)
                    ])
                cmd.append("process_data.py")
                result = subprocess.run(cmd, cwd=server_dir, text=True, timeout=120)
                
                if result.returncode != 0:
                    raise Exception(f"Data processing failed with return code {result.returncode}")
                
                print("   ✅ Test data processing complete.")
        
        # 3. Build mobile APK with test data
        if need_apk_build:
            # Track APK build execution in debug file (bypass pytest buffering)
            with open(debug_file, "a") as f:
                f.write(f"APK_BUILD_STARTING: need_apk_build={need_apk_build}\n")
            
            print("   📱 Building mobile APK with test data (this may take 5-10 minutes)...")
            print("   🔍 APK Build Output (verbose mode):")
            
            # Run mobile build with auto mode and stdin input for prompts INSIDE the isolated env
            build_env = os.environ.copy()
            build_env['MOBILE_BUILD_AUTO'] = '1'  # Enable auto mode
            
            # Pass through coverage and instrumentation flags
            if is_cov_run:
                build_env['COVERAGE_RUN'] = '1'
            if os.environ.get('INSTRUMENT_JS') == '1':
                build_env['INSTRUMENT_JS'] = '1'
                print("   📦 JS instrumentation enabled for mobile build")
            
            cmd = [str(main_venv_python)]
            if is_cov_run:
                cmd.extend([
                    "-m", "coverage", "run", "--parallel-mode",
                    "--rcfile", str(project_root / '.coveragerc'),
                    "--source", str(server_dir)  # ensure build_mobile.py in isolated env is measured
                ])
            cmd.append("build_mobile.py")

            build_process = subprocess.Popen(
                cmd,
                cwd=server_dir,  # IMPORTANT: build inside the isolated server dir
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=build_env,
            )
            
            # Automatically answer "y" to any prompts
            stdout, _ = build_process.communicate(input="y\ny\n", timeout=600)
            
            # Show the output
            print(stdout)
            
            if build_process.returncode != 0:
                raise Exception(f"Mobile APK build failed with return code {build_process.returncode}")
            
            print("   ✅ Mobile APK built successfully.")
            
            # Use the newly built APK (now in the isolated env)
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
                
                # Pass through coverage and instrumentation flags
                if is_cov_run:
                    build_env['COVERAGE_RUN'] = '1'
                if os.environ.get('INSTRUMENT_JS') == '1':
                    build_env['INSTRUMENT_JS'] = '1'
                    print("   📦 JS instrumentation enabled for fallback mobile build")
                
                cmd = [str(main_venv_python)]
                if is_cov_run:
                    cmd.extend([
                        "-m", "coverage", "run", "--parallel-mode",
                        "--rcfile", str(project_root / '.coveragerc'),
                        "--source", str(server_dir)  # measure isolated server path
                    ])
                cmd.append("build_mobile.py")

                build_process = subprocess.Popen(cmd, cwd=server_dir, stdin=subprocess.PIPE,
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
            
            # Only cache PMTiles and runs.pkl if we processed data
            if need_data_processing:
                # Cache PMTiles
                pmtiles_source = server_dir / "runs.pmtiles"
                if pmtiles_source.exists():
                    cached_pmtiles_path = cached_data_dir / "runs.pmtiles"
                    shutil.copy2(pmtiles_source, cached_pmtiles_path)
                    print(f"   🗺️ Cached PMTiles data: {cached_pmtiles_path}")
                
                # Cache runs.pkl
                pkl_source = server_dir / "runs.pkl"
                if pkl_source.exists():
                    cached_pkl_path = cached_data_dir / "runs.pkl"
                    shutil.copy2(pkl_source, cached_pkl_path)
                    print(f"   📦 Cached PKL data: {cached_pkl_path}")

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
        # Final instrumented files check
        with open(instr_debug_file, "a") as f:
            f.write(f"\n=== FINAL STATE BEFORE YIELD ===\n")
            f.write(f"test_env = {test_env}\n")
            f.write(f"server_dir = {server_dir}\n")
            
            # Check if instrumented files exist in test environment
            test_instrumented = server_dir / ".instrumented"
            f.write(f"test_instrumented = {test_instrumented}\n")
            f.write(f"test_instrumented.exists() = {test_instrumented.exists()}\n")
            
            if test_instrumented.exists():
                files = list(test_instrumented.iterdir())
                f.write(f"instrumented files in test env: {[f.name for f in files]}\n")
            
            # Check original instrumented files still exist
            orig_instrumented = project_root / "server" / ".instrumented"
            f.write(f"orig_instrumented.exists() = {orig_instrumented.exists()}\n")
            if orig_instrumented.exists():
                orig_files = list(orig_instrumented.iterdir())
                f.write(f"original instrumented files: {[f.name for f in orig_files]}\n")
        
        session_data = {
            'package_name': 'com.run.heatmap',
            'apk_path': str(apk_path),
            'pmtiles_path': str(server_dir / "runs.pmtiles"),
            'test_env': str(test_env),
            'server_dir': str(server_dir)
        }
        
        yield session_data
        
    finally:
        # Before cleanup, preserve any coverage fragments from the isolated env
        try:
            project_root = Path(__file__).parent.parent
            server_cov_dir = project_root / "server"
            server_cov_dir.mkdir(exist_ok=True)
            # Copy .coverage.* fragments so run_tests.py can combine later
            for cov_file in (server_dir.glob('.coverage.*') if 'server_dir' in locals() else []):
                dest = server_cov_dir / cov_file.name
                try:
                    shutil.copy2(cov_file, dest)
                    print(f"   📊 Preserved coverage fragment: {dest}")
                except Exception as e:
                    print(f"   ⚠️ Warning: Could not preserve coverage fragment {cov_file}: {e}")
        except Exception as e:
            print(f"   ⚠️ Warning during coverage preservation: {e}")

        # Cleanup using modularized cleanup utility
        cleanup_test_environment(str(test_env))

@pytest.fixture(scope="function")
def mobile_driver(request, session_setup):
    """
    Provide Appium WebDriver instance for mobile tests.
    This fixture creates a driver instance and handles cleanup.
    """
    from appium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from pathlib import Path
    import config
    
    print(f"\n📱 Setting up mobile driver...")
    
    # Configure emulator for deterministic behavior
    configure_emulator_stability()
    
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

    # Stash driver for session-level cleanup and JS coverage
    request.config._appium_driver_ref["driver"] = driver

    # Set implicit wait
    driver.implicitly_wait(config.TestConfig.IMPLICIT_WAIT)
    
    # Create WebDriverWait instance
    wait = WebDriverWait(driver, config.TestConfig.EXPLICIT_WAIT)

    # Begin CSS coverage tracking when JS instrumentation is enabled
    if os.getenv("INSTRUMENT_JS"):
        try:
            from js_coverage import start_css_coverage

            # Ensure we inject into an actual WebView context
            print("🔎 Waiting for WebView context to start CSS coverage...")
            webview_name = None
            for _ in range(40):  # ~10s total (40 * 0.25s)
                try:
                    ctxs = driver.contexts
                    webviews = [c for c in ctxs if c.startswith("WEBVIEW")]
                    if webviews:
                        webview_name = webviews[0]
                        break
                except Exception:
                    pass
                time.sleep(0.25)

            if webview_name:
                prev_ctx = None
                try:
                    prev_ctx = driver.current_context
                except Exception:
                    prev_ctx = None

                try:
                    driver.switch_to.context(webview_name)
                    start_css_coverage(driver)
                    print("✅ CSS coverage tracking started (WebView)")
                    # Also start DOM coverage tracking
                    try:
                        from js_coverage import start_dom_coverage, start_worker_coverage
                        start_dom_coverage(driver)
                        start_worker_coverage(driver)
                        print("✅ DOM + Worker coverage tracking started (WebView)")
                    except Exception as e:
                        print(f"⚠️  Could not start DOM/Worker coverage tracking: {e}")
                finally:
                    # Switch back to native to avoid affecting tests
                    try:
                        driver.switch_to.context(prev_ctx or "NATIVE_APP")
                    except Exception:
                        pass
            else:
                print("⚠️  No WebView context found; skipping CSS coverage start")
        except Exception as e:  # noqa: BLE001 - best effort
            print(f"⚠️  Could not start CSS coverage tracking: {e}")

    print(f"✅ Mobile driver ready")
    
    # Yield driver and wait instance to tests
    yield {
        'driver': driver,
        'wait': wait,
        'session_data': session_setup
    }
    
    # Collect JS coverage BEFORE driver cleanup
    try:
        from pathlib import Path
        from js_coverage import collect_js_coverage, stop_css_coverage, collect_dom_coverage
        # Ensure the path is relative to the testing directory
        report_dir = Path(__file__).parent / "reports/coverage/js"
        collect_js_coverage(driver, report_dir)
        print(f"✅ JS coverage collected to {report_dir}")

        if os.getenv("INSTRUMENT_JS"):
            css_dir = Path(__file__).parent / "reports/coverage/css"
            stop_css_coverage(driver, css_dir)
            print(f"✅ CSS coverage collected to {css_dir}")
            dom_dir = Path(__file__).parent / "reports/coverage/dom"
            collect_dom_coverage(driver, dom_dir)
            print(f"✅ DOM coverage collected to {dom_dir}")
    except Exception as e:
        # Do not fail the suite if coverage collection has issues
        print(f"⚠️  Could not collect JS coverage: {e}")
    
    # Cleanup using modularized cleanup utility
    cleanup_mobile_driver(driver)

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
