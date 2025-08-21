#!/usr/bin/env python3
"""
Optimized test runner for the running heatmap mobile app
Supports intelligent optimization with change detection and fast mode
"""
import sys
import time
import subprocess
import signal
import os
import argparse
import webbrowser
import concurrent.futures
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from change_detector import ChangeDetector, BuildOptimization
from infrastructure_setup import (
    check_dependencies,
    check_and_start_emulator,
    start_appium_server,
    cleanup_appium_server,
    shutdown_emulator
)

def check_for_persistent_infrastructure():
    """Simple check for persistent infrastructure availability."""
    try:
        # Check if emulator is running
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=5)
        has_emulator = 'emulator-' in result.stdout and 'device' in result.stdout
        
        # Check if Appium is running
        import requests
        response = requests.get("http://localhost:4723/wd/hub/status", timeout=3)
        has_appium = response.status_code == 200 and 'ready' in response.text
        
        return has_emulator and has_appium
    except:
        return False

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
    parallel_execution_time: float = 0.0
    sequential_fallback_time: float = 0.0
    parallel_workers_used: int = 0
    parallel_execution_details: Dict[str, any] = field(default_factory=dict)
    test_group_timings: Dict[str, Dict[str, any]] = field(default_factory=dict)
    
    def add_optimization(self, optimization: str):
        """Record an optimization that was applied."""
        self.optimizations_applied.append(optimization)
    
    def set_cache_hit(self, cache_type: str, hit: bool):
        """Record whether a cache was hit or missed."""
        self.cache_hits[cache_type] = hit
    
    def record_test_group_execution(self, group_name: str, execution_time: float, 
                                  execution_info: Dict[str, any]):
        """Record execution details for a specific test group."""
        self.test_group_timings[group_name] = {
            'execution_time': execution_time,
            'execution_method': execution_info.get('method', 'unknown'),
            'parallel_used': execution_info.get('parallel_used', False),
            'workers': execution_info.get('workers', 0),
            'test_count': execution_info.get('test_count', 0)
        }
    
    def calculate_parallel_efficiency(self) -> Optional[Dict[str, float]]:
        """Calculate parallel execution efficiency metrics."""
        parallel_time = sum(
            timing['execution_time'] 
            for timing in self.test_group_timings.values() 
            if timing.get('parallel_used', False)
        )
        
        sequential_time = sum(
            timing['execution_time'] 
            for timing in self.test_group_timings.values() 
            if not timing.get('parallel_used', False)
        )
        
        if parallel_time > 0 and sequential_time > 0:
            total_time = parallel_time + sequential_time
            return {
                'parallel_portion': parallel_time / total_time,
                'sequential_portion': sequential_time / total_time,
                'total_parallel_time': parallel_time,
                'total_sequential_time': sequential_time
            }
        return None
    
    def finalize(self):
        """Calculate final metrics when execution completes."""
        self.end_time = datetime.now()
        self.total_time = (self.end_time - self.start_time).total_seconds()
        self.parallel_execution_details = self.calculate_parallel_efficiency()
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary of performance metrics."""
        return {
            'total_time_seconds': self.total_time,
            'emulator_startup_seconds': self.emulator_startup_time,
            'appium_startup_seconds': self.appium_startup_time,
            'build_time_seconds': self.build_time,
            'data_processing_seconds': self.data_processing_time,
            'test_execution_seconds': self.test_execution_time,
            'parallel_execution_seconds': self.parallel_execution_time,
            'sequential_fallback_seconds': self.sequential_fallback_time,
            'parallel_workers_used': self.parallel_workers_used,
            'parallel_execution_details': self.parallel_execution_details,
            'test_group_timings': self.test_group_timings,
            'cache_hits': self.cache_hits,
            'optimizations_applied': self.optimizations_applied
        }



def analyze_test_dependencies():
    """Analyze test files to determine safe parallel execution groups."""
    test_files = list(Path(__file__).parent.glob("test_*.py"))
    
    # Sort by filename to maintain execution order
    test_files = sorted(test_files)
    
    # Define dependency groups based on test naming conventions and markers
    dependency_groups = {
        'infrastructure': [],  # Must run first, sequentially
        'core': [],           # Core tests, can run in parallel after infrastructure
        'integration': [],    # Integration tests, can run in parallel
        'independent': []     # Independent tests, safe for parallel
    }
    
    for test_file in test_files:
        test_name = test_file.name
        
        # Infrastructure setup tests (00_ prefix) must run first
        if test_name.startswith('test_00_'):
            dependency_groups['infrastructure'].append(test_file)
        # Core tests with specific ordering requirements (01-09 prefix)
        elif test_name.startswith('test_01_') or test_name.startswith('test_02_') or \
             test_name.startswith('test_03_') or test_name.startswith('test_04_') or \
             test_name.startswith('test_05_') or test_name.startswith('test_06_') or \
             test_name.startswith('test_07_') or test_name.startswith('test_08_') or \
             test_name.startswith('test_09_'):
            dependency_groups['core'].append(test_file)
        # Integration tests (explicit naming or markers)
        elif 'integration' in test_name.lower() or 'e2e' in test_name.lower():
            dependency_groups['integration'].append(test_file)
        # Upload/network tests should run in integration group (potential shared resources)
        elif 'upload' in test_name.lower() or 'network' in test_name.lower() or 'api' in test_name.lower():
            dependency_groups['integration'].append(test_file)
        # All other tests are considered independent
        else:
            dependency_groups['independent'].append(test_file)
    
    return dependency_groups

def run_test_group_parallel(test_files: List[Path], max_workers: int = 2, profile_args: List[str] = None) -> Tuple[int, float, Dict[str, any]]:
    """Run a group of tests in parallel using pytest-xdist if available."""
    if not test_files:
        return 0, 0.0, {'parallel_used': False, 'workers': 0, 'method': 'none'}
    
    start_time = time.time()
    execution_info = {'parallel_used': False, 'workers': 0, 'method': 'sequential_fallback'}
    
    # Check if pytest-xdist is available
    try:
        import xdist
        has_xdist = True
    except ImportError:
        has_xdist = False
        print("   📝 Note: pytest-xdist not available - install with 'pip install pytest-xdist' for parallel execution")
    
    if has_xdist and len(test_files) > 1:
        # Use pytest-xdist for parallel execution
        optimal_workers = min(max_workers, len(test_files))
        execution_info.update({
            'parallel_used': True, 
            'workers': optimal_workers, 
            'method': 'pytest-xdist'
        })
        
        if profile_args:
            print(f"   ⚠️  Warning: Profiling with parallel execution may have limited functionality")
        
        print(f"   ⚡ Running {len(test_files)} tests with {optimal_workers} parallel workers")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            '-n', str(optimal_workers),
            '--tb=short', '-v',
            '--dist', 'loadfile'  # Distribute by test file for better load balancing
        ]
        
        # Add profiling args if provided
        if profile_args:
            cmd.extend(profile_args)
        
        cmd.extend([str(f) for f in test_files])
    else:
        # Fallback to sequential execution
        if len(test_files) == 1:
            execution_info['method'] = 'single_test'
            print(f"   🔄 Running single test file: {test_files[0].name}")
        else:
            print(f"   🔄 Running {len(test_files)} tests sequentially (parallel not available)")
            
        cmd = [
            sys.executable, '-m', 'pytest',
            '--tb=short', '-v'
        ]
        
        # Add profiling args if provided
        if profile_args:
            cmd.extend(profile_args)
        
        cmd.extend([str(f) for f in test_files])
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
        execution_time = time.time() - start_time
        return result.returncode, execution_time, execution_info
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"   ❌ Test execution failed: {e}")
        return 1, execution_time, execution_info

def run_test_group_sequential(test_files: List[Path], profile_args: List[str] = None) -> Tuple[int, float, Dict[str, any]]:
    """Run a group of tests sequentially."""
    if not test_files:
        return 0, 0.0, {'method': 'none', 'test_count': 0}
    
    start_time = time.time()
    execution_info = {'method': 'sequential', 'test_count': len(test_files)}
    
    print(f"   🔄 Running {len(test_files)} tests sequentially")
    
    cmd = [
        sys.executable, '-m', 'pytest',
        '--tb=short', '-v'
    ]
    
    # Add profiling args if provided
    if profile_args:
        cmd.extend(profile_args)
    
    cmd.extend([str(f) for f in test_files])
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Run tests
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
        execution_time = time.time() - start_time
        return result.returncode, execution_time, execution_info
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"   ❌ Test execution failed: {e}")
        return 1, execution_time, execution_info

def analyze_optimization_opportunities(metrics: PerformanceMetrics):
    """Analyze what optimizations can be applied to the current test run."""
    print("🔍 Analyzing optimization opportunities...")
    
    detector = ChangeDetector()
    optimization = detector.get_build_optimization()
    
    print(f"   APK cache available: {'✅' if optimization.apk_exists else '❌'}")
    print(f"   Source code unchanged: {'✅' if optimization.source_unchanged else '❌'}")
    print(f"   Test data unchanged: {'✅' if optimization.data_unchanged else '❌'}")
    
    if optimization.can_skip_build:
        print("   🚀 Can skip APK build (using cached)")
        metrics.add_optimization("APK build cache hit")
        metrics.set_cache_hit("apk_build", True)
    else:
        print("   🔨 APK build required")
        metrics.set_cache_hit("apk_build", False)
        
    if optimization.can_skip_data:
        print("   🚀 Can skip data processing (using cached)")
        metrics.add_optimization("Data processing cache hit")
        metrics.set_cache_hit("data_processing", True)
    else:
        print("   📊 Data processing required")
        metrics.set_cache_hit("data_processing", False)
    
    return optimization

def parse_arguments():
    """Parse command line arguments with optimization support"""
    parser = argparse.ArgumentParser(
        description="Optimized test runner for Running Heatmap mobile app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                     # Run all tests with automatic optimization
  python run_tests.py --fast              # Run tests in fast mode (use cached artifacts)
  python run_tests.py --force-build       # Force APK build even if source unchanged
  python run_tests.py --force-data        # Force data processing even if data unchanged
  python run_tests.py --one-test          # Interactive single test selection
  python run_tests.py --no-optimize       # Disable all optimizations
  python run_tests.py --update-baseline   # Update change detection baseline after run
  python run_tests.py --performance-report # Generate detailed performance metrics
  python run_tests.py --parallel          # Enable parallel test execution where safe
  python run_tests.py --parallel-workers 2 # Set maximum parallel workers (default: 2)
  python run_tests.py --skip-cleanup      # Skip cleanup for faster repeated runs
  python run_tests.py --profile           # Enable performance profiling (generates flame graphs)
  python run_tests.py --one-test --profile # Profile a specific test for detailed analysis
        """
    )
    
    # Main flags
    parser.add_argument('--fast', action='store_true',
                       help='Use cached artifacts when available (skip builds if source unchanged)')
    parser.add_argument('--one-test', action='store_true',
                       help='Interactive selection of a single test to run')
    
    # Optimization control flags
    parser.add_argument('--force-build', action='store_true',
                       help='Force APK build even if source code unchanged')
    parser.add_argument('--force-data', action='store_true',
                       help='Force data processing even if test data unchanged')
    parser.add_argument('--no-optimize', action='store_true',
                       help='Disable all optimizations (traditional build behavior)')
    parser.add_argument('--update-baseline', action='store_true',
                       help='Update change detection baseline after successful test run')
    parser.add_argument('--performance-report', action='store_true',
                       help='Generate detailed performance metrics report')
    parser.add_argument('--parallel', action='store_true',
                       help='Enable parallel test execution where safe')
    parser.add_argument('--parallel-workers', type=int, default=2, choices=range(1, 5),
                       help='Maximum number of parallel workers (default: 2, range: 1-4, max recommended: 2 for mobile tests)')
    parser.add_argument('--skip-cleanup', action='store_true',
                       help='Skip cleanup for faster repeated runs (use with caution)')
    parser.add_argument('--profile', action='store_true',
                       help='Enable performance profiling for tests (generates flame graphs)')
    
    # Report file (internal use)
    parser.add_argument('--report-file', default='reports/test_report.html',
                       help=argparse.SUPPRESS)  # Hidden from help
    
    return parser.parse_args()

