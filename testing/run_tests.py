#!/usr/bin/env python3
"""
Test runner for the running heatmap mobile app
"""
import sys
import time
import subprocess
import signal
import os
from pathlib import Path

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if APK exists
    apk_path = Path(__file__).parent.parent / "mobile/android/app/build/outputs/apk/debug/app-debug.apk"
    if not apk_path.exists():
        print("❌ APK not found. Please build the APK first:")
        print("   cd server && python build_mobile.py")
        return False
    
    print(f"✅ APK found at: {apk_path}")
    
    # Check if adb is available
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ADB is available")
        else:
            print("❌ ADB not found. Please install Android SDK platform-tools")
            return False
    except FileNotFoundError:
        print("❌ ADB not found. Please install Android SDK platform-tools")
        return False
    
    # Check for connected devices
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
    if not devices:
        print("❌ No Android devices/emulators connected")
        print("   Please start an Android emulator or connect a device")
        return False
    
    print(f"✅ Found {len(devices)} connected device(s)")
    return True

def start_appium_server():
    """Start Appium server in background"""
    print("🚀 Starting Appium server...")
    
    # Use npx to run the local appium installation
    process = subprocess.Popen(
        ['npx', 'appium', '--base-path', '/wd/hub', '--log-level', 'info'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )
    
    # Give server time to start
    print("⏳ Waiting for Appium server to start...")
    time.sleep(8)
    
    # Check if process is still running
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print("❌ Appium server failed to start")
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())
        return None
    
    print("✅ Appium server started")
    return process

def run_tests():
    """Run the test suite"""
    print("🧪 Running tests...")
    
    # Set up environment for testing
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Run pytest with verbose output
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'test_basic_functionality.py',
        '-v',
        '--tb=short',
        '--html=reports/test_report.html',
        '--self-contained-html'
    ], cwd=Path(__file__).parent, env=env)
    
    return result.returncode

def main():
    """Main test runner function"""
    print("📱 Running Heatmap Mobile App Tests")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create reports directory
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    appium_process = None
    
    try:
        # Start Appium server
        appium_process = start_appium_server()
        if appium_process is None:
            sys.exit(1)
        
        # Run tests
        exit_code = run_tests()
        
        if exit_code == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")
        
        print(f"\n📊 Test report available at: reports/test_report.html")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit_code = 1
        
    finally:
        # Clean up Appium server
        if appium_process:
            print("🛑 Stopping Appium server...")
            appium_process.terminate()
            try:
                appium_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                appium_process.kill()
                appium_process.wait()
            print("✅ Appium server stopped")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()