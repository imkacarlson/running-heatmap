#!/usr/bin/env python3
"""
Direct-import version of run_tests.py for profiling
Calls pytest directly instead of subprocess to enable profiling
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run pytest directly
import pytest

import argparse

def main():
    """Run tests directly via pytest import instead of subprocess"""
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cov",
        action="store_true",
        help="Collect coverage for server/ (Python)."
    )
    args, remaining_argv = parser.parse_known_args()

    # Set up environment for tests
    os.environ['PYTHONPATH'] = str(Path(__file__).parent)
    os.environ['OPTIMIZATION_ENABLED'] = '1'
    os.environ['SKIP_APK_BUILD'] = '1'
    os.environ['SKIP_DATA_PROCESSING'] = '1'
    if args.cov:
        os.environ['COVERAGE_RUN'] = '1'
        # Enable automatic coverage for all Python subprocesses
        os.environ['COVERAGE_PROCESS_START'] = str(Path(__file__).parent.parent / '.coveragerc')
    
    # Configure pytest arguments
    pytest_args = [
        '--tb=short', 
        '-v',
        'test_00_infrastructure_setup.py',
        'test_01_activity_visibility.py', 
        'test_basic_lasso_selection.py',
        'test_extras_last_activity_filter.py',
        'test_upload_functionality.py'
    ]
    
    if args.cov:
        from pathlib import Path
        repo_root = Path(__file__).parent.parent
        pytest_args += [
            "--cov=server",
            "--cov-branch",
            f"--cov-config={repo_root / '.coveragerc'}",
            "--cov-report=term-missing:skip-covered",
            "--cov-report=html:testing/reports/coverage/python/html",
            "--cov-report=xml",
        ]

    # Run pytest directly
    exit_code = pytest.main(pytest_args + remaining_argv)
    
    # Combine coverage data from all processes if coverage was enabled
    if args.cov:
        combine_coverage_data()
    
    return exit_code

def combine_coverage_data():
    """Combine coverage data from all processes and generate reports"""
    import sys
    import subprocess
    from pathlib import Path
    
    try:
        repo_root = Path(__file__).parent.parent
        print("\n📊 Combining Python coverage data from all processes...")
        
        # Combine all .coverage.* files
        subprocess.run([
            sys.executable, '-m', 'coverage', 'combine',
            '--rcfile', str(repo_root / '.coveragerc')
        ], cwd=repo_root, check=False)
        
        # Generate HTML report
        subprocess.run([
            sys.executable, '-m', 'coverage', 'html',
            '--rcfile', str(repo_root / '.coveragerc'),
            '-d', 'testing/reports/coverage/python/html'
        ], cwd=repo_root, check=False)
        
        # Generate XML report  
        subprocess.run([
            sys.executable, '-m', 'coverage', 'xml',
            '--rcfile', str(repo_root / '.coveragerc'),
            '-o', 'testing/reports/coverage/python/cobertura.xml'
        ], cwd=repo_root, check=False)
        
        print("✅ Python coverage combined and reports generated")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not combine coverage data: {e}")

if __name__ == '__main__':
    exit(main())