def check_prerequisites(args, optimization=None):
    """Check prerequisites for test execution with optimization awareness"""
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
    
    # Check APK requirements based on optimization analysis
    if optimization and optimization.can_skip_build and not args.force_build and not args.no_optimize:
        # Can use cached APK
        cached_apk_path = Path(__file__).parent / "cached_test_apk" / "app-debug.apk"
        if cached_apk_path.exists():
            print(f"✅ Using cached APK: {cached_apk_path}")
        else:
            print("❌ Cached APK not found, will need to build")
            return False
    else:
        # Need project structure for building or forced build
        project_root = Path(__file__).parent.parent
        server_dir = project_root / "server"
        if not server_dir.exists():
            print("❌ Server directory not found. Are you in the right project?")
            return False
        print("✅ Project structure verified for APK building")
    
    # Check for existing test data
    if optimization and optimization.can_skip_data and not args.force_data and not args.no_optimize:
        cached_data_path = Path(__file__).parent / "cached_test_data" / "runs.pmtiles"
        if cached_data_path.exists():
            print(f"✅ Using cached test data: {cached_data_path}")
        else:
            print("❌ Cached test data not found, will need to process")
    else:
        print("✅ Test data processing will be performed")
    
    return True



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

def prepare_optimized_environment(args, optimization):
    """Prepare test environment with optimization features"""
    print("🚀 Preparing optimized test environment...")
    
    # Create cache directories if they don't exist
    cache_apk_dir = Path(__file__).parent / "cached_test_apk"
    cache_data_dir = Path(__file__).parent / "cached_test_data"
    cache_apk_dir.mkdir(exist_ok=True)
    cache_data_dir.mkdir(exist_ok=True)
    
    # Set environment variables for pytest fixtures to use optimization
    env_vars = {
        'OPTIMIZATION_ENABLED': '1' if not args.no_optimize else '0',
        'SKIP_APK_BUILD': '1' if (optimization.can_skip_build and not args.force_build and not args.no_optimize) else '0',
        'SKIP_DATA_PROCESSING': '1' if (optimization.can_skip_data and not args.force_data and not args.no_optimize) else '0',
        'CACHED_APK_PATH': str(cache_apk_dir / "app-debug.apk"),
        'CACHED_DATA_PATH': str(cache_data_dir / "runs.pmtiles"),
        'FORCE_BUILD': '1' if args.force_build else '0',
        'FORCE_DATA': '1' if args.force_data else '0',
        'PERFORMANCE_REPORT': '1' if args.performance_report else '0',
        'PARALLEL_EXECUTION': '1' if args.parallel else '0',
        'SKIP_CLEANUP': '1' if args.skip_cleanup else '0'
    }
    
    print("   Environment configuration:")
    for key, value in env_vars.items():
        print(f"     {key}={value}")
        os.environ[key] = value
    
    return env_vars

