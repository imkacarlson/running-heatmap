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


@pytest.fixture(scope="session")
def test_gpx_data():
    """Provide test GPX data"""
    return Path(__file__).parent / "test_data" / "sample_run.gpx"


@pytest.fixture(scope="session") 
def isolated_test_environment(test_gpx_data):
    """Create isolated test environment with processed data"""
    print("\n🏗️ Setting up isolated test environment...")
    
    # Create temporary environment
    test_env = Path(tempfile.mkdtemp(prefix="heatmap_test_session_"))
    server_dir = test_env / "server"
    raw_data_dir = test_env / "data" / "raw"
    
    # Set up directory structure
    server_dir.mkdir(parents=True)
    raw_data_dir.mkdir(parents=True)
    
    # Copy server scripts
    real_server_dir = Path(__file__).parent.parent / "server" 
    scripts = ["import_runs.py", "make_pmtiles.py", "build_mobile.py"]
    for script in scripts:
        if (real_server_dir / script).exists():
            shutil.copy(real_server_dir / script, server_dir / script)
    
    # Copy other server files needed for build
    other_files = ["mobile_template.html", "mobile_main.js", "sw_template.js", 
                  "spatial.worker.js", "AndroidManifest.xml.template", 
                  "MainActivity.java.template", "HttpRangeServerPlugin.java.template",
                  "network_security_config.xml.template"]
    for file in other_files:
        if (real_server_dir / file).exists():
            shutil.copy(real_server_dir / file, server_dir / file)
    
    # Copy test GPX to raw data
    shutil.copy(test_gpx_data, raw_data_dir / "test_run.gpx")
    
    # Run data pipeline using the main venv that has the required packages
    main_venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python"
    
    print("🔄 Running GPX import...")
    subprocess.run([str(main_venv_python), "import_runs.py"], cwd=server_dir, check=True)
    
    print("🗺️ Generating PMTiles...")
    subprocess.run([str(main_venv_python), "make_pmtiles.py"], cwd=server_dir, check=True)
    
    yield {
        'test_env': test_env,
        'server_dir': server_dir,
        'pmtiles_path': server_dir / "runs.pmtiles"
    }
    
    # Cleanup
    print(f"\n🧹 Cleaning up test environment: {test_env}")
    shutil.rmtree(test_env)


