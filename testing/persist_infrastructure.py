#!/usr/bin/env python3
"""
Simple persistent infrastructure runner for emulator and Appium server.
Uses the proven working setup code from run_tests.py for reliability.
"""
import sys
import signal
import time
from pathlib import Path

# Import the working infrastructure functions
from infrastructure_setup import (
    PerformanceMetrics,
    check_dependencies,
    check_and_start_emulator,
    start_appium_server,
    cleanup_appium_server,
    shutdown_emulator
)

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class PersistentInfrastructure:
    """Simple persistent infrastructure manager using proven working code."""
    
    def __init__(self):
        self.emulator_info = None
        self.appium_process = None
        self.running = False
        self.metrics = PerformanceMetrics()
        
    def setup_signal_handlers(self):
        """Setup signal handlers for clean shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n{YELLOW}🔌 Received shutdown signal, cleaning up...{NC}")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start the persistent infrastructure."""
        print(f"{BLUE}🚀 Starting Persistent Test Infrastructure{NC}")
        print(f"{BLUE}{'='*50}{NC}")
        
        try:
            # Check dependencies first
            print(f"{BLUE}🔍 Checking dependencies...{NC}")
            if not check_dependencies():
                return False
            print(f"{GREEN}✅ Dependencies check complete{NC}")
            
            # Start emulator
            print(f"\n{BLUE}📱 Setting up emulator...{NC}")
            emulator_result = check_and_start_emulator(self.metrics)
            if emulator_result is False:
                print(f"{RED}❌ Failed to start emulator{NC}")
                return False
            
            self.emulator_info = emulator_result
            print(f"{GREEN}✅ Emulator ready{NC}")
            
            # Start Appium server
            print(f"\n{BLUE}🔧 Setting up Appium server...{NC}")
            appium_process = start_appium_server(self.metrics)
            if appium_process is None:
                print(f"{RED}❌ Failed to start Appium server{NC}")
                self.cleanup()
                return False
            
            self.appium_process = appium_process
            print(f"{GREEN}✅ Appium server ready{NC}")
            
            self.running = True
            
            print(f"\n{GREEN}🎉 Persistent infrastructure is now running!{NC}")
            print(f"{GREEN}{'='*50}{NC}")
            print(f"{YELLOW}💡 Usage:{NC}")
            print(f"   • Run {GREEN}./test.sh{NC} in another terminal to execute tests")
            print(f"   • Tests will use this persistent infrastructure for faster execution")
            print(f"   • Press {GREEN}Enter{NC} or {GREEN}Ctrl+C{NC} to stop this infrastructure")
            print(f"{GREEN}{'='*50}{NC}")
            
            return True
            
        except Exception as e:
            print(f"{RED}❌ Failed to start infrastructure: {e}{NC}")
            self.cleanup()
            return False
    
    def wait_for_stop_signal(self):
        """Wait for user input or signal to stop."""
        try:
            print(f"\n{BLUE}🔄 Infrastructure running... Press Enter to stop.{NC}")
            input()  # Wait for user to press Enter
            print(f"{YELLOW}🔌 Stopping infrastructure...{NC}")
        except KeyboardInterrupt:
            print(f"\n{YELLOW}🔌 Received Ctrl+C, stopping infrastructure...{NC}")
        except EOFError:
            # Handle case where input is redirected
            print(f"{YELLOW}🔌 Input closed, stopping infrastructure...{NC}")
        
    def stop(self):
        """Stop the persistent infrastructure."""
        if not self.running:
            return
        
        self.running = False
        self.cleanup()
    
    def cleanup(self):
        """Clean up all infrastructure components."""
        print(f"{BLUE}🧹 Cleaning up infrastructure...{NC}")
        
        # Stop Appium server
        if self.appium_process:
            cleanup_appium_server(self.appium_process)
            self.appium_process = None
        
        # Shutdown emulator
        if self.emulator_info:
            shutdown_emulator(self.emulator_info)
            self.emulator_info = None
        
        print(f"{GREEN}✅ Infrastructure cleanup complete{NC}")
    
    def get_status(self):
        """Get current infrastructure status."""
        if not self.running:
            return "Infrastructure not running"
        
        status = []
        if self.emulator_info:
            if self.emulator_info.get('started_emulator', False):
                status.append("Emulator: Started by this script")
            else:
                status.append("Emulator: Using existing device")
        else:
            status.append("Emulator: Not available")
        
        if self.appium_process and self.appium_process.poll() is None:
            status.append("Appium: Running")
        else:
            status.append("Appium: Not running")
        
        return " | ".join(status)


def show_help():
    """Show usage information."""
    print(f"{BLUE}🔧 Persistent Test Infrastructure{NC}")
    print(f"{BLUE}{'='*40}{NC}")
    print(f"\n{YELLOW}Usage:{NC}")
    print(f"   {GREEN}python persist_infrastructure.py{NC}     # Start persistent infrastructure")
    print(f"   {GREEN}python persist_infrastructure.py --help{NC} # Show this help")
    print(f"\n{YELLOW}Description:{NC}")
    print(f"   This script starts and manages persistent test infrastructure")
    print(f"   (emulator + Appium server) for faster test iterations.")
    print(f"\n{YELLOW}Workflow:{NC}")
    print(f"   1. Run this script to start persistent infrastructure")
    print(f"   2. Run {GREEN}./test.sh{NC} in other terminals for fast test execution")
    print(f"   3. Press Enter or Ctrl+C in this terminal to stop when done")
    print(f"\n{YELLOW}Benefits:{NC}")
    print(f"   • No emulator startup time between test runs")
    print(f"   • Consistent test environment")
    print(f"   • Faster development iteration")


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return 0
    
    # Create and configure infrastructure manager
    infra = PersistentInfrastructure()
    infra.setup_signal_handlers()
    
    try:
        # Start infrastructure
        if not infra.start():
            print(f"{RED}❌ Failed to start persistent infrastructure{NC}")
            return 1
        
        # Wait for stop signal
        infra.wait_for_stop_signal()
        
        # Clean shutdown
        infra.stop()
        
        print(f"{GREEN}👋 Persistent infrastructure stopped successfully{NC}")
        return 0
        
    except Exception as e:
        print(f"{RED}❌ Unexpected error: {e}{NC}")
        infra.cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())