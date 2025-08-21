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

def main():
    """Run tests directly via pytest import instead of subprocess"""
    
    # Set up environment for tests
    os.environ['PYTHONPATH'] = str(Path(__file__).parent)
    os.environ['OPTIMIZATION_ENABLED'] = '1'
    os.environ['SKIP_APK_BUILD'] = '1'
    os.environ['SKIP_DATA_PROCESSING'] = '1'
    
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
    
    # Run pytest directly
    exit_code = pytest.main(pytest_args)
    return exit_code

if __name__ == '__main__':
    exit(main())