@pytest.fixture(scope="session")
def test_apk_with_data(isolated_test_environment):
    """Build APK with test data in completely isolated environment - expensive operation done once per session"""
    print("\n📱 Building APK with test data in isolated environment (this may take 5-10 minutes)...")
    
    env_info = isolated_test_environment
    project_root = Path(__file__).parent.parent
    real_server_dir = project_root / "server"
    real_mobile_dir = project_root / "mobile"
    
    # Create isolated mobile build environment
    isolated_mobile_dir = env_info['test_env'] / "mobile"
    isolated_mobile_dir.mkdir(exist_ok=True)
    
    print("🏗️ Setting up isolated mobile build environment...")
    
    try:
        # Copy entire mobile project structure to isolated environment
        if real_mobile_dir.exists():
            print("📋 Copying existing mobile project structure...")
            # Copy package.json and capacitor config if they exist
            for config_file in ["package.json", "package-lock.json", "capacitor.config.json"]:
                src = real_mobile_dir / config_file
                if src.exists():
                    shutil.copy(src, isolated_mobile_dir / config_file)
                    
            # Copy node_modules if it exists (speeds up build)
            real_node_modules = real_mobile_dir / "node_modules"
            if real_node_modules.exists():
                print("📦 Copying node_modules (this may take a moment)...")
                shutil.copytree(real_node_modules, isolated_mobile_dir / "node_modules")
            
            # Copy android directory structure if it exists
            real_android_dir = real_mobile_dir / "android"
            if real_android_dir.exists():
                print("📱 Copying Android project structure...")
                shutil.copytree(real_android_dir, isolated_mobile_dir / "android")
        
        # Run build_mobile.py in isolated environment pointing to our test data
        print("🔨 Running mobile build with test data...")
        
        # Set environment to point to our test data
        build_env = os.environ.copy()
        build_env['MOBILE_BUILD_AUTO'] = '1'
        
        # Create a custom build script that uses our test data
        isolated_build_script = isolated_mobile_dir / "build_mobile_test.py"
        build_script_content = f'''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, "{real_server_dir}")

# Override the SCRIPT_DIR to point to our test server directory
import build_mobile
build_mobile.SCRIPT_DIR = "{env_info['server_dir']}"
build_mobile.PROJECT_ROOT = "{env_info['test_env']}"
build_mobile.MOBILE_DIR = "{isolated_mobile_dir}"

if __name__ == '__main__':
    build_mobile.main()
'''
        
        with open(isolated_build_script, 'w') as f:
            f.write(build_script_content)
        
        # Run the isolated build using main venv python
        main_venv_python = Path(__file__).parent.parent / ".venv" / "bin" / "python"
        build_process = subprocess.Popen([
            str(main_venv_python), str(isolated_build_script)
        ], cwd=isolated_mobile_dir, stdin=subprocess.PIPE, 
           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
           text=True, env=build_env)
        
        # Provide automated responses to prompts
        stdout, _ = build_process.communicate(input="y\ny\n", timeout=600)  # 10 minute timeout
        
        print("📋 Isolated build output:")
        print(stdout)
        
        if build_process.returncode != 0:
            raise Exception(f"Isolated mobile build failed with return code {build_process.returncode}")
            
        print("✅ Mobile APK built successfully with test data in isolated environment")
        
        # Verify APK exists in isolated environment
        apk_path = isolated_mobile_dir / "android/app/build/outputs/apk/debug/app-debug.apk"
        if not apk_path.exists():
            raise Exception(f"APK not found after isolated build at {apk_path}")
            
        yield apk_path
        
    except Exception as e:
        print(f"❌ Isolated build failed: {e}")
        raise


@pytest.fixture(scope="session")
def test_emulator_with_apk(test_apk_with_data):
    """Install test APK on emulator - done once per session"""
    print("\n📲 Installing test APK on emulator...")
    
    # Set up adb environment
    android_home = os.environ.get('ANDROID_HOME', '/home/imkacarlson/android-sdk')
    adb_env = os.environ.copy()
    adb_env['PATH'] = f"{adb_env['PATH']}:{android_home}/platform-tools"
    
    # Check device connection
    devices_result = subprocess.run(["adb", "devices"], 
                                  capture_output=True, text=True, env=adb_env)
    print(f"📱 Connected devices: {devices_result.stdout.strip()}")
    
    if "device" not in devices_result.stdout:
        raise Exception("No Android devices connected")
    
    # Uninstall existing app
    subprocess.run(["adb", "uninstall", "com.run.heatmap"], 
                   capture_output=True, check=False, env=adb_env)
    
    # Install test APK
    result = subprocess.run(["adb", "install", str(test_apk_with_data)], 
                          capture_output=True, text=True, env=adb_env)
    
    if result.returncode != 0:
        raise Exception(f"APK installation failed: {result.stderr}")
        
    print("✅ Test APK installed successfully")
    
    # Give system time to register app
    time.sleep(5)
    
    yield {
        'apk_path': test_apk_with_data,
        'package_name': 'com.run.heatmap'
    }
    
    print("📱 Test APK session complete")


@pytest.fixture(scope="function")
def fresh_app_session(test_emulator_with_apk):
    """Provide a fresh app session for each test"""
    # Force stop the app to ensure clean state
    android_home = os.environ.get('ANDROID_HOME', '/home/imkacarlson/android-sdk')
    adb_env = os.environ.copy()
    adb_env['PATH'] = f"{adb_env['PATH']}:{android_home}/platform-tools"
    
    subprocess.run(["adb", "shell", "am", "force-stop", "com.run.heatmap"], 
                   capture_output=True, env=adb_env)
    
    yield test_emulator_with_apk
    
    # Cleanup after test if needed
    pass