def build_pytest_command(args):
    """Build pytest command based on arguments with optimization support"""
    cmd = [sys.executable, '-m', 'pytest']
    
    # Test selection
    if args.one_test and hasattr(args, 'selected_tests') and args.selected_tests:
        cmd.extend(args.selected_tests)
    else:
        # Run all tests by default
        cmd.append('.')
    
    # Add fast mode flag if specified (backwards compatibility)
    if args.fast:
        cmd.append('--fast')
    
    # Add profiling flags if enabled
    if args.profile:
        # pytest-profiling uses fixed 'prof/' directory - we'll move files later
        cmd.extend(['--profile', '--profile-svg'])
    
    # Standard options - pytest.ini now includes -rw for warnings
    cmd.extend(['-v', '--tb=short'])
    
    # HTML reporting with warnings included  
    cmd.extend(['--html', args.report_file, '--self-contained-html'])
    
    return cmd

def run_tests(args, optimization=None, metrics: PerformanceMetrics = None):
    """Run the tests with optimization orchestration"""
    test_start_time = time.time()
    
    # Determine test mode description
    if args.no_optimize:
        mode = "traditional mode (no optimization)"
    elif args.fast:
        mode = "fast mode (using cached artifacts)"
    elif optimization and (optimization.can_skip_build or optimization.can_skip_data):
        mode = "optimized mode (automatic caching)"
    else:
        mode = "full mode (building all artifacts)"
    
    test_type = "selected test" if args.one_test else "all tests"
    parallel_mode = " with parallel execution" if args.parallel else ""
    print(f"🧪 Running {test_type} in {mode}{parallel_mode}...")
    
    # Set up environment for testing
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Add optimization environment variables if optimization is available
    if optimization:
        prepare_optimized_environment(args, optimization)
    
    # Handle parallel execution
    if args.parallel and not args.one_test:
        return run_tests_parallel(args, metrics)
    else:
        # Traditional sequential execution
        return run_tests_sequential(args, metrics, test_start_time)

