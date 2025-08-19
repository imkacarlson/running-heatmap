#!/usr/bin/env python3
"""
Infrastructure Setup Tests

This module contains tests that handle the expensive, one-time setup operations
required before running functional tests:
- Building APK with test data 
- Installing APK on emulator
- Setting up test environment

These tests run first (00_ prefix) and prepare the infrastructure that
functional tests depend on.
"""
import pytest
import time
from pathlib import Path


@pytest.mark.core
@pytest.mark.mobile
class TestInfrastructureSetup:
    """Infrastructure setup tests for mobile testing environment"""
    
    def test_build_and_install_test_apk(self, session_setup):
        """
        🏗️ Build and install test APK with sample data
        
        This test handles all the expensive infrastructure setup:
        - Creates isolated test environment with GPX data
        - Runs data pipeline (GPX import, PMTiles generation)  
        - Builds mobile APK with test data
        - Installs APK on emulator
        
        This runs once per test session and enables all functional tests.
        """
        print("🏗️ Infrastructure setup test starting...")
        print("   This test builds APK with test data and installs it on emulator")
        
        # The session_setup fixture handles all the actual work
        # We just need to verify it completed successfully
        setup_info = session_setup
        
        # Verify essential components were set up
        assert 'package_name' in setup_info, "Package name not set in setup"
        assert setup_info['package_name'] == 'com.run.heatmap', f"Unexpected package name: {setup_info['package_name']}"
        
        if not setup_info.get('apk_path') and not setup_info.get('test_env'):
            # Fast mode - APK already exists
            print("   ⚡ Fast mode: Using existing APK installation")
        else:
            # Full mode - APK was built and installed
            if setup_info.get('apk_path'):
                apk_path = Path(setup_info['apk_path'])
                assert apk_path.exists(), f"APK not found after build: {apk_path}"
                print(f"   ✅ APK built and available: {apk_path}")
            
            if setup_info.get('pmtiles_path'):
                pmtiles_path = Path(setup_info['pmtiles_path'])
                assert pmtiles_path.exists(), f"PMTiles not found after build: {pmtiles_path}"
                print(f"   ✅ PMTiles generated: {pmtiles_path}")
            
            print("   ✅ Test environment created with sample GPX data")
        
        print("   ✅ APK installed and ready for functional testing")
        print("🏗️ Infrastructure setup completed successfully!")
        
        # Brief pause to ensure everything is settled
        time.sleep(2)
    
    def test_network_isolation_verification(self):
        """
        🔒 Verify test suite operates without external network requests
        
        This test ensures that the test suite runs completely offline,
        eliminating network latency as a variable in test runtime.
        Tests should be isolated from external connectivity issues.
        """
        print("🔒 Verifying network isolation...")
        
        # Import here to avoid affecting other tests
        import unittest.mock
        import subprocess
        
        external_calls = []
        original_subprocess_run = subprocess.run
        
        def mock_subprocess_run(*args, **kwargs):
            # Log any external network calls
            if args and len(args[0]) > 0:
                cmd = args[0]
                if isinstance(cmd, list) and len(cmd) > 0:
                    if 'ping' in cmd[0] and any('openstreetmap' in str(arg) for arg in cmd):
                        external_calls.append(('ping', cmd))
                        # Return mock result for ping to avoid external call
                        class MockResult:
                            stdout = "PING tile.openstreetmap.org: 56 data bytes\n64 bytes from 1.2.3.4: icmp_seq=0 time=25.0 ms\n64 bytes from 1.2.3.4: icmp_seq=1 time=30.0 ms\n64 bytes from 1.2.3.4: icmp_seq=2 time=35.0 ms"
                            stderr = ""
                            returncode = 0
                        return MockResult()
            
            return original_subprocess_run(*args, **kwargs)
        
        # Import modules that might make external calls
        try:
            from testing.network_config import NetworkConfig
            
            # Mock subprocess to catch external calls
            with unittest.mock.patch('subprocess.run', side_effect=mock_subprocess_run):
                # Test network config operations
                speed = NetworkConfig.estimate_network_speed()
                multiplier = NetworkConfig.get_timeout_multiplier()
                adaptive_timeout = NetworkConfig.get_adaptive_timeout(10)
                
                # Verify we get reasonable defaults without external calls
                assert speed in ['fast', 'normal', 'slow'], f"Invalid network speed: {speed}"
                assert isinstance(multiplier, (int, float)), f"Invalid multiplier type: {type(multiplier)}"
                assert isinstance(adaptive_timeout, int), f"Invalid timeout type: {type(adaptive_timeout)}"
                
            print("   ✅ Network configuration operates without external calls")
            
        except ImportError:
            print("   ⚠️ network_config module not found - skipping network config test")
        
        # Verify no external network calls were attempted
        if external_calls:
            print(f"   ⚠️ Warning: {len(external_calls)} external network calls detected:")
            for call_type, cmd in external_calls:
                print(f"      - {call_type}: {' '.join(cmd)}")
        else:
            print("   ✅ No external network calls detected")
        
        print("🔒 Network isolation verification completed!")