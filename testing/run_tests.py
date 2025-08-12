#!/usr/bin/env python3
"""
Enhanced test runner for the running heatmap mobile app
Features:
- Automatic emulator management
- Intelligent test discovery and execution
- Enhanced HTML reporting with auto-browser opening
- Comprehensive command line options
- Robust error handling and cleanup
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
        print("   # OR run the setup script:")
        print("   python setup_test_env.py")
        return False
    
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Enhanced test runner for Running Heatmap mobile app (defaults: core tests, auto-emulator, no browser)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --smoke                  # Fast smoke tests (< 5 seconds, no emulator)
  python run_tests.py --smoke --smoke-server   # Server smoke tests only
  python run_tests.py --smoke --smoke-mobile   # Mobile smoke tests only
  python run_tests.py                          # Core tests with auto-emulator (most common)
  python run_tests.py --fast                   # Core tests in fast mode
  python run_tests.py --mobile                 # Full mobile test suite
  python run_tests.py --one-test               # Interactive single test selection
  python run_tests.py --one-test --fast        # Interactive single test selection in fast mode
  python run_tests.py --browser                # Core tests with browser report
  python run_tests.py --manual-emulator        # Core tests with manual emulator
  python run_tests.py --legacy --keep-app      # Legacy tests, keep app installed
        """
    )
    
    # Test suite selection (defaults to core tests)
    suite_group = parser.add_mutually_exclusive_group()
    suite_group.add_argument('--smoke', action='store_true',
                           help='Run fast smoke tests only (< 5 seconds, no emulator required)')
    suite_group.add_argument('--mobile', action='store_true',
                           help='Run all mobile tests (default: core tests)')
    suite_group.add_argument('--legacy', action='store_true',
                           help='Run legacy tests only (default: core tests)')
    suite_group.add_argument('--integration', action='store_true',
                           help='Run integration tests only (default: core tests)')
    suite_group.add_argument('--one-test', action='store_true',
                           help='Interactive selection of a single test to run (always includes test_00 setup)')
    
    # Smoke test component selection (only valid with --smoke)
    parser.add_argument('--smoke-server', action='store_true',
                       help='Run server smoke tests only (use with --smoke)')
    parser.add_argument('--smoke-api', action='store_true',
                       help='Run API smoke tests only (use with --smoke)')
    parser.add_argument('--smoke-web', action='store_true',
                       help='Run web smoke tests only (use with --smoke)')
    parser.add_argument('--smoke-data', action='store_true',
                       help='Run data pipeline smoke tests only (use with --smoke)')
    parser.add_argument('--smoke-build', action='store_true',
                       help='Run build smoke tests only (use with --smoke)')
    parser.add_argument('--smoke-mobile', action='store_true',
                       help='Run mobile smoke tests only (use with --smoke)')
    
    # Test execution options
    parser.add_argument('--fast', action='store_true',
                       help='Skip expensive operations (APK builds, tile generation)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    # Infrastructure management
    parser.add_argument('--manual-emulator', action='store_true',
                       help='Disable automatic emulator startup (default: auto-start emulator if needed)')
    parser.add_argument('--emulator-name', default='TestDevice',
                       help='Name of AVD to start (default: TestDevice)')
    parser.add_argument('--keep-emulator', action='store_true',
                       help='Keep emulator running after tests (default: shutdown auto-started emulator)')
    parser.add_argument('--keep-app', action='store_true',
                       help='Keep test app installed after tests (default: uninstall for fresh runs)')
    
    # Reporting options
    parser.add_argument('--browser', action='store_true',
                       help='Automatically open test report in browser (default: no browser)')
    parser.add_argument('--report-file', default='reports/test_report.html',
                       help='Path for HTML test report (default: reports/test_report.html)')
    
    # Specific test files
    parser.add_argument('tests', nargs='*',
                       help='Specific test files to run (optional)')
    
    return parser.parse_args()

def check_prerequisites(args):
    """Enhanced prerequisite checking with intelligent APK handling"""
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
            print("❌ APK not found for --fast mode. Please run without --fast first:")
            print("   python run_tests.py --core")
            return False
        print(f"✅ APK found for fast mode: {apk_path}")
    
    return True

def check_and_start_emulator(args):
    """Check for devices and optionally start emulator"""
    print("📱 Checking for connected devices...")
    
    # Check for connected devices
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
    
    if devices:
        print(f"✅ Found {len(devices)} connected device(s)")
        for device in devices:
            print(f"   - {device}")
        return True
    
    if args.manual_emulator:
        print("❌ No Android devices/emulators connected")
        print("   Manual emulator mode enabled. Options:")
        print("   1. Start an Android emulator manually")
        print("   2. Connect a physical device")
        print("   3. Remove --manual-emulator flag for automatic startup")
        print("   4. Run ./setup_emulator.sh for guided setup")
        return False
    
    # Auto-start emulator
    print(f"🚀 No devices found. Starting emulator: {args.emulator_name}")
    
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
    
    if args.emulator_name not in avds:
        print(f"❌ AVD '{args.emulator_name}' not found")
        print("   Available AVDs:")
        for avd in avds:
            print(f"     - {avd}")
        print("   Create an AVD in Android Studio or use --emulator-name with an existing AVD")
        return False
    
    # Start emulator
    print(f"   Starting {args.emulator_name} with WSL-compatible settings...")
    emulator_process = subprocess.Popen([
        'emulator', '-avd', args.emulator_name, 
        '-no-audio', '-gpu', 'swiftshader_indirect', 
        '-skin', '1080x1920'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for emulator to boot
    print("⏳ Waiting for emulator to boot (this may take 2-3 minutes)...")
    timeout = 300  # 5 minutes
    counter = 0
    
    while counter < timeout:
        # First check if ADB can see any devices
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
                        # Give it a moment to fully settle
                        time.sleep(3)
                        return True
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
    return False

def cleanup_existing_appium_servers():
    """Clean up any existing Appium server processes"""
    try:
        # Kill any existing Appium processes
        subprocess.run(['pkill', '-f', 'appium'], capture_output=True)
        time.sleep(2)  # Give processes time to die
        
        # Check if port 4723 is still in use and try to free it
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 4723))
            sock.close()
            
            if result == 0:
                # Port is still in use, try to find and kill the process
                try:
                    lsof_result = subprocess.run(['lsof', '-t', '-i:4723'], 
                                               capture_output=True, text=True)
                    if lsof_result.returncode == 0:
                        for pid in lsof_result.stdout.strip().split('\n'):
                            if pid:
                                subprocess.run(['kill', '-9', pid], capture_output=True)
                        time.sleep(1)
                except:
                    pass
        except:
            pass
            
    except Exception:
        pass

def start_appium_server(verbose=False):
    """Enhanced Appium server startup with health checks"""
    print("🚀 Starting Appium server...")
    
    # Clean up any existing Appium servers first
    cleanup_existing_appium_servers()
    
    # Check prerequisites first
    try:
        # Check if npx is available
        npx_check = subprocess.run(['npx', '--version'], capture_output=True, text=True)
        if npx_check.returncode != 0:
            print("❌ npx not available - please install Node.js")
            return None
        if verbose:
            print(f"   npx version: {npx_check.stdout.strip()}")
            
        # Check if appium is available
        appium_check = subprocess.run(['npx', 'appium', '--version'], capture_output=True, text=True)
        if appium_check.returncode != 0:
            print("❌ Appium not available - please run 'npm install' in testing directory")
            return None
        if verbose:
            print(f"   Appium version: {appium_check.stdout.strip()}")
            
    except Exception as e:
        print(f"❌ Error checking prerequisites: {e}")
        return None
    
    # Try to start Appium with multiple port strategies
    log_level = 'debug' if verbose else 'info'
    ports_to_try = [4723, 4724, 4725]  # Try alternative ports if 4723 fails
    
    for port in ports_to_try:
        base_path = '/wd/hub' if port == 4723 else f'/wd/hub-{port}'
        cmd = ['npx', 'appium', '--base-path', base_path, '--port', str(port), '--log-level', log_level]
        if verbose:
            print(f"   Trying port {port} with command: {' '.join(cmd)}")
            print(f"   Working directory: {Path(__file__).parent}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent,
                text=True,  # Ensure text mode for better error handling
                bufsize=1   # Line buffered
            )
            
            # Give the process a moment to start and check if it immediately fails
            time.sleep(3)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                if "EADDRINUSE" in stderr:
                    if verbose:
                        print(f"   Port {port} is in use, trying next port...")
                    continue
                else:
                    # Some other error occurred
                    print(f"❌ Appium server process terminated unexpectedly on port {port}")
                    print(f"   Return code: {process.returncode}")
                    print("   STDERR output:")
                    for line in str(stderr).splitlines():
                        print(f"     {line}")
                    continue
            
            # Process is still running, break out of port-trying loop
            if verbose:
                print(f"   Successfully started Appium on port {port}")
            break
            
        except Exception as e:
            print(f"❌ Failed to start Appium process on port {port}: {e}")
            if port == ports_to_try[-1]:  # Last port attempt
                return None
            continue
    else:
        # No ports worked
        print("❌ Failed to start Appium on any available port")
        return None
    
    # Wait for server to start with health checks
    print("⏳ Waiting for Appium server to start...")
    max_attempts = 30  # Increased timeout for better stability
    attempt = 0
    
    # Determine the port and base path being used
    server_port = port  # Use the port from the successful loop above
    base_path_part = base_path  # Use the base_path from the successful loop above
    server_url = f"http://localhost:{server_port}{base_path_part}/status"
    
    if verbose:
        print(f"   Health checking server at: {server_url}")
    
    while attempt < max_attempts:
        time.sleep(1)
        attempt += 1
        
        # Check if process is still running
        if process.poll() is not None:
            # Process has terminated, get output
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                stdout, stderr = "Timeout getting output", "Timeout getting output"
                
            print("❌ Appium server process terminated unexpectedly")
            print(f"   Return code: {process.returncode}")
            print("   STDOUT output:")
            for line in str(stdout).splitlines():
                print(f"     {line}")
            print("   STDERR output:")  
            for line in str(stderr).splitlines():
                print(f"     {line}")
            return None
        
        # Try to connect to server
        try:
            import requests
            response = requests.get(server_url, timeout=3)
            if response.status_code == 200:
                print(f"✅ Appium server is ready and responding on port {server_port}")
                if server_port != 4723:
                    print(f"   ⚠️  Note: Using alternate port {server_port} instead of default 4723")
                # Store the port info for the process so tests can use it
                process.appium_port = server_port
                process.appium_base_path = base_path_part
                return process
        except requests.exceptions.RequestException as e:
            # Server not ready yet, continue waiting
            if verbose and attempt % 10 == 0:
                print(f"   Connection attempt failed: {e}")
        except Exception as e:
            if verbose and attempt % 10 == 0:
                print(f"   Unexpected error checking server: {e}")
        
        if attempt % 5 == 0:
            print(f"   Still waiting... ({attempt}/{max_attempts})")
    
    print("❌ Appium server failed to respond within timeout")
    print("   Server process is still running but not responding to HTTP requests")
    if process.poll() is None:
        print("   Terminating unresponsive server process...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("   Force killing server process...")
            process.kill()
    return None

def build_pytest_command(args):
    """Build pytest command based on arguments"""
    cmd = [sys.executable, '-m', 'pytest']
    
    # Test selection based on markers or specific files
    if args.tests:
        # Specific test files provided
        cmd.extend(args.tests)
    elif getattr(args, 'smoke', False):
        # Smoke tests mode
        cmd.extend(['smoke_tests/'])  # Run tests from smoke_tests directory
        
        # Determine which smoke test components to run
        smoke_components = []
        if args.smoke_server:
            smoke_components.append('smoke_server')
        if args.smoke_api:
            smoke_components.append('smoke_api')
        if args.smoke_web:
            smoke_components.append('smoke_web')
        if args.smoke_data:
            smoke_components.append('smoke_data')
        if args.smoke_build:
            smoke_components.append('smoke_build')
        if args.smoke_mobile:
            smoke_components.append('smoke_mobile')
        
        if smoke_components:
            # Run specific smoke test components
            marker_expr = ' or '.join(smoke_components)
            cmd.extend(['-m', marker_expr])
        else:
            # Run all smoke tests
            cmd.extend(['-m', 'smoke'])
    elif getattr(args, 'one_test', False):
        # one_test mode - tests will be set by discover_and_select_test()
        if hasattr(args, 'selected_tests') and args.selected_tests:
            cmd.extend(args.selected_tests)
        else:
            print("❌ No tests selected for one-test mode")
            return None
        if args.fast:
            cmd.append('--fast')
    elif args.mobile:
        cmd.extend(['-m', 'mobile'])
        if args.fast:
            cmd.append('--fast')
    elif args.legacy:
        cmd.extend(['-m', 'legacy'])
        if args.fast:
            cmd.append('--fast')
    elif args.integration:
        cmd.extend(['-m', 'integration'])
        if args.fast:
            cmd.append('--fast')
    else:
        # Default: run core tests
        cmd.extend(['-m', 'core'])
        if args.fast:
            cmd.append('--fast')
    
    # Verbosity
    if args.verbose:
        cmd.append('-vv')
    else:
        cmd.append('-v')
    
    # Error display
    cmd.append('--tb=short')
    
    # HTML reporting
    cmd.extend(['--html', args.report_file, '--self-contained-html'])
    
    return cmd

def run_tests(args):
    """Enhanced test execution with intelligent discovery"""
    # Determine what we're running
    if getattr(args, 'smoke', False):
        # Smoke tests mode
        smoke_components = []
        if args.smoke_server:
            smoke_components.append('server')
        if args.smoke_api:
            smoke_components.append('api')
        if args.smoke_web:
            smoke_components.append('web')
        if args.smoke_data:
            smoke_components.append('data')
        if args.smoke_build:
            smoke_components.append('build')
        if args.smoke_mobile:
            smoke_components.append('mobile')
        
        if smoke_components:
            suite_name = f"smoke tests ({', '.join(smoke_components)})"
        else:
            suite_name = "smoke tests (all components)"
    elif getattr(args, 'one_test', False):
        # Test selection already done in main()
        if hasattr(args, 'selected_tests') and args.selected_tests:
            suite_name = f"selected tests ({', '.join(args.selected_tests)})"
        else:
            print("❌ No test selected for one-test mode")
            return 1
    elif args.tests:
        suite_name = "custom tests"
    elif args.mobile:
        suite_name = "mobile tests"
    elif args.legacy:
        suite_name = "legacy tests"
    elif args.integration:
        suite_name = "integration tests"
    else:
        suite_name = "core tests"
    
    if getattr(args, 'smoke', False):
        mode_desc = " (< 5 seconds, no emulator required)"
    else:
        mode_desc = " (fast mode)" if args.fast else " (full build mode)"
    print(f"🧪 Running {suite_name}{mode_desc}...")
    
    # Set up environment for testing
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Build pytest command
    cmd = build_pytest_command(args)
    
    if cmd is None:
        return 1  # Error in building command
    
    if args.verbose:
        print(f"   Command: {' '.join(cmd)}")
    
    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
    
    return result.returncode

def open_test_report(report_path, no_browser=False):
    """Open test report in browser with improved WSL detection"""
    abs_report_path = Path(__file__).parent / report_path
    
    if no_browser:
        print(f"📊 Test report available at: {abs_report_path}")
        return
    
    if not abs_report_path.exists():
        print(f"📊 Test report was not generated: {report_path}")
        return
    
    # Check if we're in WSL (common case where browser opening fails)
    is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
    
    try:
        if is_wsl:
            # In WSL, try to open with Windows browser via WSL interop
            windows_path = subprocess.run(
                ['wslpath', '-w', str(abs_report_path)], 
                capture_output=True, text=True
            ).stdout.strip()
            
            # Try different Windows browsers
            browsers = ['cmd.exe /c start', 'powershell.exe Start-Process']
            success = False
            
            for browser_cmd in browsers:
                try:
                    subprocess.run(f'{browser_cmd} "{windows_path}"', 
                                 shell=True, check=True, capture_output=True)
                    print(f"📊 Test report opened in Windows browser: {report_path}")
                    success = True
                    break
                except:
                    continue
            
            if not success:
                raise Exception("Could not open with Windows browsers")
        else:
            # Non-WSL: use standard webbrowser
            file_url = abs_report_path.as_uri()
            webbrowser.open(file_url)
            print(f"📊 Test report opened in browser: {report_path}")
            
    except Exception as e:
        print(f"📊 Test report available at: {abs_report_path}")
        print(f"   💡 In WSL? Copy path to Windows and open in browser manually")
        print(f"   💡 Or use: --no-browser flag to skip auto-opening")

def extract_test_description(test_file_path):
    """Extract a description from the test file by looking at docstrings or class names"""
    try:
        with open(test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to find class docstring first
        import re
        
        # Look for class docstring
        class_match = re.search(r'class\s+\w+.*?:\s*"""(.*?)"""', content, re.DOTALL)
        if class_match:
            docstring = class_match.group(1).strip()
            # Take first line of docstring
            first_line = docstring.split('\n')[0].strip()
            if first_line and len(first_line) < 80:
                return first_line
        
        # Look for module docstring
        module_match = re.search(r'^"""(.*?)"""', content, re.DOTALL | re.MULTILINE)
        if module_match:
            docstring = module_match.group(1).strip()
            first_line = docstring.split('\n')[0].strip()
            if first_line and len(first_line) < 80:
                return first_line
        
        # Look for class name and make it readable
        class_name_match = re.search(r'class\s+(\w+)', content)
        if class_name_match:
            class_name = class_name_match.group(1)
            if class_name.startswith('Test'):
                class_name = class_name[4:]  # Remove 'Test' prefix
            # Convert CamelCase to readable format
            readable = re.sub(r'([A-Z])', r' \1', class_name).strip()
            return readable
            
    except Exception:
        pass
    
    # Fallback: convert filename to readable format
    name = test_file_path.stem.replace('test_', '').replace('_', ' ')
    # Remove leading numbers like "00 "
    name = re.sub(r'^\d+\s*', '', name)
    return name.title()

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
    print("=" * 80)
    
    for i, test_file in enumerate(test_files, 1):
        description = extract_test_description(test_file)
        
        # Special note for the setup test
        if test_file.name.startswith('test_00'):
            description += " (always runs first)"
        
        print(f"{i:2}. {test_file.name:<35} - {description}")
    
    print("=" * 80)
    
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
                
                # Always run test_00 first if it's not the selected test
                tests_to_run = []
                setup_test = None
                
                # Find the setup test (test_00*)
                for test_file in test_files:
                    if test_file.name.startswith('test_00'):
                        setup_test = test_file.name
                        break
                
                if selected_test.name != setup_test and setup_test:
                    tests_to_run.append(setup_test)
                    print(f"📋 Will run: {setup_test} (setup) + {selected_test.name}")
                else:
                    if setup_test:
                        print(f"📋 Will run: {selected_test.name} (setup test selected)")
                    else:
                        print(f"📋 Will run: {selected_test.name} (no setup test found)")
                
                tests_to_run.append(selected_test.name)
                return tests_to_run
                
            else:
                print(f"❌ Please enter a number between 1 and {len(test_files)}")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Test selection cancelled")
            return None
        except EOFError:
            print("\n❌ Test selection cancelled")
            return None

def print_test_summary(exit_code, args):
    """Print a comprehensive test summary"""
    print("\n" + "=" * 60)
    print("📊 TEST EXECUTION SUMMARY")
    print("=" * 60)
    
    # Test result
    if exit_code == 0:
        print("✅ RESULT: All tests passed!")
    else:
        print("❌ RESULT: Some tests failed")
    
    # Test configuration
    suite = "mobile" if args.mobile else "legacy" if args.legacy else "integration" if args.integration else "custom" if args.tests else "core"
    mode = "fast mode" if args.fast else "full build mode"
    print(f"🧪 SUITE: {suite}")
    print(f"⚡ MODE: {mode}")
    
    if args.tests:
        print(f"📁 FILES: {', '.join(args.tests)}")
    
    print("=" * 60)

def cleanup_test_app(args, verbose=False):
    """Clean up test app and data from emulator"""
    if args.keep_app:
        print("📱 Keeping test app installed (--keep-app flag)")
        return
        
    try:
        print("🧹 Cleaning up test app and data...")
        
        # Uninstall the test app
        print("   📱 Uninstalling test app...")
        result = subprocess.run(['adb', 'uninstall', 'com.run.heatmap'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Test app uninstalled")
        elif "not installed" in result.stderr.lower():
            print("   ℹ️  Test app was not installed")
        else:
            if verbose:
                print(f"   ⚠️  App uninstall warning: {result.stderr}")
        
        # Clear any uploaded test files
        print("   📁 Clearing test files from device...")
        subprocess.run(['adb', 'shell', 'rm', '-f', '/sdcard/Download/manual_upload_run.gpx'], 
                      capture_output=True)
        subprocess.run(['adb', 'shell', 'rm', '-f', '/sdcard/Download/test_*.gpx'], 
                      capture_output=True)
        print("   ✅ Test files cleared")
        
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Cleanup warning: {e}")

def find_emulator_processes(verbose=False):
    """Find running emulator processes by name"""
    emulator_processes = []
    
    try:
        # Check for common emulator process names
        process_names = ['qemu-system-x86_64', 'emulator64', 'emulator', 'qemu-system']
        
        for process_name in process_names:
            try:
                # Use pgrep to find processes by name  
                result = subprocess.run(['pgrep', '-f', process_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    pids = [pid.strip() for pid in result.stdout.split('\n') if pid.strip()]
                    for pid in pids:
                        # Get process details
                        ps_result = subprocess.run(['ps', '-p', pid, '-o', 'pid,comm,args'], 
                                                 capture_output=True, text=True)
                        if ps_result.returncode == 0 and 'avd' in ps_result.stdout.lower():
                            emulator_processes.append({
                                'pid': pid,
                                'name': process_name,
                                'details': ps_result.stdout.strip()
                            })
                            if verbose:
                                print(f"   Found emulator process: PID {pid} ({process_name})")
            except:
                continue
                
    except Exception as e:
        if verbose:
            print(f"   Process detection error: {e}")
    
    return emulator_processes

def kill_emulator_processes(processes, verbose=False):
    """Kill emulator processes by PID"""
    success = True
    
    for process in processes:
        try:
            print(f"   🔪 Killing emulator process PID {process['pid']} ({process['name']})")
            
            # Try graceful termination first (SIGTERM)
            subprocess.run(['kill', process['pid']], capture_output=True, timeout=5)
            time.sleep(2)
            
            # Check if process still exists
            check_result = subprocess.run(['kill', '-0', process['pid']], 
                                        capture_output=True)
            if check_result.returncode == 0:
                # Process still exists, force kill (SIGKILL)
                if verbose:
                    print(f"      Process {process['pid']} still running, force killing...")
                subprocess.run(['kill', '-9', process['pid']], capture_output=True)
                time.sleep(1)
            
            print(f"   ✅ Process {process['pid']} terminated")
            
        except Exception as e:
            if verbose:
                print(f"   ⚠️  Failed to kill process {process['pid']}: {e}")
            success = False
    
    return success

def shutdown_emulator(args, verbose=False):
    """Enhanced multi-method emulator shutdown"""
    if args.manual_emulator:
        print("📱 Emulator was manually started - leaving it running")
        return
        
    if args.keep_emulator:
        print("📱 Keeping auto-started emulator running (--keep-emulator flag)")
        return
    
    print("🔌 Shutting down auto-started emulator...")
    
    # First, check if emulator is running
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if 'emulator-' in line and '\tdevice' in line]
    
    if not devices:
        print("   ℹ️  No emulator devices found in ADB")
        # Still check for processes in case ADB connection is broken
        processes = find_emulator_processes(verbose)
        if processes:
            print(f"   🔍 Found {len(processes)} emulator process(es) despite no ADB devices")
            kill_emulator_processes(processes, verbose)
        return
    
    emulator_serial = devices[0].split('\t')[0]
    print(f"   📱 Target emulator: {emulator_serial}")
    
    # Method 1: Clean ADB shutdown (recommended approach)
    print("   🧼 Method 1: Clean ADB shutdown (adb shell reboot -p)")
    try:
        clean_shutdown = subprocess.run([
            'adb', '-s', emulator_serial, 'shell', 'reboot', '-p'
        ], capture_output=True, text=True, timeout=20)
        
        if clean_shutdown.returncode == 0:
            print("   ✅ Clean shutdown command sent")
            
            # Wait for clean shutdown to complete
            print("   ⏳ Waiting for clean shutdown...")
            for i in range(10):  # 20 seconds total
                time.sleep(2)
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
                devices = [line for line in result.stdout.split('\n') if 'emulator-' in line and '\tdevice' in line]
                if not devices:
                    print("   ✅ Emulator shut down cleanly!")
                    return
                if i % 3 == 0:
                    print(f"      Clean shutdown in progress... ({(i+1)*2}s)")
            
            print("   ⏳ Clean shutdown taking longer than expected, trying next method...")
        else:
            if verbose:
                print(f"   ⚠️  Clean shutdown failed: {clean_shutdown.stderr}")
    
    except subprocess.TimeoutExpired:
        print("   ⏳ Clean shutdown timed out, trying next method...")
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Clean shutdown error: {e}")
    
    # Method 2: Original ADB emu kill (with shorter timeout)
    print("   ⚡ Method 2: ADB emulator kill (adb emu kill)")
    try:
        emu_kill = subprocess.run([
            'adb', '-s', emulator_serial, 'emu', 'kill'
        ], capture_output=True, text=True, timeout=10)
        
        if emu_kill.returncode == 0:
            print("   ✅ Emulator kill command sent")
            
            # Wait for kill to complete (shorter timeout)
            for i in range(5):  # 10 seconds total
                time.sleep(2)
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
                devices = [line for line in result.stdout.split('\n') if 'emulator-' in line and '\tdevice' in line]
                if not devices:
                    print("   ✅ Emulator killed via ADB!")
                    return
                if i % 2 == 0:
                    print(f"      ADB kill in progress... ({(i+1)*2}s)")
                    
            print("   ⏳ ADB kill incomplete, trying process-based method...")
        else:
            if verbose:
                print(f"   ⚠️  ADB kill failed: {emu_kill.stderr}")
    
    except subprocess.TimeoutExpired:
        print("   ⏳ ADB kill timed out (common issue), trying process-based method...")
    except Exception as e:
        if verbose:
            print(f"   ⚠️  ADB kill error: {e}")
    
    # Method 3: Process-based killing
    print("   🔪 Method 3: Process-based termination")
    processes = find_emulator_processes(verbose)
    
    if processes:
        print(f"   🎯 Found {len(processes)} emulator process(es)")
        if kill_emulator_processes(processes, verbose):
            # Wait a moment for processes to fully terminate
            time.sleep(3)
            
            # Final verification
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
            devices = [line for line in result.stdout.split('\n') if 'emulator-' in line and '\tdevice' in line]
            
            if not devices:
                print("   ✅ Emulator shutdown completed via process termination!")
                return
            else:
                print("   ⚠️  ADB still shows emulator, but processes were killed")
                return
        else:
            print("   ⚠️  Some processes could not be terminated")
    else:
        print("   ℹ️  No emulator processes found")
    
    # Final status check
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if 'emulator-' in line and '\tdevice' in line]
    
    if not devices:
        print("   ✅ Emulator appears to be shut down (no ADB devices)")
    else:
        print("   ⚠️  Emulator may still be running - manual closure may be needed")
        if verbose:
            print("   💡 Consider using --keep-emulator flag if shutdown issues persist")

def cleanup_appium_server(appium_process, verbose=False):
    """Enhanced Appium server cleanup with port verification"""
    if not appium_process:
        return
        
    print("🛑 Stopping Appium server...")
    
    # Get the port info if available
    server_port = getattr(appium_process, 'appium_port', 4723)
    
    try:
        # Try graceful termination first
        appium_process.terminate()
        appium_process.wait(timeout=8)
        print("✅ Appium server stopped gracefully")
    except subprocess.TimeoutExpired:
        if verbose:
            print("   Graceful shutdown timed out, force-killing Appium server...")
        try:
            appium_process.kill()
            appium_process.wait(timeout=3)
            print("✅ Appium server stopped (force-killed)")
        except Exception as e:
            if verbose:
                print(f"   Warning: Error force-killing Appium server: {e}")
    except Exception as e:
        if verbose:
            print(f"   Warning: Error stopping Appium server: {e}")
    
    # Verify the port is actually free and clean up if needed
    try:
        import socket
        import time
        
        # Give a moment for the port to be released
        time.sleep(2)
        
        # Test if the port is still in use
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', server_port))
        sock.close()
        
        if result == 0:
            # Port is still in use, try to find and kill the process
            print(f"   🔍 Port {server_port} still in use, attempting cleanup...")
            try:
                lsof_result = subprocess.run(['lsof', '-t', f'-i:{server_port}'], 
                                           capture_output=True, text=True)
                if lsof_result.returncode == 0 and lsof_result.stdout.strip():
                    for pid in lsof_result.stdout.strip().split('\n'):
                        if pid:
                            print(f"   🔪 Killing process {pid} using port {server_port}")
                            subprocess.run(['kill', '-9', pid], capture_output=True)
                    time.sleep(1)
                    print(f"✅ Port {server_port} cleanup completed")
                else:
                    if verbose:
                        print(f"   ℹ️  No processes found using port {server_port}")
            except Exception as e:
                if verbose:
                    print(f"   ⚠️  Port cleanup error: {e}")
        else:
            if verbose:
                print(f"   ✅ Port {server_port} is properly released")
                
    except Exception as e:
        if verbose:
            print(f"   ⚠️  Port verification error: {e}")

def cleanup_resources(appium_process, args, verbose=False):
    """Enhanced cleanup with app cleanup and emulator shutdown"""
    # 1. Stop Appium server with enhanced port cleanup
    cleanup_appium_server(appium_process, verbose)
    
    # 2. Clean up test app and data
    cleanup_test_app(args, verbose)
    
    # 3. Shutdown emulator if auto-started
    shutdown_emulator(args, verbose)


def main():
    """Enhanced main test runner function"""
    # Parse arguments first to handle help and early exits
    args = parse_arguments()
    
    print("📱 Enhanced Running Heatmap Mobile App Test Runner")
    print("=" * 60)
    
    # Check dependencies first
    mobile_only = getattr(args, 'smoke', False)
    if not check_dependencies(mobile_only=mobile_only):
        print("\n💡 For mobile-only tests:")
        print("   ./test_mobile.sh")
        print("\n💡 Run setup script to install all dependencies:")
        print("   python setup_test_env.py")
        sys.exit(1)
    
    # Handle test selection BEFORE infrastructure setup
    if getattr(args, 'one_test', False):
        selected_tests = discover_and_select_test()
        if selected_tests is None:
            print("❌ No test selected, exiting...")
            sys.exit(1)
        
        # Set the selected tests on args object
        args.selected_tests = selected_tests
        print(f"🎯 Proceeding with infrastructure setup for: {', '.join(selected_tests)}")
        print()
    
    # Handle smoke tests - bypass emulator and Appium setup
    if getattr(args, 'smoke', False):
        print("🚀 Smoke test mode: Bypassing emulator and Appium setup")
        
        # Create reports directory
        reports_dir = Path(__file__).parent / Path(args.report_file).parent
        reports_dir.mkdir(exist_ok=True)
        
        try:
            # Run smoke tests directly
            exit_code = run_tests(args)
            
            # Print summary
            print_test_summary(exit_code, args)
            
            # Open test report
            open_test_report(args.report_file, not args.browser)
            
        except KeyboardInterrupt:
            print("\n⏹️  Smoke tests interrupted by user")
            exit_code = 1
        except Exception as e:
            print(f"❌ Smoke test execution failed: {e}")
            exit_code = 1
        
        sys.exit(exit_code)
    
    # Regular tests - full infrastructure setup
    # Check prerequisites
    if not check_prerequisites(args):
        sys.exit(1)
    
    # Check and start emulator if needed
    if not check_and_start_emulator(args):
        sys.exit(1)
    
    # Create reports directory
    reports_dir = Path(__file__).parent / Path(args.report_file).parent
    reports_dir.mkdir(exist_ok=True)
    
    
    appium_process = None
    exit_code = 1
    
    try:
        # Start Appium server
        appium_process = start_appium_server(args.verbose)
        if appium_process is None:
            print("❌ Failed to start Appium server")
            sys.exit(1)
        
        # Run tests
        exit_code = run_tests(args)
        
        # Print comprehensive summary
        print_test_summary(exit_code, args)
        
        # Open test report
        open_test_report(args.report_file, not args.browser)
        
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit_code = 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        exit_code = 1
        
    finally:
        # Enhanced cleanup with app cleanup and emulator shutdown
        cleanup_resources(appium_process, args, args.verbose)
        
        # Final port cleanup - ensure all Appium ports are released
        if args.verbose:
            print("🧹 Final port cleanup check...")
        for port in [4723, 4724, 4725]:
            try:
                lsof_result = subprocess.run(['lsof', '-t', f'-i:{port}'], 
                                           capture_output=True, text=True)
                if lsof_result.returncode == 0 and lsof_result.stdout.strip():
                    for pid in lsof_result.stdout.strip().split('\n'):
                        if pid:
                            if args.verbose:
                                print(f"   🔪 Final cleanup: killing process {pid} on port {port}")
                            subprocess.run(['kill', '-9', pid], capture_output=True)
            except Exception:
                pass
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()