def run_tests_sequential(args, metrics: PerformanceMetrics = None, start_time: float = None):
    """Run tests sequentially (traditional mode)"""
    if start_time is None:
        start_time = time.time()
    
    # Build pytest command
    cmd = build_pytest_command(args)
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).parent)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent, env=env)
    
    if metrics:
        metrics.test_execution_time = time.time() - start_time
    
    return result.returncode

def run_tests_parallel(args, metrics: PerformanceMetrics = None):
    """Run tests with safe parallel execution"""
    parallel_start_time = time.time()
    overall_exit_code = 0
    
    # Extract profiling arguments if enabled
    profile_args = None
    if args.profile:
        # pytest-profiling uses fixed 'prof/' directory - we'll move files later
        profile_args = ['--profile', '--profile-svg']
    
    print("🔍 Analyzing test dependencies for safe parallel execution...")
    
    # Analyze test dependencies
    dependency_groups = analyze_test_dependencies()
    
    # Print execution plan
    print("📋 Parallel execution plan:")
    total_tests = 0
    for group_name, test_files in dependency_groups.items():
        if test_files:
            count = len(test_files)
            total_tests += count
            execution_type = "sequential" if group_name == 'infrastructure' else "parallel"
            print(f"   {group_name.title()}: {count} test(s) - {execution_type}")
            for test_file in test_files:
                print(f"     • {test_file.name}")
    
    print(f"   Total: {total_tests} tests")
    
    try:
        # Step 1: Run infrastructure tests sequentially (must run first)
        if dependency_groups['infrastructure']:
            print(f"\n🏗️ Running infrastructure tests sequentially...")
            exit_code, exec_time, exec_info = run_test_group_sequential(dependency_groups['infrastructure'], profile_args)
            
            if metrics:
                metrics.record_test_group_execution('infrastructure', exec_time, exec_info)
            
            if exit_code != 0:
                print("❌ Infrastructure tests failed - cannot continue with parallel execution")
                overall_exit_code = exit_code
                return overall_exit_code
            
            print(f"✅ Infrastructure tests completed in {exec_time:.1f}s")
        
        # Step 2: Run remaining test groups - try parallel first, fallback if needed
        parallel_groups = ['core', 'integration', 'independent']
        
        for group_name in parallel_groups:
            group_tests = dependency_groups[group_name]
            if not group_tests:
                continue
                
            print(f"\n⚡ Processing {group_name} group ({len(group_tests)} tests)...")
            
            # Determine optimal worker count (respecting user setting and emulator constraints)
            max_workers = min(args.parallel_workers, len(group_tests), 2)  # Cap at 2 for mobile stability
            
            # Try parallel execution first
            exit_code, exec_time, exec_info = run_test_group_parallel(group_tests, max_workers, profile_args)
            
            if exit_code != 0 and exec_info.get('parallel_used', False):
                print(f"⚠️ Parallel execution failed for {group_name} group, trying sequential fallback...")
                
                # Fallback to sequential execution
                exit_code_sequential, fallback_exec_time, fallback_info = run_test_group_sequential(group_tests, profile_args)
                
                if metrics:
                    metrics.record_test_group_execution(f'{group_name}_fallback', fallback_exec_time, fallback_info)
                    metrics.sequential_fallback_time += fallback_exec_time
                    metrics.add_optimization(f"Sequential fallback for {group_name} group after parallel failure")
                
                if exit_code_sequential == 0:
                    print(f"✅ Sequential fallback for {group_name} completed successfully in {fallback_exec_time:.1f}s")
                    exit_code = 0  # Override with successful sequential result
                else:
                    print(f"❌ Sequential fallback for {group_name} also failed")
                    overall_exit_code = exit_code_sequential
                    break  # Stop processing remaining groups
            
            # Record metrics for successful execution
            if metrics and exit_code == 0:
                metrics.record_test_group_execution(group_name, exec_time, exec_info)
                if exec_info.get('parallel_used', False):
                    metrics.parallel_execution_time += exec_time
                    metrics.parallel_workers_used = max(metrics.parallel_workers_used, exec_info.get('workers', 0))
                    metrics.add_optimization(f"Parallel execution for {group_name} group with {exec_info.get('workers', 0)} workers")
            
            if exit_code != 0:
                overall_exit_code = exit_code
                break
            else:
                print(f"✅ {group_name.title()} tests completed successfully in {exec_time:.1f}s")
        
        # Calculate total execution time and performance insights
        total_parallel_time = time.time() - parallel_start_time
        
        if metrics:
            metrics.test_execution_time = total_parallel_time
            
            # Calculate efficiency metrics
            efficiency_metrics = metrics.calculate_parallel_efficiency()
            if efficiency_metrics:
                parallel_portion = efficiency_metrics['parallel_portion']
                if parallel_portion > 0.5:  # More than 50% parallel
                    estimated_sequential_time = efficiency_metrics['total_parallel_time'] + efficiency_metrics['total_sequential_time']
                    if estimated_sequential_time > total_parallel_time:
                        speedup = estimated_sequential_time / total_parallel_time
                        if speedup > 1.1:  # Only report significant speedup
                            print(f"🚀 Parallel execution achieved estimated {speedup:.1f}x speedup")
                            metrics.add_optimization(f"Parallel speedup: {speedup:.1f}x")
    
    except Exception as e:
        print(f"❌ Parallel execution failed with exception: {e}")
        print("🔄 Falling back to full sequential execution...")
        
        # Complete fallback to sequential mode
        sequential_start_time = time.time()
        overall_exit_code = run_tests_sequential(args, metrics, sequential_start_time)
        
        if metrics:
            metrics.sequential_fallback_time = time.time() - sequential_start_time
            metrics.add_optimization("Full sequential fallback due to parallel execution exception")
    
    return overall_exit_code

