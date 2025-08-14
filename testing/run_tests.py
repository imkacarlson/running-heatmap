#!/usr/bin/env python3
"""
Simplified test runner for the running heatmap mobile app
Supports only --fast and --one-test flags for streamlined testing
"""
import sys
import time
import subprocess
import signal
import os
import argparse
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required mobile testing dependencies are available"""
    missing_deps = []
    
    # Check pytest
    try:
        import pytest
    except ImportError:
        missing_deps.append("pytest")
    
    # Check Appium (for mobile tests)
    try:
        import appium
    except ImportError:
        missing_deps.append("appium-python-client")
    
    if missing_deps:
        print("❌ Missing required mobile testing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n🔧 To install dependencies:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def parse_arguments():
    """Parse command line arguments - simplified to support only --fast and --one-test"""
    parser = argparse.ArgumentParser(
        description="Simplified test runner for Running Heatmap mobile app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                  # Run all tests
  python run_tests.py --fast           # Run tests in fast mode (skip expensive operations)
  python run_tests.py --one-test       # Interactive single test selection
  python run_tests.py --one-test --fast # Single test in fast mode
        """
    )
    
    # Simplified flags
    parser.add_argument('--fast', action='store_true',
                       help='Skip expensive operations (APK builds, tile generation)')
    parser.add_argument('--one-test', action='store_true',
                       help='Interactive selection of a single test to run')
    
    # Report file (internal use)
    parser.add_argument('--report-file', default='reports/test_report.html',
                       help=argparse.SUPPRESS)  # Hidden from help
    
    return parser.parse_args()

def check_prerequisites(args):
    """Check prerequisites for test execution"""
    print("🔍 Checking prerequisites...")
    
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
    
    # Check APK requirements based on test mode
    if not args.fast:
        # In full mode, we need project structure for APK building
        project_root = Path(__file__).parent.parent
        server_dir = project_root / "server"
        if not server_dir.exists():
            print("❌ Server directory not found. Are you in the right project?")
            return False
        print("✅ Project structure verified for APK building")
    else:
        # In fast mode, we need existing APK
        apk_path = Path(__file__).parent.parent / "mobile/android/app/build/outputs/apk/debug/app-debug.apk"
        if not apk_path.exists():
            print("❌ APK not found for --fast mode. Please run without --fast first")
            return False
        print(f"✅ APK found for fast mode: {apk_path}")
    
    return True

