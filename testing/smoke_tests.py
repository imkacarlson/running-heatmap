#!/usr/bin/env python3
"""
Standalone smoke test runner for Running Heatmap mobile app
Fast validation of core functionality without emulator overhead
"""
import sys
import argparse
from pathlib import Path

# Add the testing directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from smoke_tests.smoke_test_runner import SmokeTestRunner, run_smoke_tests_with_pytest


def main():
    """Main entry point for standalone smoke test runner"""
    parser = argparse.ArgumentParser(
        description="Fast smoke tests for Running Heatmap mobile app (< 5 seconds)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smoke_tests.py                        # Run all smoke tests
  python smoke_tests.py --components data      # Run data pipeline tests only
  python smoke_tests.py --components server api # Run server and API tests
  python smoke_tests.py --pytest              # Use pytest integration
  python smoke_tests.py --verbose             # Verbose output
        """
    )
    
    parser.add_argument('--components', nargs='+', 
                       choices=['data', 'server', 'api', 'web', 'build', 'mobile'],
                       help='Specific components to test (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--pytest', action='store_true',
                       help='Use pytest integration instead of direct runner')
    parser.add_argument('--no-timing', action='store_true',
                       help='Disable timing validation (for debugging)')
    
    args = parser.parse_args()
    
    print("🚀 Running Heatmap Mobile App Smoke Tests")
    print("=" * 50)
    
    if args.pytest:
        print("📋 Using pytest integration...")
        exit_code = run_smoke_tests_with_pytest(args.components, args.verbose)
    else:
        print("📋 Using direct smoke test runner...")
        
        # Create and configure runner
        from smoke_tests.smoke_test_runner import SmokeTestConfig
        config = SmokeTestConfig()
        
        if args.no_timing:
            # Disable timing constraints for debugging
            config.server_timeout = 30
            config.api_timeout = 30
            config.web_timeout = 30
            config.mobile_timeout = 30
        
        runner = SmokeTestRunner(config)
        result = runner.run_all_smoke_tests(args.components)
        
        # Exit with appropriate code
        exit_code = 0 if result.failed == 0 else 1
        
        # Additional summary for standalone mode
        if exit_code == 0:
            print("\n🎉 All smoke tests passed! System appears healthy.")
            print("💡 You can now run full tests with confidence:")
            print("   python run_tests.py --core")
        else:
            print(f"\n❌ {result.failed} smoke test(s) failed.")
            print("💡 Fix these issues before running full tests:")
            for failure in result.failures:
                if failure.suggestion:
                    print(f"   • {failure.component}: {failure.suggestion}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()