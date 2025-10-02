#!/usr/bin/env python3
"""
Manual testing script for the running heatmap mobile app

This script sets up the testing environment (emulator, app, test data) and then
allows the user to manually test the app. When the user is done, it automatically
cleans up everything just like the automated test runner.

Features:
- Automatic emulator management (same as run_tests.py)
- Installs APK with test data
- Pushes test activity files
- Interactive session for manual testing
- Comprehensive cleanup on completion
"""

import sys
import time
import subprocess
import signal
import os
import argparse
from pathlib import Path

# Import all the helper functions from run_tests.py
import importlib.util
spec = importlib.util.spec_from_file_location("run_tests", Path(__file__).parent / "run_tests.py")
run_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_tests)

def parse_manual_arguments():
    """Parse command line arguments for manual testing"""
    parser = argparse.ArgumentParser(
        description="Manual testing script for Running Heatmap mobile app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manual_test.py                     # Auto-start emulator, full setup
  python manual_test.py --fast              # Use existing APK, skip build
  python manual_test.py --manual-emulator   # Use manually started emulator
  python manual_test.py --keep-emulator     # Don't shutdown emulator when done
  python manual_test.py --keep-app          # Don't uninstall app when done
        """
    )
    
    # Build options
    parser.add_argument('--fast', action='store_true',
                       help='Skip APK build and tile generation (use existing APK)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output for debugging')
    
    # Emulator management
    parser.add_argument('--manual-emulator', action='store_true',
                       help='Use manually started emulator (don\'t auto-start)')
    parser.add_argument('--emulator-name', default='TestDevice',
                       help='Name of AVD to start (default: TestDevice)')
    parser.add_argument('--keep-emulator', action='store_true',
                       help='Keep emulator running after manual testing session')
    parser.add_argument('--keep-app', action='store_true',
                       help='Keep test app installed after session ends')
    
    return parser.parse_args()

def setup_test_environment(args):
    """Set up the complete testing environment"""
    print("\n🚀 SETTING UP MANUAL TESTING ENVIRONMENT")
    print("=" * 60)

    # Import infrastructure setup functions
    from infrastructure_setup import (
        check_and_start_emulator,
        start_appium_server,
        PerformanceMetrics
    )

    # Create metrics object to track setup performance
    metrics = PerformanceMetrics()

    # Check prerequisites
    print("Step 1: Checking prerequisites...")
    if not run_tests.check_prerequisites(args, None):
        return False, None, None

    # Check and start emulator
    print("\nStep 2: Setting up emulator...")
    emulator_result = check_and_start_emulator(metrics)
    if not emulator_result:
        return False, None, None

    # Start Appium server
    print("\nStep 3: Starting Appium server...")
    appium_process = start_appium_server(metrics)
    if appium_process is None:
        print("❌ Failed to start Appium server")
        return False, None, None

    return True, appium_process, emulator_result.get('started_emulator', False)

def install_test_app(args):
    """Install the test app with data using pytest infrastructure"""
    print("\nStep 4: Installing test app...")
    
    # We need to run the infrastructure setup that builds/installs the APK
    # This mimics what the test_00_infrastructure_setup.py does
    
    try:
        # Set up environment for pytest infrastructure
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent)
        
        # Run only the infrastructure setup test
        cmd = [
            sys.executable, '-m', 'pytest', 
            'test_00_infrastructure_setup.py',
            '-v', '--tb=short'
        ]
        
        if args.fast:
            cmd.append('--fast')
            
        if args.verbose:
            cmd.append('-vv')
            print(f"   Running command: {' '.join(cmd)}")
        
        print("   📱 Building and installing APK with test data...")
        result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
        
        if result.returncode == 0:
            print("   ✅ Test app installed successfully!")
            return True
        else:
            print("   ❌ Failed to install test app")
            return False
            
    except Exception as e:
        print(f"   ❌ Error installing test app: {e}")
        return False

def push_test_files():
    """Push test activity files to the emulator"""
    print("\nStep 5: Pushing test activity files...")
    
    test_data_dir = Path(__file__).parent / "test_data"
    
    try:
        # Push manual upload test file (the main one for manual testing)
        manual_upload_file = test_data_dir / "manual_upload_run.gpx"
        if manual_upload_file.exists():
            print("   📄 Pushing manual_upload_run.gpx...")
            result = subprocess.run([
                'adb', 'push', str(manual_upload_file), 
                '/sdcard/Download/manual_upload_run.gpx'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ manual_upload_run.gpx pushed successfully")
            else:
                print(f"   ⚠️  Warning: Could not push manual_upload_run.gpx: {result.stderr}")
        else:
            print("   ⚠️  Warning: manual_upload_run.gpx not found in test_data directory")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Warning: Error pushing test files: {e}")
        return True  # Don't fail the whole process for this

def launch_app():
    """Launch the test app"""
    print("\nStep 6: Launching the Running Heatmap app...")
    
    try:
        # Launch the app
        result = subprocess.run([
            'adb', 'shell', 'am', 'start', 
            '-n', 'com.run.heatmap/.MainActivity'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ App launched successfully!")
            # Give the app a moment to start up
            time.sleep(3)
            return True
        else:
            print(f"   ❌ Failed to launch app: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error launching app: {e}")
        return False

def print_manual_testing_instructions():
    """Display instructions for manual testing"""
    print("\n" + "=" * 60)
    print("🎯 MANUAL TESTING SESSION ACTIVE")
    print("=" * 60)
    print("✅ Setup complete! Your testing environment is ready:")
    print()
    print("📱 Emulator: Running with Running Heatmap app installed")
    print("🗂️  Test data: PMTiles data loaded with sample activities")
    print("📄 Test files: GPX files available in /sdcard/Download/")
    print("🔧 Appium: Server running for app interactions")
    print()
    print("📋 SUGGESTED TESTING ACTIVITIES:")
    print("   • Test map loading and navigation")
    print("   • Try the lasso selection tool")
    print("   • Upload GPX files from /sdcard/Download/")
    print("   • Test activity toggling and filtering")
    print("   • Check PMTiles vector rendering")
    print("   • Test app performance and responsiveness")
    print()
    print("📁 Available test file in device Downloads:")
    print("   • manual_upload_run.gpx")
    print()
    print("🎮 TEST AT YOUR OWN PACE")
    print("   When you're finished testing, press Enter to clean up")
    print("   Or press Ctrl+C to interrupt and clean up")
    print("=" * 60)

def wait_for_user_completion():
    """Wait for user to complete manual testing"""
    try:
        print("\n⏳ Press Enter when you're done testing (or Ctrl+C to interrupt)...")
        input()
        print("\n🏁 Manual testing session ended by user")
        return True
    except KeyboardInterrupt:
        print("\n\n⏹️  Manual testing session interrupted by user")
        return True
    except Exception as e:
        print(f"\n❌ Unexpected error during testing session: {e}")
        return False

def main():
    """Main manual testing function"""
    args = parse_manual_arguments()

    print("🧪 Running Heatmap Manual Testing Script")
    print("This will set up everything for manual testing, then clean up when done")
    print("=" * 60)

    appium_process = None
    started_emulator = False
    success = False

    try:
        # Set up the testing environment
        setup_success, appium_process, started_emulator = setup_test_environment(args)
        if not setup_success:
            print("\n❌ Failed to set up testing environment")
            return 1
        
        # Install test app
        if not install_test_app(args):
            print("\n❌ Failed to install test app")
            return 1
        
        # Push test files
        push_test_files()
        
        # Launch the app
        if not launch_app():
            print("\n❌ Failed to launch app")
            return 1
        
        # Display instructions and wait for user
        print_manual_testing_instructions()
        success = wait_for_user_completion()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Manual testing interrupted by user")
        return 0
        
    except Exception as e:
        print(f"\n❌ Unexpected error in manual testing: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
        
    finally:
        # Clean up everything using the infrastructure functions
        print("\n🧹 CLEANING UP TESTING ENVIRONMENT")
        print("=" * 60)

        # Import cleanup functions
        from infrastructure_setup import cleanup_appium_server, shutdown_emulator

        # Stop Appium server
        if appium_process:
            cleanup_appium_server(appium_process)

        # Uninstall app if requested (default is to uninstall)
        if not args.keep_app:
            print("🗑️  Uninstalling test app...")
            try:
                subprocess.run(['adb', 'uninstall', 'com.run.heatmap'],
                             capture_output=True, text=True)
                print("✅ Test app uninstalled")
            except Exception as e:
                print(f"⚠️  Warning: Could not uninstall app: {e}")
        else:
            print("📱 Keeping app installed (--keep-app flag)")

        # Shutdown emulator if we started it and user doesn't want to keep it
        if started_emulator and not args.keep_emulator and not args.manual_emulator:
            shutdown_emulator()
        elif args.keep_emulator:
            print("📱 Keeping emulator running (--keep-emulator flag)")
        else:
            print("📱 Emulator was already running, leaving it running")

        print("\n✅ Cleanup complete!")
        print("🎉 Manual testing session finished")

if __name__ == '__main__':
    sys.exit(main())