def update_baseline_after_successful_run(args):
    """Update change detection baseline after successful test run"""
    if args.update_baseline:
        print("📝 Updating change detection baseline...")
        try:
            detector = ChangeDetector()
            detector.update_baseline()
        except Exception as e:
            print(f"⚠️  Warning: Could not update baseline: {e}")
    elif not args.no_optimize:
        # Auto-update baseline after successful optimized runs
        print("📝 Auto-updating change detection baseline...")
        try:
            detector = ChangeDetector()
            detector.update_baseline()
        except Exception as e:
            print(f"⚠️  Warning: Could not auto-update baseline: {e}")



def move_profiling_files_to_reports(profiling_enabled: bool, report_dir: Path):
    """Move pytest-profiling generated files to reports directory."""
    if not profiling_enabled:
        return
    
    prof_dir = Path(__file__).parent / "prof"
    target_profiles_dir = report_dir / "profiles"
    
    if not prof_dir.exists():
        return
    
    # Create target directory
    target_profiles_dir.mkdir(exist_ok=True, parents=True)
    
    # Move/copy prof files to target directory
    moved_files = []
    for prof_file in prof_dir.glob("*"):
        if prof_file.is_file():
            target_file = target_profiles_dir / prof_file.name
            try:
                import shutil
                shutil.copy2(prof_file, target_file)
                moved_files.append(target_file.name)
            except Exception as e:
                print(f"⚠️  Warning: Could not copy {prof_file.name}: {e}")
    
    if moved_files:
        print(f"📊 Profiling files copied to {target_profiles_dir}: {', '.join(moved_files)}")
    
    return target_profiles_dir

