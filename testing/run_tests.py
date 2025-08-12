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
    """Check for devices and prompt user if none found"""
    print("📱 Checking for connected devices...")
    
    # Check for connected devices
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
    
    if devices:
        print(f"✅ Found {len(devices)} connected device(s)")
        for device in devices:
            print(f"   - {device}")
        return True
    
    print("❌ No Android devices/emulators connected")
    print("   Please connect a device or start an emulator manually")
    return False

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
    
    # Standard options
    cmd.extend(['-v', '--tb=short'])
    
    # HTML reporting
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

def open_test_report(report_path):
    """Open test report if it exists"""
    abs_report_path = Path(__file__).parent / report_path
    
    if not abs_report_path.exists():
        print(f"📊 Test report was not generated: {report_path}")
        return
    
    # Check if we're in WSL
    is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
    
    try:
        if is_wsl:
            # In WSL, try to open with Windows browser
            windows_path = subprocess.run(
                ['wslpath', '-w', str(abs_report_path)], 
                capture_output=True, text=True
            ).stdout.strip()
            
            subprocess.run(f'cmd.exe /c start "{windows_path}"', 
                         shell=True, check=True, capture_output=True)
            print(f"📊 Test report opened in Windows browser: {report_path}")
        else:
            # Non-WSL: use standard webbrowser
            file_url = abs_report_path.as_uri()
            webbrowser.open(file_url)
            print(f"📊 Test report opened in browser: {report_path}")
            
    except Exception:
        print(f"📊 Test report available at: {abs_report_path}")

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
    if not check_and_start_emulator():
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
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()