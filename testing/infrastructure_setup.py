#!/usr/bin/env python3
"""
Infrastructure setup module for emulator and Appium server management.
Extracted from the working test runner for reuse in persistent mode.
"""
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """Performance monitoring data for test execution."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    emulator_startup_time: float = 0.0
    appium_startup_time: float = 0.0
    build_time: float = 0.0
    data_processing_time: float = 0.0
    test_execution_time: float = 0.0
    total_time: float = 0.0
    cache_hits: Dict[str, bool] = field(default_factory=dict)
    optimizations_applied: List[str] = field(default_factory=list)
    
    def add_optimization(self, optimization: str):
        """Record an optimization that was applied."""
        self.optimizations_applied.append(optimization)


def check_and_start_emulator(metrics: PerformanceMetrics):
    """Check for devices and auto-start emulator if needed"""
    emulator_start_time = time.time()
    print("📱 Checking for connected devices...")
    
    # Check for connected devices
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    devices = [line for line in result.stdout.split('\n') if '\tdevice' in line]
    
    if devices:
        print(f"✅ Found {len(devices)} connected device(s)")
        for device in devices:
            print(f"   - {device}")
        metrics.emulator_startup_time = time.time() - emulator_start_time
        metrics.add_optimization("Emulator already running")
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
                        metrics.emulator_startup_time = time.time() - emulator_start_time
                        print(f"✅ Emulator is ready! (started in {metrics.emulator_startup_time:.1f}s)")
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
    
    metrics.emulator_startup_time = time.time() - emulator_start_time
    print(f"❌ Emulator failed to start within timeout ({metrics.emulator_startup_time:.1f}s)")
    emulator_process.terminate()
    return {'started_emulator': False}


def start_appium_server(metrics: PerformanceMetrics):
    """Start Appium server"""
    appium_start_time = time.time()
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
                    metrics.appium_startup_time = time.time() - appium_start_time
                    print(f"✅ Appium server is ready (started in {metrics.appium_startup_time:.1f}s)")
                    return process
            except:
                continue
        
        metrics.appium_startup_time = time.time() - appium_start_time
        print(f"❌ Appium server failed to start within timeout ({metrics.appium_startup_time:.1f}s)")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start Appium server: {e}")
        return None


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