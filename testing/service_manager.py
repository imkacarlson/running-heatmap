#!/usr/bin/env python3
"""
Service management infrastructure for test optimization.
Provides persistent lifecycle management for emulator and Appium services.
"""

import os
import subprocess
import time
import psutil
import signal
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import requests

# Import modularized cleanup utilities from conftest for reuse
try:
    from .conftest import cleanup_all_test_artifacts, cleanup_mobile_driver, cleanup_app_installation, cleanup_emulator_state
except ImportError:
    # Fallback if running as standalone script
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from conftest import cleanup_all_test_artifacts, cleanup_mobile_driver, cleanup_app_installation, cleanup_emulator_state


@dataclass
class ServiceInfo:
    """Information about a running service."""
    pid: int
    name: str
    status: str
    started_time: datetime
    health_status: str = "unknown"
    restart_count: int = 0


@dataclass
class EmulatorInfo:
    """Information about emulator service."""
    device_serial: Optional[str] = None
    avd_name: str = "TestDevice"
    process: Optional[subprocess.Popen] = None
    startup_time: float = 0.0
    is_running: bool = False
    health_status: str = "unknown"
    service_info: Optional[ServiceInfo] = None


@dataclass
class AppiumInfo:
    """Information about Appium service."""
    server_url: str = "http://localhost:4723"
    process: Optional[subprocess.Popen] = None
    startup_time: float = 0.0
    is_running: bool = False
    health_status: str = "healthy"
    service_info: Optional[ServiceInfo] = None


@dataclass
class ServiceStatus:
    """Overall service status report."""
    emulator_running: bool
    appium_running: bool
    services_healthy: bool
    startup_time: float
    restart_needed: bool
    emulator_info: Optional[EmulatorInfo] = None
    appium_info: Optional[AppiumInfo] = None