def generate_performance_report(metrics: PerformanceMetrics, report_dir: Path, profiling_enabled: bool = False):
    """Generate performance metrics report."""
    try:
        performance_report_path = report_dir / "performance_metrics.json"
        
        with open(performance_report_path, 'w') as f:
            import json
            summary = metrics.get_summary()
            summary['generated_at'] = datetime.now().isoformat()
            json.dump(summary, f, indent=2)
        
        print(f"📈 Performance metrics saved: {performance_report_path}")
        
        # Print summary to console
        print("\n📊 Performance Summary:")
        print("=" * 50)
        print(f"   Total execution time: {metrics.total_time:.1f}s")
        
        if metrics.emulator_startup_time > 0:
            print(f"   Emulator startup: {metrics.emulator_startup_time:.1f}s")
        
        if metrics.appium_startup_time > 0:
            print(f"   Appium startup: {metrics.appium_startup_time:.1f}s")
        
        if metrics.build_time > 0:
            print(f"   Build time: {metrics.build_time:.1f}s")
        
        if metrics.data_processing_time > 0:
            print(f"   Data processing: {metrics.data_processing_time:.1f}s")
        
        if metrics.test_execution_time > 0:
            print(f"   Test execution: {metrics.test_execution_time:.1f}s")
        
        # Detailed parallel execution reporting
        if metrics.test_group_timings:
            print(f"   Test group execution details:")
            total_parallel_time = 0
            total_sequential_time = 0
            for group_name, timing in metrics.test_group_timings.items():
                method = timing['execution_method']
                exec_time = timing['execution_time']
                test_count = timing.get('test_count', 0)
                workers = timing.get('workers', 0)
                
                if timing.get('parallel_used', False):
                    total_parallel_time += exec_time
                    print(f"     {group_name}: {exec_time:.1f}s ({test_count} tests, {workers} workers) ⚡")
                else:
                    total_sequential_time += exec_time
                    if method == 'sequential':
                        print(f"     {group_name}: {exec_time:.1f}s ({test_count} tests) 🔄")
                    else:
                        print(f"     {group_name}: {exec_time:.1f}s ({method})")
            
            if total_parallel_time > 0 and total_sequential_time > 0:
                total_test_time = total_parallel_time + total_sequential_time
                parallel_percentage = (total_parallel_time / total_test_time) * 100
                print(f"     Execution breakdown: {parallel_percentage:.1f}% parallel, {100-parallel_percentage:.1f}% sequential")
        
        if metrics.parallel_execution_time > 0:
            print(f"   Total parallel execution: {metrics.parallel_execution_time:.1f}s")
            print(f"   Max workers used: {metrics.parallel_workers_used}")
        
        if metrics.sequential_fallback_time > 0:
            print(f"   Sequential fallback time: {metrics.sequential_fallback_time:.1f}s")
        
        if metrics.parallel_execution_details:
            details = metrics.parallel_execution_details
            print(f"   Parallel efficiency:")
            print(f"     Parallel portion: {details['parallel_portion']*100:.1f}%")
            print(f"     Sequential portion: {details['sequential_portion']*100:.1f}%")
        
        if metrics.cache_hits:
            print(f"   Cache performance:")
            for cache_type, hit in metrics.cache_hits.items():
                status = "HIT" if hit else "MISS"
                emoji = "🎯" if hit else "🔄"
                print(f"     {cache_type}: {emoji} {status}")
        
        if profiling_enabled:
            # Check for flame graphs in both original prof/ directory and moved profiles directory
            prof_dir = Path(__file__).parent / "prof"
            profile_dir = report_dir / "profiles"
            
            svg_files_found = []
            
            # Check original prof directory
            if prof_dir.exists():
                svg_files_found.extend(list(prof_dir.glob("*.svg")))
            
            # Check moved profiles directory  
            if profile_dir.exists():
                svg_files_found.extend(list(profile_dir.glob("*.svg")))
            
            if svg_files_found:
                print(f"   🔥 Flame graphs generated: {len(svg_files_found)} files")
                if profile_dir.exists():
                    print(f"     Location: {profile_dir}")
                elif prof_dir.exists():
                    print(f"     Location: {prof_dir}")
                print(f"     💡 Open .svg files in browser to view flame graphs")
                
                # List the actual files found
                for svg_file in svg_files_found:
                    print(f"       • {svg_file.name}")
            else:
                print(f"   🔥 Profiling enabled but no flame graphs found")
        
        if metrics.optimizations_applied:
            print(f"   Optimizations applied: {len(metrics.optimizations_applied)}")
            for opt in metrics.optimizations_applied:
                print(f"     ⚡ {opt}")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"⚠️  Warning: Could not generate performance report: {e}")


