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

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Enhanced test runner for Running Heatmap mobile app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --core --fast --auto-emulator    # Full automation with cleanup
  python run_tests.py --mobile                         # Full mobile test suite  
  python run_tests.py --core --fast --keep-emulator    # Keep emulator running
  python run_tests.py --legacy --keep-app              # Keep test app installed
  python run_tests.py --no-browser                     # Don't open report in browser
        """
    )
    
    # Test suite selection
    suite_group = parser.add_mutually_exclusive_group()
    suite_group.add_argument('--core', action='store_true', 
                           help='Run core essential tests only (recommended)')
    suite_group.add_argument('--mobile', action='store_true',
                           help='Run all mobile tests')
    suite_group.add_argument('--legacy', action='store_true',
                           help='Run legacy tests only')
    suite_group.add_argument('--integration', action='store_true',
                           help='Run integration tests only')
    
    # Test execution options
    parser.add_argument('--fast', action='store_true',
                       help='Skip expensive operations (APK builds, tile generation)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    # Infrastructure management
    parser.add_argument('--auto-emulator', action='store_true',
                       help='Automatically start emulator if no devices connected')
    parser.add_argument('--emulator-name', default='TestDevice',
                       help='Name of AVD to start (default: TestDevice)')
    parser.add_argument('--keep-emulator', action='store_true',
                       help='Keep emulator running after tests (default: shutdown auto-started emulator)')
    parser.add_argument('--keep-app', action='store_true',
                       help='Keep test app installed after tests (default: uninstall for fresh runs)')
    
    # Reporting options
    parser.add_argument('--no-browser', action='store_true',
                       help="Don't automatically open test report in browser")
    parser.add_argument('--report-file', default='reports/test_report.html',
                       help='Path for HTML test report (default: reports/test_report.html)')
    parser.add_argument('--keep-old-screenshots', action='store_true',
                       help='Keep old screenshots from previous test runs (default: clear old screenshots for clean reports)')
    
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
    
    # Restart ADB server first to ensure fresh detection
    print("   Refreshing ADB connection...")
    subprocess.run(['adb', 'kill-server'], capture_output=True)
    subprocess.run(['adb', 'start-server'], capture_output=True)
    time.sleep(2)  # Give ADB a moment to start
    
    # Check for connected devices
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
    
    if devices:
        print(f"✅ Found {len(devices)} connected device(s)")
        for device in devices:
            print(f"   - {device}")
        return True
    
    if not args.auto_emulator:
        print("❌ No Android devices/emulators connected")
        print("   Options:")
        print("   1. Start an Android emulator manually")
        print("   2. Connect a physical device")
        print("   3. Use --auto-emulator flag to start emulator automatically")
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
                if counter > 60 and counter % 30 == 0:
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

def start_appium_server(verbose=False):
    """Enhanced Appium server startup with health checks"""
    print("🚀 Starting Appium server...")
    
    # Use npx to run the local appium installation
    log_level = 'debug' if verbose else 'info'
    process = subprocess.Popen(
        ['npx', 'appium', '--base-path', '/wd/hub', '--log-level', log_level],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )
    
    # Wait for server to start with health checks
    print("⏳ Waiting for Appium server to start...")
    max_attempts = 20
    attempt = 0
    
    while attempt < max_attempts:
        time.sleep(1)
        attempt += 1
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("❌ Appium server failed to start")
            if verbose:
                print("STDOUT:", stdout.decode())
                print("STDERR:", stderr.decode())
            return None
        
        # Try to connect to server
        try:
            import requests
            response = requests.get('http://localhost:4723/wd/hub/status', timeout=2)
            if response.status_code == 200:
                print("✅ Appium server is ready and responding")
                return process
        except:
            # Server not ready yet, continue waiting
            pass
        
        if attempt % 5 == 0:
            print(f"   Still waiting... ({attempt}/{max_attempts})")
    
    print("❌ Appium server failed to respond within timeout")
    process.terminate()
    return None

def build_pytest_command(args):
    """Build pytest command based on arguments"""
    cmd = [sys.executable, '-m', 'pytest']
    
    # Test selection based on markers or specific files
    if args.tests:
        # Specific test files provided
        cmd.extend(args.tests)
    elif args.core:
        cmd.extend(['-m', 'core'])
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
        # Default: run core tests (recommended)
        print("ℹ️  No test suite specified, running core tests (recommended)")
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
    suite_name = "custom tests" if args.tests else "core tests"
    if args.core:
        suite_name = "core tests"
    elif args.mobile:
        suite_name = "mobile tests"
    elif args.legacy:
        suite_name = "legacy tests"
    elif args.integration:
        suite_name = "integration tests"
    
    mode_desc = " (fast mode)" if args.fast else " (full build mode)"
    print(f"🧪 Running {suite_name}{mode_desc}...")
    
    # Set up environment for testing
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Build pytest command
    cmd = build_pytest_command(args)
    
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
    suite = "core" if args.core else "mobile" if args.mobile else "legacy" if args.legacy else "integration" if args.integration else "custom" if args.tests else "core (default)"
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
    if not args.auto_emulator:
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

def cleanup_resources(appium_process, args, verbose=False):
    """Enhanced cleanup with app cleanup and emulator shutdown"""
    # 1. Stop Appium server
    if appium_process:
        print("🛑 Stopping Appium server...")
        try:
            appium_process.terminate()
            appium_process.wait(timeout=5)
            print("✅ Appium server stopped gracefully")
        except subprocess.TimeoutExpired:
            if verbose:
                print("   Force-killing Appium server...")
            appium_process.kill()
            appium_process.wait()
            print("✅ Appium server stopped (force-killed)")
        except Exception as e:
            if verbose:
                print(f"   Warning: Error stopping Appium server: {e}")
    
    # 2. Clean up test app and data
    cleanup_test_app(args, verbose)
    
    # 3. Shutdown emulator if auto-started
    shutdown_emulator(args, verbose)

def clear_old_screenshots(keep_old_screenshots=False, verbose=False):
    """
    Clear old screenshots to ensure HTML reports only show current test run screenshots.
    
    Args:
        keep_old_screenshots: If True, keep existing screenshots
        verbose: If True, show detailed output
    """
    screenshots_dir = Path(__file__).parent / "screenshots"
    
    if keep_old_screenshots:
        if verbose:
            print("📸 Keeping old screenshots as requested")
        return
    
    if not screenshots_dir.exists():
        if verbose:
            print("📸 No screenshots directory found, nothing to clear")
        return
    
    try:
        screenshot_files = list(screenshots_dir.glob("*.png"))
        if not screenshot_files:
            if verbose:
                print("📸 No old screenshots found")
            return
        
        print(f"🧹 Clearing {len(screenshot_files)} old screenshots for clean test report...")
        
        for screenshot_file in screenshot_files:
            try:
                screenshot_file.unlink()
                if verbose:
                    print(f"   Removed: {screenshot_file.name}")
            except Exception as e:
                print(f"   Warning: Could not remove {screenshot_file.name}: {e}")
        
        print("✅ Old screenshots cleared")
        
    except Exception as e:
        print(f"⚠️  Warning: Error clearing screenshots: {e}")

def main():
    """Enhanced main test runner function"""
    # Parse arguments first to handle help and early exits
    args = parse_arguments()
    
    print("📱 Enhanced Running Heatmap Mobile App Test Runner")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites(args):
        sys.exit(1)
    
    # Check and start emulator if needed
    if not check_and_start_emulator(args):
        sys.exit(1)
    
    # Create reports directory
    reports_dir = Path(__file__).parent / Path(args.report_file).parent
    reports_dir.mkdir(exist_ok=True)
    
    # Clear old screenshots for clean test reports (unless explicitly keeping them)
    clear_old_screenshots(args.keep_old_screenshots, args.verbose)
    
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
        open_test_report(args.report_file, args.no_browser)
        
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
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()