class ServiceManager:
    """
    Manages lifecycle of emulator and Appium services for persistent test infrastructure.
    Supports both traditional isolated runs and persistent service mode.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize service manager."""
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.testing_root = self.project_root / "testing"
        self.cache_dir = self.testing_root / ".service_cache"
        self.service_state_file = self.cache_dir / "service_state.json"
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(exist_ok=True)
        
        # Default service configurations
        self.emulator_name = "TestDevice"
        self.appium_port = 4723
        self.appium_base_path = "/wd/hub"
        
        # Health check settings
        self.health_check_timeout = 30
        self.startup_timeout = 180  # 3 minutes for emulator startup
        self.appium_startup_timeout = 30
        
        # Service restart policies
        self.max_restart_attempts = 3
        self.restart_delay = 10  # seconds
        
    def _save_service_state(self, emulator_info: EmulatorInfo, appium_info: AppiumInfo):
        """Save current service state to cache."""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "emulator": {
                    "device_serial": emulator_info.device_serial,
                    "avd_name": emulator_info.avd_name,
                    "is_running": emulator_info.is_running,
                    "health_status": emulator_info.health_status,
                    "startup_time": emulator_info.startup_time,
                    "pid": emulator_info.process.pid if emulator_info.process else None
                },
                "appium": {
                    "server_url": appium_info.server_url,
                    "is_running": appium_info.is_running,
                    "health_status": appium_info.health_status,
                    "startup_time": appium_info.startup_time,
                    "pid": appium_info.process.pid if appium_info.process else None
                }
            }
            
            with open(self.service_state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save service state: {e}")
    
    def _load_service_state(self) -> Tuple[Optional[EmulatorInfo], Optional[AppiumInfo]]:
        """Load previous service state from cache."""
        try:
            if not self.service_state_file.exists():
                return None, None
            
            with open(self.service_state_file, 'r') as f:
                state = json.load(f)
            
            # Reconstruct EmulatorInfo
            emulator_data = state.get("emulator", {})
            emulator_info = EmulatorInfo(
                device_serial=emulator_data.get("device_serial"),
                avd_name=emulator_data.get("avd_name", "TestDevice"),
                is_running=emulator_data.get("is_running", False),
                health_status=emulator_data.get("health_status", "unknown"),
                startup_time=emulator_data.get("startup_time", 0.0)
            )
            
            # Check if process is still running
            pid = emulator_data.get("pid")
            if pid and psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    if "emulator" in proc.name().lower():
                        emulator_info.process = proc
                    else:
                        emulator_info.is_running = False
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    emulator_info.is_running = False
            else:
                emulator_info.is_running = False
            
            # Reconstruct AppiumInfo
            appium_data = state.get("appium", {})
            appium_info = AppiumInfo(
                server_url=appium_data.get("server_url", "http://localhost:4723"),
                is_running=appium_data.get("is_running", False),
                health_status=appium_data.get("health_status", "unknown"),
                startup_time=appium_data.get("startup_time", 0.0)
            )
            
            # Check if process is still running
            pid = appium_data.get("pid")
            if pid and psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    if "node" in proc.name().lower() or "appium" in " ".join(proc.cmdline()).lower():
                        appium_info.process = proc
                    else:
                        appium_info.is_running = False
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    appium_info.is_running = False
            else:
                appium_info.is_running = False
            
            return emulator_info, appium_info
        except Exception as e:
            print(f"Warning: Could not load service state: {e}")
            return None, None
    
    def _check_adb_devices(self) -> List[str]:
        """Check for available ADB devices."""
        try:
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                devices = []
                for line in lines:
                    if '\tdevice' in line:
                        device_serial = line.split('\t')[0]
                        devices.append(device_serial)
                return devices
        except Exception:
            pass
        return []
    
    def _check_emulator_health(self, device_serial: str) -> str:
        """Check emulator health status."""
        try:
            # Check boot completion
            result = subprocess.run([
                'adb', '-s', device_serial, 'shell', 'getprop', 'sys.boot_completed'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip() == '1':
                return "healthy"
            else:
                return "booting"
        except Exception:
            return "unhealthy"
    
    def _check_appium_health(self, server_url: str) -> str:
        """Check Appium server health status."""
        try:
            response = requests.get(f"{server_url}/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get("value", {}).get("ready", False):
                    return "healthy"
                else:
                    return "starting"
            else:
                return "unhealthy"
        except Exception:
            return "unreachable"
    
    def _configure_emulator_stability(self, device_serial: str):
        """
        Configure emulator settings for deterministic test behavior.
        Leverages existing emulator configuration from conftest.py.
        """
        print("   🎛️ Configuring emulator for deterministic behavior...")
        
        stability_commands = [
            # Disable all animations for deterministic behavior
            ['adb', '-s', device_serial, 'shell', 'settings', 'put', 'global', 'window_animation_scale', '0'],
            ['adb', '-s', device_serial, 'shell', 'settings', 'put', 'global', 'transition_animation_scale', '0'],
            ['adb', '-s', device_serial, 'shell', 'settings', 'put', 'global', 'animator_duration_scale', '0'],
            # Set consistent density (420 is standard for many devices)
            ['adb', '-s', device_serial, 'shell', 'wm', 'density', '420'],
            # Set consistent font scaling
            ['adb', '-s', device_serial, 'shell', 'settings', 'put', 'system', 'font_scale', '1.0'],
            # Lock orientation and screen size for WebView stability
            ['adb', '-s', device_serial, 'shell', 'settings', 'put', 'system', 'accelerometer_rotation', '0'],
            ['adb', '-s', device_serial, 'shell', 'settings', 'put', 'system', 'user_rotation', '0'],  # 0 = portrait
            ['adb', '-s', device_serial, 'shell', 'wm', 'size', '1080x1920'],
        ]
        
        for cmd in stability_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    setting_name = cmd[-2] if len(cmd) > 3 else "setting"
                    print(f"   ✅ {setting_name} = {cmd[-1]}")
                else:
                    print(f"   ⚠️ Warning: {' '.join(cmd[2:])} failed: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️ Warning: {' '.join(cmd[2:])} timed out")
            except Exception as e:
                print(f"   ⚠️ Warning: {' '.join(cmd[2:])} error: {e}")
        
        print("   ✅ Emulator stability configuration complete")
    
    def start_emulator_if_needed(self) -> EmulatorInfo:
        """Start emulator if not already running, return emulator info."""
        print("🔍 Checking emulator status...")
        
        # Check for existing devices
        devices = self._check_adb_devices()
        emulator_devices = [d for d in devices if d.startswith('emulator-')]
        
        if emulator_devices:
            device_serial = emulator_devices[0]
            health = self._check_emulator_health(device_serial)
            
            print(f"✅ Found running emulator: {device_serial} (status: {health})")
            
            # Apply stability configuration to existing emulator
            if health == "healthy":
                self._configure_emulator_stability(device_serial)
            
            return EmulatorInfo(
                device_serial=device_serial,
                avd_name=self.emulator_name,
                is_running=True,
                health_status=health,
                startup_time=0.0  # Already running
            )
        
        # Need to start emulator
        print(f"🚀 Starting emulator: {self.emulator_name}")
        start_time = time.time()
        
        try:
            # Check if emulator command is available
            subprocess.run(['emulator', '-help'], capture_output=True, check=False, timeout=5)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Android emulator not found. Please install Android SDK")
            raise RuntimeError("Emulator command not available")
        
        # Check if AVD exists
        try:
            result = subprocess.run(['emulator', '-list-avds'], capture_output=True, text=True, timeout=10)
            avds = result.stdout.strip().split('\n')
            if self.emulator_name not in avds:
                print(f"❌ AVD '{self.emulator_name}' not found")
                print("   Available AVDs:", avds)
                raise RuntimeError(f"AVD {self.emulator_name} not found")
        except subprocess.TimeoutExpired:
            print("❌ Timeout checking AVDs")
            raise RuntimeError("Timeout checking emulator AVDs")
        
        # Start emulator process
        print(f"   Starting {self.emulator_name} with optimized settings...")
        
        emulator_process = subprocess.Popen([
            'emulator', '-avd', self.emulator_name,
            '-no-window', '-no-audio', '-no-snapshot-save', '-no-snapshot-load',
            '-gpu', 'swiftshader_indirect', '-camera-back', 'none', '-camera-front', 'none'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for emulator to boot
        print("⏳ Waiting for emulator to boot...")
        timeout = self.startup_timeout
        
        for counter in range(1, timeout + 1):
            time.sleep(1)
            
            # Check if process is still alive
            if emulator_process.poll() is not None:
                stdout, stderr = emulator_process.communicate()
                print(f"❌ Emulator process died: {stderr}")
                raise RuntimeError("Emulator process terminated unexpectedly")
            
            # Check for ADB devices
            devices = self._check_adb_devices()
            emulator_devices = [d for d in devices if d.startswith('emulator-')]
            
            if emulator_devices:
                device_serial = emulator_devices[0]
                health = self._check_emulator_health(device_serial)
                
                if health == "healthy":
                    startup_time = time.time() - start_time
                    print(f"✅ Emulator ready: {device_serial} (started in {startup_time:.1f}s)")
                    
                    # Apply stability configuration from conftest.py
                    self._configure_emulator_stability(device_serial)
                    
                    emulator_info = EmulatorInfo(
                        device_serial=device_serial,
                        avd_name=self.emulator_name,
                        process=emulator_process,
                        startup_time=startup_time,
                        is_running=True,
                        health_status="healthy"
                    )
                    
                    return emulator_info
                elif health == "booting":
                    if counter % 10 == 0:  # Print every 10 seconds
                        print(f"   Emulator booting... ({counter}s)")
                else:
                    if counter % 15 == 0:  # Print every 15 seconds  
                        print(f"   Waiting for emulator health check... ({counter}s)")
            else:
                if counter % 20 == 0:  # Print every 20 seconds
                    print(f"   Waiting for emulator to appear in ADB... ({counter}s)")
        
        # Timeout reached
        startup_time = time.time() - start_time
        print(f"❌ Emulator startup timeout ({startup_time:.1f}s)")
        
        try:
            emulator_process.terminate()
        except Exception:
            pass
        
        raise RuntimeError("Emulator failed to start within timeout")
    
    def start_appium_if_needed(self) -> AppiumInfo:
        """Start Appium server if not already running, return server info."""
        server_url = f"http://localhost:{self.appium_port}"
        
        print("🔍 Checking Appium server status...")
        
        # Check if Appium is already running
        health = self._check_appium_health(server_url)
        if health == "healthy":
            print(f"✅ Appium server already running: {server_url}")
            return AppiumInfo(
                server_url=server_url,
                is_running=True,
                health_status="healthy",
                startup_time=0.0  # Already running
            )
        
        # Need to start Appium
        print(f"🚀 Starting Appium server on port {self.appium_port}...")
        start_time = time.time()
        
        try:
            # Start Appium server
            cmd = ['npx', 'appium', '--base-path', self.appium_base_path, '--port', str(self.appium_port)]
            
            appium_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print("⏳ Waiting for Appium server to start...")
            
            # Wait for server to be ready
            for counter in range(1, self.appium_startup_timeout + 1):
                time.sleep(1)
                
                # Check if process is still alive
                if appium_process.poll() is not None:
                    stdout, stderr = appium_process.communicate()
                    print(f"❌ Appium process died: {stderr}")
                    raise RuntimeError("Appium process terminated unexpectedly")
                
                # Check server health
                health = self._check_appium_health(server_url)
                if health == "healthy":
                    startup_time = time.time() - start_time
                    print(f"✅ Appium server ready (started in {startup_time:.1f}s)")
                    
                    return AppiumInfo(
                        server_url=server_url,
                        process=appium_process,
                        startup_time=startup_time,
                        is_running=True,
                        health_status="healthy"
                    )
                elif counter % 5 == 0:  # Print every 5 seconds
                    print(f"   Waiting for Appium server... ({counter}s)")
            
            # Timeout reached
            startup_time = time.time() - start_time
            print(f"❌ Appium startup timeout ({startup_time:.1f}s)")
            
            try:
                appium_process.terminate()
            except Exception:
                pass
            
            raise RuntimeError("Appium server failed to start within timeout")
            
        except Exception as e:
            print(f"❌ Failed to start Appium server: {e}")
            raise
    
    def health_check_services(self, emulator_info: EmulatorInfo, appium_info: AppiumInfo) -> ServiceStatus:
        """Perform comprehensive health check on all services."""
        start_time = time.time()
        
        # Check emulator health
        emulator_healthy = False
        if emulator_info.is_running and emulator_info.device_serial:
            health = self._check_emulator_health(emulator_info.device_serial)
            emulator_info.health_status = health
            emulator_healthy = (health == "healthy")
        
        # Check Appium health
        appium_healthy = False
        if appium_info.is_running:
            health = self._check_appium_health(appium_info.server_url)
            appium_info.health_status = health
            appium_healthy = (health == "healthy")
        
        services_healthy = emulator_healthy and appium_healthy
        restart_needed = not services_healthy
        
        total_startup_time = emulator_info.startup_time + appium_info.startup_time
        check_time = time.time() - start_time
        
        return ServiceStatus(
            emulator_running=emulator_info.is_running,
            appium_running=appium_info.is_running,
            services_healthy=services_healthy,
            startup_time=total_startup_time,
            restart_needed=restart_needed,
            emulator_info=emulator_info,
            appium_info=appium_info
        )
    
    def restart_unhealthy_services(self, emulator_info: EmulatorInfo, appium_info: AppiumInfo) -> Tuple[EmulatorInfo, AppiumInfo]:
        """Restart any unhealthy services."""
        print("🔄 Restarting unhealthy services...")
        
        # Restart emulator if needed
        if emulator_info.health_status != "healthy":
            print("   🔄 Restarting emulator...")
            try:
                self.cleanup_emulator(emulator_info)
                time.sleep(self.restart_delay)
                emulator_info = self.start_emulator_if_needed()
                # Stability configuration is applied in start_emulator_if_needed()
            except Exception as e:
                print(f"   ❌ Failed to restart emulator: {e}")
        
        # Restart Appium if needed
        if appium_info.health_status != "healthy":
            print("   🔄 Restarting Appium server...")
            try:
                self.cleanup_appium(appium_info)
                time.sleep(self.restart_delay)
                appium_info = self.start_appium_if_needed()
            except Exception as e:
                print(f"   ❌ Failed to restart Appium: {e}")
        
        return emulator_info, appium_info
    
    def cleanup_emulator(self, emulator_info: EmulatorInfo):
        """Clean up emulator service."""
        if not emulator_info.is_running:
            return
        
        print("🔌 Shutting down emulator...")
        
        try:
            if emulator_info.device_serial:
                # Try graceful shutdown first
                result = subprocess.run([
                    'adb', '-s', emulator_info.device_serial, 'emu', 'kill'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print("   ✅ Emulator shutdown command sent")
                    
                    # Wait for shutdown
                    for _ in range(15):  # Wait up to 15 seconds
                        time.sleep(1)
                        devices = self._check_adb_devices()
                        if emulator_info.device_serial not in devices:
                            print("   ✅ Emulator shut down gracefully")
                            emulator_info.is_running = False
                            return
            
            # Force kill if process exists
            if emulator_info.process:
                try:
                    if isinstance(emulator_info.process, subprocess.Popen):
                        emulator_info.process.terminate()
                        emulator_info.process.wait(timeout=5)
                    elif isinstance(emulator_info.process, psutil.Process):
                        emulator_info.process.terminate()
                        emulator_info.process.wait(timeout=5)
                    print("   ✅ Emulator process terminated")
                except (subprocess.TimeoutExpired, psutil.TimeoutExpired):
                    if isinstance(emulator_info.process, subprocess.Popen):
                        emulator_info.process.kill()
                    elif isinstance(emulator_info.process, psutil.Process):
                        emulator_info.process.kill()
                    print("   ✅ Emulator process killed")
            
            emulator_info.is_running = False
            
        except Exception as e:
            print(f"   ⚠️ Warning: Error during emulator cleanup: {e}")
    
    def cleanup_appium(self, appium_info: AppiumInfo):
        """Clean up Appium service."""
        if not appium_info.is_running:
            return
        
        print("🔌 Shutting down Appium server...")
        
        try:
            if appium_info.process:
                try:
                    if isinstance(appium_info.process, subprocess.Popen):
                        appium_info.process.terminate()
                        appium_info.process.wait(timeout=5)
                    elif isinstance(appium_info.process, psutil.Process):
                        appium_info.process.terminate()
                        appium_info.process.wait(timeout=5)
                    print("   ✅ Appium server stopped")
                except (subprocess.TimeoutExpired, psutil.TimeoutExpired):
                    if isinstance(appium_info.process, subprocess.Popen):
                        appium_info.process.kill()
                    elif isinstance(appium_info.process, psutil.Process):
                        appium_info.process.kill()
                    print("   ✅ Appium server killed")
            
            appium_info.is_running = False
            
        except Exception as e:
            print(f"   ⚠️ Warning: Error during Appium cleanup: {e}")
    
    def cleanup_services(self, emulator_info: EmulatorInfo, appium_info: AppiumInfo, force: bool = False):
        """Clean up all services."""
        print("🧹 Cleaning up services...")
        
        # Clean up Appium first
        self.cleanup_appium(appium_info)
        
        # Clean up emulator
        self.cleanup_emulator(emulator_info)
        
        # Clear service state
        try:
            if self.service_state_file.exists():
                self.service_state_file.unlink()
        except Exception as e:
            print(f"   ⚠️ Warning: Could not clear service state: {e}")
        
        print("✅ Service cleanup complete")
    
    def cleanup_test_artifacts(self, package_name="com.run.heatmap", test_env_path=None, driver=None):
        """
        Clean up test artifacts using modularized cleanup utilities from conftest.
        This leverages the reusable cleanup functions for consistency across scripts.
        """
        print("🧹 Cleaning up test artifacts using shared cleanup utilities...")
        cleanup_all_test_artifacts(package_name, test_env_path, driver)
    
    def setup_persistent_infrastructure(self) -> ServiceStatus:
        """Set up persistent test infrastructure with emulator and Appium."""
        print("🚀 Setting up persistent test infrastructure...")
        
        total_start_time = time.time()
        
        try:
            # Start emulator
            emulator_info = self.start_emulator_if_needed()
            
            # Start Appium
            appium_info = self.start_appium_if_needed()
            
            # Perform health check
            status = self.health_check_services(emulator_info, appium_info)
            
            # Save service state for future runs
            self._save_service_state(emulator_info, appium_info)
            
            total_time = time.time() - total_start_time
            print(f"✅ Persistent infrastructure ready (total time: {total_time:.1f}s)")
            
            return status
            
        except Exception as e:
            print(f"❌ Failed to set up persistent infrastructure: {e}")
            raise
    
    def get_existing_infrastructure(self) -> Optional[ServiceStatus]:
        """Check for existing persistent infrastructure."""
        print("🔍 Checking for existing persistent infrastructure...")
        
        # Load previous service state
        emulator_info, appium_info = self._load_service_state()
        
        if not emulator_info or not appium_info:
            print("   No previous service state found")
            return None
        
        # Perform health check
        status = self.health_check_services(emulator_info, appium_info)
        
        if status.services_healthy:
            print("✅ Found healthy persistent infrastructure")
            return status
        else:
            print("⚠️ Found persistent infrastructure with health issues")
            return status


def main():
    """Command line interface for service management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Service management for test optimization")
    parser.add_argument("--setup", action="store_true", help="Set up persistent infrastructure")
    parser.add_argument("--status", action="store_true", help="Check service status")
    parser.add_argument("--cleanup", action="store_true", help="Clean up all services")
    parser.add_argument("--restart", action="store_true", help="Restart unhealthy services")
    parser.add_argument("--health-check", action="store_true", help="Perform health check")
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.setup:
        try:
            status = manager.setup_persistent_infrastructure()
            print(f"Infrastructure status: {'healthy' if status.services_healthy else 'unhealthy'}")
            return status.services_healthy
        except Exception as e:
            print(f"Failed to setup infrastructure: {e}")
            return False
    
    if args.status:
        status = manager.get_existing_infrastructure()
        if status:
            print(f"Emulator running: {status.emulator_running}")
            print(f"Appium running: {status.appium_running}")
            print(f"Services healthy: {status.services_healthy}")
            return status.services_healthy
        else:
            print("No infrastructure found")
            return False
    
    if args.cleanup:
        # Get existing services first
        emulator_info, appium_info = manager._load_service_state()
        if emulator_info is None:
            emulator_info = EmulatorInfo()
        if appium_info is None:
            appium_info = AppiumInfo()
        
        manager.cleanup_services(emulator_info, appium_info, force=True)
        return True
    
    if args.restart:
        status = manager.get_existing_infrastructure()
        if status and status.restart_needed:
            try:
                emulator_info, appium_info = manager.restart_unhealthy_services(
                    status.emulator_info, status.appium_info
                )
                new_status = manager.health_check_services(emulator_info, appium_info)
                print(f"After restart - Services healthy: {new_status.services_healthy}")
                return new_status.services_healthy
            except Exception as e:
                print(f"Failed to restart services: {e}")
                return False
        else:
            print("No services need restart or no services found")
            return True
    
    if args.health_check:
        status = manager.get_existing_infrastructure()
        if status:
            print(f"Health check results:")
            print(f"  Emulator: {status.emulator_info.health_status if status.emulator_info else 'not found'}")
            print(f"  Appium: {status.appium_info.health_status if status.appium_info else 'not found'}")
            return status.services_healthy
        else:
            print("No services found for health check")
            return False
    
    # Default: show current status
    status = manager.get_existing_infrastructure()
    if status:
        print("Current Infrastructure Status:")
        print(f"  Emulator running: {status.emulator_running}")
        print(f"  Appium running: {status.appium_running}")
        print(f"  Services healthy: {status.services_healthy}")
        print(f"  Total startup time: {status.startup_time:.1f}s")
        return status.services_healthy
    else:
        print("No persistent infrastructure found")
        print("Use --setup to create persistent infrastructure")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)