def open_test_report(report_path, metrics: PerformanceMetrics = None, profiling_enabled: bool = False):
    """Report test report location without auto-opening"""
    abs_report_path = Path(__file__).parent / report_path
    
    if not abs_report_path.exists():
        print(f"📊 Test report was not generated: {report_path}")
        return
    
    print(f"📊 Test report saved: {abs_report_path}")
    
    # Move profiling files to reports directory if profiling was enabled
    if profiling_enabled:
        move_profiling_files_to_reports(profiling_enabled, abs_report_path.parent)
    
    # Generate performance report if metrics available
    if metrics:
        generate_performance_report(metrics, abs_report_path.parent, profiling_enabled)
    
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
    """Main test runner function with optimization orchestration"""
    # Initialize performance metrics
    metrics = PerformanceMetrics()
    
    # Parse arguments
    args = parse_arguments()
    
    print("📱 Running Heatmap Mobile App Test Runner (Optimized)")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Analyze optimization opportunities
    optimization = None
    if not args.no_optimize:
        try:
            optimization = analyze_optimization_opportunities(metrics)
        except Exception as e:
            print(f"⚠️  Warning: Optimization analysis failed: {e}")
            print("   Continuing with traditional mode...")
    
    # Handle test selection if one-test mode
    if args.one_test:
        selected_tests = discover_and_select_test()
        if selected_tests is None:
            print("❌ No test selected, exiting...")
            sys.exit(1)
        args.selected_tests = selected_tests
    
    # Check prerequisites with optimization awareness
    if not check_prerequisites(args, optimization):
        sys.exit(1)
    
    # Check for persistent infrastructure first (simple check)
    use_persistent = check_for_persistent_infrastructure()
    
    emulator_info = None
    appium_process = None
    
    if use_persistent:
        print("⚡ Using existing persistent infrastructure")
        # Update metrics with cached startup times
        metrics.emulator_startup_time = 0.0  # Already running
        metrics.appium_startup_time = 0.0    # Already running
        metrics.add_optimization("Used persistent emulator")
        metrics.add_optimization("Used persistent Appium server")
        # Set traditional emulator_info for compatibility
        emulator_info = {'started_emulator': False}  # Didn't start it ourselves
    else:
        print("🔧 Setting up traditional isolated infrastructure")
        # Check for devices using traditional method
        emulator_info = check_and_start_emulator(metrics)
        if not emulator_info:
            sys.exit(1)
        
        # Start Appium server using traditional method
        appium_process = start_appium_server(metrics)
        if appium_process is None:
            print("❌ Failed to start Appium server")
            sys.exit(1)
    
    # Create reports directory
    reports_dir = Path(__file__).parent / Path(args.report_file).parent
    reports_dir.mkdir(exist_ok=True)
    
    exit_code = 1
    
    try:
        
        # Run tests with optimization
        exit_code = run_tests(args, optimization, metrics)
        
        # Print result
        if exit_code == 0:
            print("\n✅ All tests passed!")
            # Update baseline after successful run
            update_baseline_after_successful_run(args)
        else:
            print("\n❌ Some tests failed")
        
        # Finalize performance metrics
        metrics.finalize()
        
        # Open test report with performance metrics
        open_test_report(args.report_file, metrics, args.profile)
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit_code = 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit_code = 1
        
    finally:
        # Cleanup (unless skip-cleanup is specified or using persistent infrastructure)
        if not args.skip_cleanup and not use_persistent:
            cleanup_appium_server(appium_process)
            shutdown_emulator(emulator_info)
        elif use_persistent:
            print("⏩ Using persistent infrastructure - no cleanup needed")
            print("   Use './persist_tests.sh stop' to clean up persistent services")
        else:
            print("⏩ Skipping cleanup per --skip-cleanup flag")
            print("   Emulator and Appium server remain running for faster subsequent runs")
            print("   💡 Consider using persistent infrastructure: './persist_tests.sh start'")
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()