def check_and_start_emulator():
    """Check for devices and auto-start emulator if needed"""
    print("📱 Checking for connected devices...")
    
    # Check for connected devices
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
    
    if devices:
        print(f"✅ Found {len(devices)} connected device(s)")
        for device in devices:
            print(f"   - {device}")
        return {'started_emulator': False}  # Didn't start emulator
    
    # Auto-start emulator
    emulator_name = 'TestDevice'
    print(f"🚀 No devices found. Starting emulator: {emulator_name}")
    
    # Check if emulator command is available
    try:
        subprocess.run(['emulator', '-help'], capture_output=True, check=False)
    except FileNotFoundError:
        print("❌ Android emulator not found. Please install Android SDK")
        print("   Or start emulator manually and run tests again")
        return False
    
    # Check if AVD exists
    result = subprocess.run(['emulator', '-list-avds'], capture_output=True, text=True)
    avds = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    
    if emulator_name not in avds:
        print(f"❌ AVD '{emulator_name}' not found")
        print("   Available AVDs:")
        for avd in avds:
            print(f"     - {avd}")
        print("   Create an AVD or run ./setup_emulator.sh for setup")
        return False
    
    # Start emulator
    print(f"   Starting {emulator_name} with WSL-compatible settings...")
    emulator_process = subprocess.Popen([
        'emulator', '-avd', emulator_name, 
        '-no-audio', '-gpu', 'swiftshader_indirect', 
        '-skin', '1080x1920'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for emulator to boot
    print("⏳ Waiting for emulator to boot (this may take 2-3 minutes)...")
    timeout = 300  # 5 minutes
    counter = 0
    
    while counter < timeout:
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
            devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
            
            if devices:
                # Device found, now check if it's fully booted
                try:
                    boot_result = subprocess.run(['adb', 'shell', 'getprop', 'sys.boot_completed'], 
                                              capture_output=True, text=True, timeout=5)
                    if boot_result.returncode == 0 and '1' in boot_result.stdout.strip():
                        print("✅ Emulator is ready!")
                        time.sleep(3)  # Give it a moment to fully settle
                        return {'started_emulator': True, 'emulator_process': emulator_process}
                    elif counter % 15 == 0:  # Show boot progress occasionally
                        print(f"   Emulator detected, waiting for boot completion... ({counter}s)")
                except subprocess.TimeoutExpired:
                    if counter % 15 == 0:
                        print(f"   Emulator detected, checking boot status... ({counter}s)")
            else:
                # Try restarting ADB if no devices after reasonable time
                if counter >= 30 and counter % 30 == 0:
                    print(f"   Restarting ADB server to refresh device detection... ({counter}s)")
                    subprocess.run(['adb', 'kill-server'], capture_output=True)
                    subprocess.run(['adb', 'start-server'], capture_output=True)
                elif counter % 15 == 0:
                    print(f"   Still waiting for emulator to appear in ADB... ({counter}s)")
                    
        except subprocess.TimeoutExpired:
            if counter % 15 == 0:
                print(f"   ADB timeout, retrying... ({counter}s)")
        
        time.sleep(3)
        counter += 3
    
    print("❌ Emulator failed to start within timeout")
    emulator_process.terminate()
    return {'started_emulator': False}

def start_appium_server():
    """Start Appium server"""
    print("🚀 Starting Appium server...")
    
    # Check if npx is available
    try:
        npx_check = subprocess.run(['npx', '--version'], capture_output=True, text=True)
        if npx_check.returncode != 0:
            print("❌ npx not available - please install Node.js")
            return None
    except FileNotFoundError:
        print("❌ npx not available - please install Node.js")
        return None
    
    # Start Appium
    cmd = ['npx', 'appium', '--base-path', '/wd/hub', '--port', '4723']
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent,
            text=True
        )
        
        # Wait for server to start
        print("⏳ Waiting for Appium server to start...")
        for attempt in range(30):
            time.sleep(1)
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print("❌ Appium server process terminated unexpectedly")
                print(f"   STDERR: {stderr}")
                return None
            
            # Try to connect to server
            try:
                import requests
                response = requests.get("http://localhost:4723/wd/hub/status", timeout=3)
                if response.status_code == 200:
                    print("✅ Appium server is ready")
                    return process
            except:
                continue
        
        print("❌ Appium server failed to start within timeout")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start Appium server: {e}")
        return None

def discover_and_select_test():
    """Discover available tests and let user select one"""
    print("🔍 Discovering available tests...")
    
    # Get all test files in the current directory
    test_files = []
    test_dir = Path(__file__).parent
    
    for test_file in sorted(test_dir.glob("test_*.py")):
        test_files.append(test_file)
    
    if not test_files:
        print("❌ No test files found!")
        return None
        
    # Display menu
    print("\n🧪 Available Tests:")
    print("=" * 60)
    
    for i, test_file in enumerate(test_files, 1):
        print(f"{i:2}. {test_file.name}")
    
    print("=" * 60)
    
    # Get user selection
    while True:
        try:
            choice = input(f"Enter test number to run (1-{len(test_files)}): ").strip()
            
            if not choice:
                print("❌ Please enter a number")
                continue
                
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(test_files):
                selected_test = test_files[choice_num - 1]
                print(f"\n✅ Selected: {selected_test.name}")
                return [selected_test.name]
                
            else:
                print(f"❌ Please enter a number between 1 and {len(test_files)}")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Test selection cancelled")
            return None

def build_pytest_command(args):
    """Build pytest command based on arguments"""
    cmd = [sys.executable, '-m', 'pytest']
    
    # Test selection
    if args.one_test and hasattr(args, 'selected_tests') and args.selected_tests:
        cmd.extend(args.selected_tests)
    else:
        # Run all tests by default
        cmd.append('.')
    
    # Add fast mode flag if specified
    if args.fast:
        cmd.append('--fast')
    
    # Standard options - pytest.ini now includes -rw for warnings
    cmd.extend(['-v', '--tb=short'])
    
    # HTML reporting with warnings included  
    cmd.extend(['--html', args.report_file, '--self-contained-html'])
    
    return cmd

def run_tests(args):
    """Run the tests"""
    mode = "fast mode" if args.fast else "full mode"
    test_type = "selected test" if args.one_test else "all tests"
    print(f"🧪 Running {test_type} in {mode}...")
    
    # Set up environment for testing
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Build pytest command
    cmd = build_pytest_command(args)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
    
    return result.returncode

def cleanup_appium_server(appium_process):
    """Stop Appium server"""
    if not appium_process:
        return
        
    print("🛑 Stopping Appium server...")
    
    try:
        appium_process.terminate()
        appium_process.wait(timeout=5)
        print("✅ Appium server stopped")
    except subprocess.TimeoutExpired:
        appium_process.kill()
        print("✅ Appium server stopped (force-killed)")
    except Exception as e:
        print(f"⚠️  Warning: Error stopping Appium server: {e}")

def shutdown_emulator(emulator_info):
    """Shut down auto-started emulator"""
    if not emulator_info.get('started_emulator', False):
        return
        
    print("🔌 Shutting down auto-started emulator...")
    
    # Check current emulator devices
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if 'emulator-' in line and '\tdevice' in line]
    
    if not devices:
        print("   ✅ No emulator devices found")
        return
    
    emulator_serial = devices[0].split('\t')[0]
    print(f"   📱 Shutting down emulator: {emulator_serial}")
    
    # Try clean shutdown first
    try:
        result = subprocess.run(['adb', '-s', emulator_serial, 'emu', 'kill'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Emulator shutdown command sent")
            
            # Wait for shutdown
            for i in range(5):
                time.sleep(2)
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
                devices = [line for line in result.stdout.split('\n') if 'emulator-' in line and '\tdevice' in line]
                if not devices:
                    print("   ✅ Emulator shut down successfully!")
                    return
            
            print("   ⏳ Emulator shutdown in progress...")
        else:
            print("   ⚠️  Emulator shutdown command failed, trying process termination...")
    except subprocess.TimeoutExpired:
        print("   ⏳ Emulator shutdown timed out, trying process termination...")
    except Exception as e:
        print(f"   ⚠️  Emulator shutdown error: {e}")
    
    # Try to terminate the emulator process directly
    if 'emulator_process' in emulator_info:
        try:
            emulator_process = emulator_info['emulator_process']
            emulator_process.terminate()
            emulator_process.wait(timeout=5)
            print("   ✅ Emulator process terminated!")
        except subprocess.TimeoutExpired:
            emulator_process.kill()
            print("   ✅ Emulator process killed!")
        except Exception as e:
            print(f"   ⚠️  Process termination failed: {e}")

def open_test_report(report_path):
    """Report test report location without auto-opening"""
    abs_report_path = Path(__file__).parent / report_path
    
    if not abs_report_path.exists():
        print(f"📊 Test report was not generated: {report_path}")
        return
    
    print(f"📊 Test report saved: {abs_report_path}")
    
    # Check if we're in WSL and provide helpful path conversion
    is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
    if is_wsl:
        try:
            windows_path = subprocess.run(
                ['wslpath', '-w', str(abs_report_path)], 
                capture_output=True, text=True
            ).stdout.strip()
            print(f"   💡 Windows path: {windows_path}")
        except:
            print(f"   💡 Open in browser manually")

def main():
    """Main test runner function"""
    # Parse arguments
    args = parse_arguments()
    
    print("📱 Running Heatmap Mobile App Test Runner")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Handle test selection if one-test mode
    if args.one_test:
        selected_tests = discover_and_select_test()
        if selected_tests is None:
            print("❌ No test selected, exiting...")
            sys.exit(1)
        args.selected_tests = selected_tests
    
    # Check prerequisites
    if not check_prerequisites(args):
        sys.exit(1)
    
    # Check for devices
    emulator_info = check_and_start_emulator()
    if not emulator_info:
        sys.exit(1)
    
    # Create reports directory
    reports_dir = Path(__file__).parent / Path(args.report_file).parent
    reports_dir.mkdir(exist_ok=True)
    
    appium_process = None
    exit_code = 1
    
    try:
        # Start Appium server
        appium_process = start_appium_server()
        if appium_process is None:
            print("❌ Failed to start Appium server")
            sys.exit(1)
        
        # Run tests
        exit_code = run_tests(args)
        
        # Print result
        if exit_code == 0:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed")
        
        # Open test report
        open_test_report(args.report_file)
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit_code = 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit_code = 1
        
    finally:
        # Cleanup
        cleanup_appium_server(appium_process)
        shutdown_emulator(emulator_info)
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()